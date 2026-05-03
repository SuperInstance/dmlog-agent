"""
dmlog_agent — Agent framework for dmlog.ai

Dungeon master tools: session notes, NPC tracking, encounter building,
and campaign management for tabletop RPG campaigns.
Integrates with the PLATO memory layer for persistent world state.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional
import json

__version__ = "0.1.0"
__all__ = [
    "NPC",
    "Faction",
    "Location",
    "Encounter",
    "SessionNote",
    "DMLogAgent",
    "CreatureType",
    "Alignment",
    "EncounterDifficulty",
]


class CreatureType(Enum):
    """D&D creature types."""
    Aberration = "aberration"
    Beast = "beast"
    Celestial = "celestial"
    Construct = "construct"
    Dragon = "dragon"
    Elemental = "elemental"
    Fey = "fey"
    Fiend = "fiend"
    Giant = "giant"
    Humanoid = "humanoid"
    Monster = "monster"
    Ooze = "ooze"
    Plant = "plant"
    Undead = "undead"


class Alignment(Enum):
    """D&D alignment grid."""
    LawfulGood = "lawful good"
    NeutralGood = "neutral good"
    ChaoticGood = "chaotic good"
    LawfulNeutral = "lawful neutral"
    Neutral = "neutral"
    ChaoticNeutral = "chaotic neutral"
    LawfulEvil = "lawful evil"
    NeutralEvil = "neutral evil"
    ChaoticEvil = "chaotic evil"
    Unaligned = "unaligned"


class EncounterDifficulty(Enum):
    """Encounter difficulty rating."""
    Trivial = "trivial"       # Easy
    Easy = "easy"
    Medium = "medium"
    Hard = "hard"
    Deadly = "deadly"         # 5e XP thresholds used as reference


@dataclass
class NPC:
    """
    A non-player character in the campaign.

    Attributes:
        name: Character name
        race: Race/species
        occupation: What they do
        alignment: Moral and ethical alignment
        location: Where they are found
        faction: Optional faction membership
        description: Physical/personality description
        motivations: What drives them
        secrets: Hidden information the party doesn't know
        notes: DM-only notes
        is_alive: Whether they're currently alive
        met_on: Session date when first encountered
        last_seen: Last session date they were active
    """
    name: str
    race: str = ""
    occupation: str = ""
    alignment: Optional[Alignment] = None
    location: str = ""
    faction: str = ""
    description: str = ""
    motivations: str = ""
    secrets: str = ""
    notes: str = ""
    is_alive: bool = True
    met_on: Optional[date] = None
    last_seen: Optional[date] = None

    def mark_dead(self, cause: str = "") -> None:
        """Record the NPC's death."""
        self.is_alive = False
        if cause:
            self.notes = f"{self.notes}\nDeath: {cause}".strip()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "race": self.race,
            "occupation": self.occupation,
            "alignment": self.alignment.value if self.alignment else None,
            "location": self.location,
            "faction": self.faction,
            "description": self.description,
            "motivations": self.motivations,
            "secrets": self.secrets,
            "notes": self.notes,
            "is_alive": self.is_alive,
            "met_on": self.met_on.isoformat() if self.met_on else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        data = data.copy()
        if data.get("alignment"):
            data["alignment"] = Alignment(data["alignment"])
        return cls(**data)


@dataclass
class Faction:
    """A faction or organization within the campaign."""
    name: str
    description: str = ""
    leader: str = ""
    headquarters: str = ""
    influence: int = 50  # 0-100 scale
    resources: str = ""
    goals: str = ""
    allies: list[str] = field(default_factory=list)  # Other faction names
    enemies: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "leader": self.leader,
            "headquarters": self.headquarters,
            "influence": self.influence,
            "resources": self.resources,
            "goals": self.goals,
            "allies": self.allies,
            "enemies": self.enemies,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Faction":
        return cls(**data)


@dataclass
class Location:
    """A named location in the campaign world."""
    name: str
    region: str = ""
    description: str = ""
    notable_features: list[str] = field(default_factory=list)
    NPCs_present: list[str] = field(default_factory=list)  # NPC names
    dangers: str = ""
    loot: str = ""
    connected_locations: list[str] = field(default_factory=list)
    session_visited: list[int] = field(default_factory=list)  # Session numbers

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "region": self.region,
            "description": self.description,
            "notable_features": self.notable_features,
            "NPCs_present": self.NPCs_present,
            "dangers": self.dangers,
            "loot": self.loot,
            "connected_locations": self.connected_locations,
            "session_visited": self.session_visited,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Location":
        return cls(**data)


@dataclass
class Encounter:
    """
    An encounter (combat or otherwise) within a session.

    Attributes:
        title: Encounter name
        description: Setup and context
        difficulty: Rated difficulty
        creatures: List of creature descriptions or names
        creature_count: Number of enemies
        location: Where the encounter takes place
        terrain: Battlefield terrain features
        objectives: What the party needs to achieve
        outcome: Result of the encounter
        xp_reward: Experience points awarded
        session_number: Which session this was in
        notes: DM notes
    """
    title: str
    description: str = ""
    difficulty: EncounterDifficulty = EncounterDifficulty.Medium
    creatures: list[str] = field(default_factory=list)
    creature_count: int = 0
    location: str = ""
    terrain: str = ""
    objectives: str = ""
    outcome: str = ""
    xp_reward: int = 0
    session_number: Optional[int] = None
    notes: str = ""

    def set_outcome(self, outcome: str, xp: int = 0) -> None:
        """Record the encounter outcome."""
        self.outcome = outcome
        if xp > 0:
            self.xp_reward = xp

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty.value,
            "creatures": self.creatures,
            "creature_count": self.creature_count,
            "location": self.location,
            "terrain": self.terrain,
            "objectives": self.objectives,
            "outcome": self.outcome,
            "xp_reward": self.xp_reward,
            "session_number": self.session_number,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Encounter":
        data = data.copy()
        data["difficulty"] = EncounterDifficulty(data["difficulty"])
        return cls(**data)


@dataclass
class SessionNote:
    """
    Notes for a single gaming session.

    Attributes:
        session_number: Sequential session number
        date: Real-world date of the session
        title: Session title/synopsis
        location: Where the party was
        party_members: Who played
        NPCs_present: NPCs that appeared
        encounters: List of encounters run
        loot_gained: Items/money awarded
        quest_progress: Updates to ongoing quests
        next_session_hooks: Plot hooks for next time
        highlights: Memorable moments
        duration_minutes: How long the session ran
        notes: General DM notes
    """
    session_number: int
    date: date = field(default_factory=date.today)
    title: str = ""
    location: str = ""  # In-world location
    party_members: list[str] = field(default_factory=list)
    NPCs_present: list[str] = field(default_factory=list)  # NPC names
    encounters: list[Encounter] = field(default_factory=list)
    loot_gained: str = ""
    quest_progress: str = ""
    next_session_hooks: str = ""
    highlights: str = ""
    duration_minutes: int = 0
    notes: str = ""

    def add_encounter(self, encounter: Encounter) -> None:
        """Add an encounter to the session."""
        encounter.session_number = self.session_number
        self.encounters.append(encounter)

    @property
    def total_xp(self) -> int:
        return sum(e.xp_reward for e in self.encounters)

    def to_dict(self) -> dict:
        return {
            "session_number": self.session_number,
            "date": self.date.isoformat(),
            "title": self.title,
            "location": self.location,
            "party_members": self.party_members,
            "NPCs_present": self.NPCs_present,
            "encounters": [e.to_dict() for e in self.encounters],
            "loot_gained": self.loot_gained,
            "quest_progress": self.quest_progress,
            "next_session_hooks": self.next_session_hooks,
            "highlights": self.highlights,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionNote":
        data = data.copy()
        data["date"] = date.fromisoformat(data["date"])
        data["encounters"] = [Encounter.from_dict(e) for e in data.get("encounters", [])]
        return cls(**data)


class DMLogAgent:
    """
    Agent for managing tabletop RPG campaigns.

    Tracks NPCs, factions, locations, sessions, and encounters.
    Provides session planning and campaign statistics.
    Integrates with PLATO for persistent world memory.

    Example:
        agent = DMLogAgent()
        agent.add_npc("Gruk the Orc", race="Orc", occupation="Barkeep")
        agent.add_faction("Thieves Guild", leader="Mira Black")
        agent.plan_session(5)
        stats = agent.get_campaign_stats()
    """

    def __init__(self, Plato_URL: str = "http://localhost:8847"):
        self.plato_url = Plato_URL
        self.npcs: list[NPC] = []
        self.factions: list[Faction] = []
        self.locations: list[Location] = []
        self.sessions: list[SessionNote] = []
        self._session_counter = 0

    def add_npc(
        self,
        name: str,
        race: str = "",
        occupation: str = "",
        alignment: Optional[Alignment] = None,
        location: str = "",
        faction: str = "",
        description: str = "",
        motivations: str = "",
        secrets: str = "",
        notes: str = "",
        met_on: Optional[date] = None,
    ) -> NPC:
        """
        Register a new NPC.

        Args:
            name: NPC name
            race: Race/species
            occupation: Their job/role
            alignment: Moral/ethical alignment
            location: Where they're found
            faction: Faction membership
            description: Physical/personality description
            motivations: What drives them
            secrets: Hidden information
            notes: DM notes
            met_on: When the party first met them

        Returns:
            The created NPC
        """
        npc = NPC(
            name=name,
            race=race,
            occupation=occupation,
            alignment=alignment,
            location=location,
            faction=faction,
            description=description,
            motivations=motivations,
            secrets=secrets,
            notes=notes,
            met_on=met_on or date.today(),
            last_seen=met_on or date.today(),
        )
        self.npcs.append(npc)
        return npc

    def find_npc(self, name: str) -> Optional[NPC]:
        """Find an NPC by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for npc in self.npcs:
            if name_lower in npc.name.lower():
                return npc
        return None

    def get_npcs_by_faction(self, faction_name: str) -> list[NPC]:
        """Get all NPCs belonging to a faction."""
        return [n for n in self.npcs if n.faction == faction_name]

    def get_npcs_by_location(self, location: str) -> list[NPC]:
        """Get all NPCs at a given location."""
        return [n for n in self.npcs if n.location == location]

    def kill_npc(self, name: str, cause: str = "") -> bool:
        """Kill an NPC. Returns True if found and marked dead."""
        npc = self.find_npc(name)
        if npc:
            npc.mark_dead(cause)
            return True
        return False

    def add_faction(
        self,
        name: str,
        description: str = "",
        leader: str = "",
        headquarters: str = "",
        influence: int = 50,
        resources: str = "",
        goals: str = "",
        allies: Optional[list[str]] = None,
        enemies: Optional[list[str]] = None,
        notes: str = "",
    ) -> Faction:
        """
        Add a faction to the campaign.

        Args:
            name: Faction name
            description: What the faction is
            leader: Current leader
            headquarters: Base of operations
            influence: Power level 0-100
            resources: Available resources
            goals: What they want to achieve
            allies: Friendly factions
            enemies: Hostile factions
            notes: DM notes

        Returns:
            The created Faction
        """
        faction = Faction(
            name=name,
            description=description,
            leader=leader,
            headquarters=headquarters,
            influence=influence,
            resources=resources,
            goals=goals,
            allies=allies or [],
            enemies=enemies or [],
            notes=notes,
        )
        self.factions.append(faction)
        return faction

    def find_faction(self, name: str) -> Optional[Faction]:
        name_lower = name.lower()
        for f in self.factions:
            if name_lower in f.name.lower():
                return f
        return None

    def add_location(
        self,
        name: str,
        region: str = "",
        description: str = "",
        notable_features: Optional[list[str]] = None,
        dangers: str = "",
        loot: str = "",
        connected_locations: Optional[list[str]] = None,
    ) -> Location:
        """
        Add a location to the campaign world.

        Args:
            name: Location name
            region: Broader region
            description: Description of the place
            notable_features: Points of interest
            dangers: Hazards or threats
            loot: Treasure or items found there
            connected_locations: Nearby locations

        Returns:
            The created Location
        """
        loc = Location(
            name=name,
            region=region,
            description=description,
            notable_features=notable_features or [],
            dangers=dangers,
            loot=loot,
            connected_locations=connected_locations or [],
        )
        self.locations.append(loc)
        return loc

    def plan_session(
        self,
        session_number: int,
        date: Optional[date] = None,
        title: str = "",
        location: str = "",
        party_members: Optional[list[str]] = None,
        NPCs_present: Optional[list[str]] = None,
        encounters: Optional[list[Encounter]] = None,
        quest_progress: str = "",
        next_session_hooks: str = "",
        duration_minutes: int = 0,
        notes: str = "",
    ) -> SessionNote:
        """
        Create a session plan or record.

        Args:
            session_number: Session number
            date: Real-world date
            title: Session title
            location: In-world starting location
            party_members: Who played
            NPCs_present: NPCs that appear
            encounters: Encounters for this session
            quest_progress: Updates
            next_session_hooks: Plot hooks
            duration_minutes: How long it ran
            notes: DM notes

        Returns:
            The created SessionNote
        """
        session = SessionNote(
            session_number=session_number,
            date=date or date.today(),
            title=title,
            location=location,
            party_members=party_members or [],
            NPCs_present=NPCs_present or [],
            encounters=encounters or [],
            quest_progress=quest_progress,
            next_session_hooks=next_session_hooks,
            duration_minutes=duration_minutes,
            notes=notes,
        )
        self.sessions.append(session)
        self.sessions.sort(key=lambda s: s.session_number)
        if session_number > self._session_counter:
            self._session_counter = session_number
        return session

    def find_session(self, session_number: int) -> Optional[SessionNote]:
        for s in self.sessions:
            if s.session_number == session_number:
                return s
        return None

    def build_encounter(
        self,
        title: str,
        creatures: list[str],
        creature_count: int,
        difficulty: EncounterDifficulty = EncounterDifficulty.Medium,
        description: str = "",
        location: str = "",
        terrain: str = "",
        objectives: str = "",
        notes: str = "",
    ) -> Encounter:
        """
        Build an encounter for a session.

        Args:
            title: Encounter name
            creatures: Types of creatures
            creature_count: Number of enemies
            difficulty: Difficulty rating
            description: Setup text
            location: Battlefield location
            terrain: Terrain features
            objectives: Party goals
            notes: DM notes

        Returns:
            The created Encounter
        """
        encounter = Encounter(
            title=title,
            description=description,
            difficulty=difficulty,
            creatures=creatures,
            creature_count=creature_count,
            location=location,
            terrain=terrain,
            objectives=objectives,
            notes=notes,
        )
        return encounter

    def get_campaign_stats(self) -> dict:
        """
        Compute campaign statistics.

        Returns:
            Dictionary with session counts, NPC counts, encounter summaries
        """
        total_encounters = sum(len(s.encounters) for s in self.sessions)
        total_xp = sum(s.total_xp for s in self.sessions)
        total_duration = sum(s.duration_minutes for s in self.sessions)
        alive_npcs = sum(1 for n in self.npcs if n.is_alive)
        dead_npcs = len(self.npcs) - alive_npcs

        difficulty_counts = {}
        for s in self.sessions:
            for e in s.encounters:
                difficulty_counts[e.difficulty.value] = (
                    difficulty_counts.get(e.difficulty.value, 0) + 1
                )

        return {
            "total_sessions": len(self.sessions),
            "total_encounters": total_encounters,
            "total_xp_awarded": total_xp,
            "total_playtime_minutes": total_duration,
            "total_npcs": len(self.npcs),
            "alive_npcs": alive_npcs,
            "dead_npcs": dead_npcs,
            "total_factions": len(self.factions),
            "total_locations": len(self.locations),
            "encounters_by_difficulty": difficulty_counts,
        }

    def export_json(self) -> str:
        """Export all campaign data as JSON."""
        data = {
            "version": __version__,
            "npcs": [n.to_dict() for n in self.npcs],
            "factions": [f.to_dict() for f in self.factions],
            "locations": [l.to_dict() for l in self.locations],
            "sessions": [s.to_dict() for s in self.sessions],
        }
        return json.dumps(data, indent=2, default=str)

    def import_json(self, json_str: str) -> None:
        """Import campaign data from JSON string."""
        data = json.loads(json_str)
        self.npcs = [NPC.from_dict(n) for n in data.get("npcs", [])]
        self.factions = [Faction.from_dict(f) for f in data.get("factions", [])]
        self.locations = [Location.from_dict(l) for l in data.get("locations", [])]
        self.sessions = [SessionNote.from_dict(s) for s in data.get("sessions", [])]
        if self.sessions:
            self._session_counter = max(s.session_number for s in self.sessions)
