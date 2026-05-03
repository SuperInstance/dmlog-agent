#!/usr/bin/env python3
"""
dmlog-agent — AI dungeon master tools for D&D and tabletop RPG campaigns
Track NPCs, factions, locations, sessions, and encounters.
Integrates with the PLATO fleet for campaign intelligence.

Now uses domain-agent-base for PLATO integration, health checks, and reporting.
"""

import json, time, random
from typing import List, Dict, Optional
from dataclasses import dataclass, field

try:
    from domain_agent_base import DomainAgent
except ImportError:
    class DomainAgent:
        domain = "base"
        plato_url = "http://147.224.38.131:8847"
        def __init__(self):
            self.tiles_submitted = []
            self.errors = []
            self.start_time = time.time()
        def submit_tile(self, question, answer, room=None):
            self.tiles_submitted.append({"q": question, "a": answer})
            return True
        def get_stats(self):
            return {"domain": self.domain, "tiles": len(self.tiles_submitted)}
        def run(self):
            raise NotImplementedError

@dataclass
class NPC:
    name: str
    race: str
    role: str
    faction: Optional[str] = None
    hp: int = 10
    ac: int = 10
    notes: str = ""
    last_seen: Optional[float] = None
    status: str = "alive"

@dataclass
class Faction:
    name: str
    alignment: str
    influence: int = 0
    members: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    relations: Dict[str, int] = field(default_factory=dict)

@dataclass
class Location:
    name: str
    region: str
    description: str
    discovered_by: List[str] = field(default_factory=list)
    connected_to: List[str] = field(default_factory=list)
    danger_level: int = 1

@dataclass
class Encounter:
    id: str
    location: str
    participants: List[str]
    outcome: str
    timestamp: float
    loot: List[str] = field(default_factory=list)
    xp_awarded: int = 0

@dataclass
class Session:
    id: str
    date: str
    summary: str
    encounters: List[Encounter] = field(default_factory=list)
    major_events: List[str] = field(default_factory=list)
    npcs_introduced: List[str] = field(default_factory=list)

class DMLogAgent(DomainAgent):
    """Dungeon master agent — now with DomainAgent base class."""
    
    domain = "dmlog"
    version = "0.2.0"
    
    def __init__(self, campaign: str = "default-campaign"):
        super().__init__()
        self.campaign = campaign
        self.npcs: Dict[str, NPC] = {}
        self.factions: Dict[str, Faction] = {}
        self.locations: Dict[str, Location] = {}
        self.encounters: List[Encounter] = []
        self.sessions: List[Session] = []
    
    def add_npc(self, name: str, race: str, role: str, faction: Optional[str] = None,
                hp: int = 10, ac: int = 10, notes: str = ""):
        """Add an NPC to the campaign."""
        npc = NPC(name=name, race=race, role=role, faction=faction, hp=hp, ac=ac, notes=notes)
        self.npcs[name] = npc
        if faction and faction in self.factions:
            if name not in self.factions[faction].members:
                self.factions[faction].members.append(name)
        
        self.submit_tile(
            question=f"Who is {name}?",
            answer=f"{name} is a {race} {role}. {notes} (Faction: {faction or 'none'})"
        )
        return npc
    
    def add_faction(self, name: str, alignment: str, influence: int = 0):
        """Add a faction to the campaign."""
        fac = Faction(name=name, alignment=alignment, influence=influence)
        self.factions[name] = fac
        return fac
    
    def add_location(self, name: str, region: str, description: str, danger_level: int = 1):
        """Add a location."""
        loc = Location(name=name, region=region, description=description, danger_level=danger_level)
        self.locations[name] = loc
        return loc
    
    def log_encounter(self, location: str, participants: List[str], outcome: str,
                      loot: Optional[List[str]] = None, xp: int = 0):
        """Log a combat or social encounter."""
        enc_id = f"enc-{len(self.encounters)+1}"
        enc = Encounter(
            id=enc_id, location=location, participants=participants,
            outcome=outcome, timestamp=time.time(),
            loot=loot or [], xp_awarded=xp
        )
        self.encounters.append(enc)
        
        for name in participants:
            if name in self.npcs:
                self.npcs[name].last_seen = time.time()
        
        self.submit_tile(
            question=f"What happened at {location}?",
            answer=f"Encounter: {outcome}. Participants: {', '.join(participants)}. XP: {xp}"
        )
        return enc
    
    def get_relationship_web(self) -> Dict:
        """Map all NPC and faction relationships."""
        web = {"npcs": {}, "factions": {}}
        
        for name, npc in self.npcs.items():
            web["npcs"][name] = {
                "faction": npc.faction,
                "role": npc.role,
                "status": npc.status,
                "connections": []
            }
            for other_name, other in self.npcs.items():
                if other_name == name:
                    continue
                if other.faction == npc.faction and npc.faction:
                    web["npcs"][name]["connections"].append({"to": other_name, "type": "faction"})
        
        for fname, fac in self.factions.items():
            web["factions"][fname] = {
                "alignment": fac.alignment,
                "members": fac.members,
                "influence": fac.influence,
                "relations": fac.relations
            }
        
        return web
    
    def generate_quest_hook(self) -> Dict:
        """Generate a quest hook from campaign state."""
        if not self.npcs or not self.locations:
            return {"error": "Need NPCs and locations for quest generation"}
        
        quest_giver = random.choice([n for n in self.npcs.values() if n.role == "quest-giver"])
        target_loc = random.choice(list(self.locations.values()))
        enemy_faction = random.choice(list(self.factions.values())) if self.factions else None
        
        hooks = [
            f"{quest_giver.name} needs adventurers to investigate {target_loc.name}.",
            f"Rumors from {quest_giver.name} suggest treasure in {target_loc.name}.",
            f"{quest_giver.name} offers a reward for clearing {target_loc.name} of threats."
        ]
        
        return {
            "quest_giver": quest_giver.name,
            "location": target_loc.name,
            "hook": random.choice(hooks),
            "danger_level": target_loc.danger_level,
            "enemy_faction": enemy_faction.name if enemy_faction else None,
            "reward_hint": random.choice(["gold", "magic item", "faction favor", "information"])
        }
    
    def get_campaign_summary(self) -> Dict:
        """Full campaign state summary."""
        return {
            "campaign": self.campaign,
            "npcs_total": len(self.npcs),
            "npcs_alive": len([n for n in self.npcs.values() if n.status == "alive"]),
            "factions": len(self.factions),
            "locations": len(self.locations),
            "encounters": len(self.encounters),
            "sessions": len(self.sessions),
            "total_xp_awarded": sum(e.xp_awarded for e in self.encounters)
        }
    
    def run(self):
        """Main agent loop — setup demo campaign and submit insights."""
        print(f"DMLogAgent v{self.version} starting...")
        
        self.add_faction("Iron Harbor Guild", "lawful-neutral", influence=5)
        self.add_faction("The Crimson Tide", "chaotic-evil", influence=-3)
        self.add_location("Iron Harbor", "coastal", "Bustling port city with ironworks", 2)
        self.add_location("Crimson Cove", "coastal", "Pirate haven, hidden caves", 7)
        self.add_location("The Deep Woods", "forest", "Ancient forest with druid circles", 4)
        
        self.add_npc("Captain Thorne", "human", "quest-giver", "Iron Harbor Guild", hp=45, ac=16, notes="Retired pirate, now guildmaster")
        self.add_npc("Blackhook", "half-orc", "enemy", "The Crimson Tide", hp=60, ac=14, notes="Pirate captain with iron hook")
        self.add_npc("Elara", "elf", "ally", None, hp=30, ac=13, notes="Druid protecting the Deep Woods")
        self.add_npc("Skeev", "goblin", "neutral", None, hp=8, ac=12, notes="Informant, knows Crimson Cove layout")
        
        self.log_encounter("Iron Harbor", ["Captain Thorne", "Blackhook"], "negotiation", xp=0)
        self.log_encounter("Crimson Cove", ["Blackhook", "Skeev"], "combat victory", ["iron key", "50gp"], xp=150)
        self.log_encounter("The Deep Woods", ["Elara"], "social", xp=50)
        
        # Submit campaign summary
        summary = self.get_campaign_summary()
        self.submit_tile(
            "What is the campaign state?",
            json.dumps(summary, indent=2, default=str)
        )
        
        # Submit quest hook
        quest = self.generate_quest_hook()
        self.submit_tile(
            "What quest is available?",
            json.dumps(quest, indent=2, default=str)
        )
        
        print(f"Run complete. {len(self.npcs)} NPCs, {len(self.factions)} factions, {len(self.tiles_submitted)} tiles")

def main():
    agent = DMLogAgent(campaign="The Shattered Coast")
    agent.run()
    print(f"\nStats: {json.dumps(agent.get_stats(), indent=2)}")
    print(f"\nHealth: {json.dumps(agent.health_check(), indent=2)}")

if __name__ == "__main__":
    main()
