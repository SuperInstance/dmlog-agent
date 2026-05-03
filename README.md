# dmlog-agent

Agent framework for [dmlog.ai](https://dmlog.ai) — dungeon master tools for D&D and tabletop RPG campaigns. Manages session notes, NPCs, factions, locations, and encounters.

## Features

- **NPC Tracking** — Track non-player characters with secrets, motivations, alignment, and status
- **Faction Management** — Organize factions with influence ratings, allies, and enemies
- **Location Database** — Map campaign locations with connections and notable features
- **Encounter Builder** — Create rated encounters with terrain, creatures, and objectives
- **Session Notes** — Record sessions with party members, loot, and quest progress
- **Export/Import** — JSON serialization for backup and portability

## Installation

```bash
pip install dmlog-agent
```

## Quick Start

```python
from dmlog_agent import (
    DMLogAgent,
    NPC,
    Faction,
    Location,
    Encounter,
    EncounterDifficulty,
    Alignment,
)

agent = DMLogAgent()

# Add NPCs
agent.add_npc(
    name="Mira Black",
    race="Half-Elf",
    occupation="Thieves Guild Leader",
    alignment=Alignment.ChaoticNeutral,
    faction="Thieves Guild",
    description="Silver-haired rogue with a sharp tongue",
    secrets="Secretly funding the rebellion",
)

# Add a faction
agent.add_faction(
    name="Thieves Guild",
    leader="Mira Black",
    headquarters="The Rusty Nail Tavern",
    influence=65,
    goals="Control the city's underground trade",
    enemies=["City Guard", "Merchants Association"],
)

# Add a location
agent.add_location(
    name="The Sunken Temple",
    region="Blighted Coast",
    description="An old temple half-submerged in black water",
    notable_features=["Altar of the Deep Ones", "Trident statues"],
    dangers="Carrion crawlers, water weird",
    loot="500 gp, potion of water breathing",
    connected_locations=["Blighted Coast", "Harbor Town"],
)

# Build an encounter
encounter = agent.build_encounter(
    title="Temple Guardians",
    creatures=["Carrion Crawler", "Water Weird"],
    creature_count=4,
    difficulty=EncounterDifficulty.Hard,
    location="The Sunken Temple",
    terrain="Partially flooded, crumbling pillars",
    objectives="Protect the mage casting Detect Treasure",
)

# Plan a session
agent.plan_session(
    session_number=1,
    title="The Sunken Temple",
    location="Blighted Coast",
    party_members=["Aldric", "Lyra", "Thorne", "Zara"],
    NPCs_present=["Mira Black"],
    encounters=[encounter],
    quest_progress="Found map to the Sunken Temple",
    next_session_hooks="What lies beneath the altar?",
    duration_minutes=180,
)

# Stats
stats = agent.get_campaign_stats()
print(f"Sessions run: {stats['total_sessions']}")
print(f"Total XP awarded: {stats['total_xp_awarded']}")
```

## API Overview

### NPCs

```python
npc = agent.add_npc(
    name="Grimjaw the Orc",
    race="Orc",
    occupation="Mercenary Captain",
    alignment=Alignment.NeutralEvil,
    location="Crossroads Inn",
    faction="Iron Banner Company",
    motivations="Gold and glory",
    secrets="Works for a secret benefactor",
)
```

### Factions

```python
faction = agent.add_faction(
    name="Iron Banner Company",
    leader="Captain Vorn",
    headquarters="Fort Ironhold",
    influence=70,
    allies=["Thieves Guild"],
    enemies=["Shadow Covenant"],
)
```

### Locations

```python
loc = agent.add_location(
    name="Crossroads Inn",
    region="Heartland",
    description="A busy inn at the intersection of two trade routes",
    notable_features=["Trading post", "Job board", "Secret basement"],
    connected_locations=["Capital City", "Border Fort"],
)
```

### Encounters

```python
enc = agent.build_encounter(
    title="Ambush at the Crossroads",
    creatures=["Bandit", "Bandit Captain"],
    creature_count=6,
    difficulty=EncounterDifficulty.Medium,
    terrain="Open road, overturned cart cover",
    objectives="Survive and capture the leader",
)
```

## Development

```bash
pip install -e .
pytest tests/
```

## License

MIT
