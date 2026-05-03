#!/usr/bin/env python3
"""
dmlog-agent — AI dungeon master tools for D&D and tabletop RPG campaigns
Track NPCs, factions, locations, sessions, and encounters.
Integrates with the PLATO fleet for campaign intelligence.
"""

import json, time, random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

@dataclass
class NPC:
    name: str
    race: str
    role: str  # ally, enemy, neutral, quest-giver
    faction: Optional[str] = None
    hp: int = 10
    ac: int = 10
    notes: str = ""
    last_seen: Optional[float] = None
    status: str = "alive"  # alive, dead, missing, imprisoned

@dataclass
class Faction:
    name: str
    alignment: str
    influence: int = 0  # -10 to +10
    members: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    relations: Dict[str, int] = field(default_factory=dict)  # faction name -> relation score

@dataclass
class Location:
    name: str
    region: str
    description: str
    discovered_by: List[str] = field(default_factory=list)
    connected_to: List[str] = field(default_factory=list)
    danger_level: int = 1  # 1-10

@dataclass
class Encounter:
    id: str
    location: str
    participants: List[str]  # NPC names
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

class DMLogAgent:
    def __init__(self, campaign: str = "default-campaign", plato_url: str = "http://147.224.38.131:8847"):
        self.campaign = campaign
        self.plato_url = plato_url.rstrip("/")
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
        
        self._submit_tile(
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
        
        # Update NPC last_seen
        for name in participants:
            if name in self.npcs:
                self.npcs[name].last_seen = time.time()
        
        self._submit_tile(
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
            # Find connections: same faction, encounter participants
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
        
        # Pick elements
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
    
    def _submit_tile(self, question: str, answer: str):
        payload = json.dumps({
            "question": question,
            "answer": answer,
            "agent": self.name,
            "room": "dmlog"
        }).encode()
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.plato_url}/submit", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                pass
        except Exception:
            pass

def demo():
    dm = DMLogAgent(campaign="The Shattered Coast")
    
    # Setup world
    dm.add_faction("Iron Harbor Guild", "lawful-neutral", influence=5)
    dm.add_faction("The Crimson Tide", "chaotic-evil", influence=-3)
    dm.add_location("Iron Harbor", "coastal", "Bustling port city with ironworks", 2)
    dm.add_location("Crimson Cove", "coastal", "Pirate haven, hidden caves", 7)
    dm.add_location("The Deep Woods", "forest", "Ancient forest with druid circles", 4)
    
    # Add NPCs
    dm.add_npc("Captain Thorne", "human", "quest-giver", "Iron Harbor Guild", hp=45, ac=16, notes="Retired pirate, now guildmaster")
    dm.add_npc("Blackhook", "half-orc", "enemy", "The Crimson Tide", hp=60, ac=14, notes="Pirate captain with iron hook")
    dm.add_npc("Elara", "elf", "ally", None, hp=30, ac=13, notes="Druid protecting the Deep Woods")
    dm.add_npc("Skeev", "goblin", "neutral", None, hp=8, ac=12, notes="Informant, knows Crimson Cove layout")
    
    # Log encounters
    dm.log_encounter("Iron Harbor", ["Captain Thorne", "Blackhook"], "negotiation", xp=0)
    dm.log_encounter("Crimson Cove", ["Blackhook", "Skeev"], "combat victory", ["iron key", "50gp"], xp=150)
    dm.log_encounter("The Deep Woods", ["Elara"], "social", xp=50)
    
    print("=== Campaign Summary ===")
    print(dm.get_campaign_summary())
    
    print("\n=== Relationship Web ===")
    web = dm.get_relationship_web()
    for name, data in web["npcs"].items():
        print(f"{name} ({data['role']}) — connections: {len(data['connections'])}")
    
    print("\n=== Quest Hook ===")
    quest = dm.generate_quest_hook()
    print(f"Hook: {quest['hook']}")
    print(f"Reward: {quest['reward_hint']}")
    print(f"Danger: {quest['danger_level']}/10")

if __name__ == "__main__":
    demo()
