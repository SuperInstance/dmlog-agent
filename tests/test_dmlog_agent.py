"""
Tests for dmlog_agent.
"""

from datetime import date

import pytest

from dmlog_agent import (
    DMLogAgent,
    NPC,
    Faction,
    Location,
    Encounter,
    SessionNote,
    Alignment,
    EncounterDifficulty,
    CreatureType,
)


class TestNPC:
    def test_add_npc(self):
        agent = DMLogAgent()
        npc = agent.add_npc(
            name="Mira Black",
            race="Half-Elf",
            occupation="Rogue",
            alignment=Alignment.ChaoticNeutral,
        )
        assert npc.name == "Mira Black"
        assert npc.race == "Half-Elf"
        assert npc.is_alive is True

    def test_find_npc_partial(self):
        agent = DMLogAgent()
        agent.add_npc("Zara the Seer")
        found = agent.find_npc("seer")
        assert found is not None
        assert found.name == "Zara the Seer"

    def test_kill_npc(self):
        agent = DMLogAgent()
        agent.add_npc("Gruk")
        result = agent.kill_npc("Gruk", cause="Fell off a cliff")
        assert result is True
        npc = agent.find_npc("Gruk")
        assert npc.is_alive is False

    def test_get_npcs_by_faction(self):
        agent = DMLogAgent()
        agent.add_npc("Bob", faction="Thieves Guild")
        agent.add_npc("Alice", faction="Thieves Guild")
        agent.add_npc("Carol", faction="Merchants")
        members = agent.get_npcs_by_faction("Thieves Guild")
        assert len(members) == 2

    def test_npc_serialization(self):
        npc = NPC(
            name="Test",
            race="Human",
            alignment=Alignment.LawfulGood,
        )
        data = npc.to_dict()
        restored = NPC.from_dict(data)
        assert restored.name == npc.name
        assert restored.alignment == npc.alignment


class TestFaction:
    def test_add_faction(self):
        agent = DMLogAgent()
        f = agent.add_faction(
            name="Thieves Guild",
            leader="Mira",
            influence=75,
            enemies=["City Guard"],
        )
        assert f.name == "Thieves Guild"
        assert f.influence == 75
        assert "City Guard" in f.enemies

    def test_find_faction(self):
        agent = DMLogAgent()
        agent.add_faction("Shadow Covenant")
        found = agent.find_faction("shadow")
        assert found is not None
        assert found.name == "Shadow Covenant"


class TestLocation:
    def test_add_location(self):
        agent = DMLogAgent()
        loc = agent.add_location(
            name="The Old Mine",
            region="Mountain Pass",
            description="Abandoned silver mine",
            notable_features=["Collapsed shaft", "Strange symbols"],
            connected_locations=["Mountain Village"],
        )
        assert loc.name == "The Old Mine"
        assert len(loc.notable_features) == 2
        assert "Mountain Village" in loc.connected_locations


class TestEncounter:
    def test_build_encounter(self):
        agent = DMLogAgent()
        enc = agent.build_encounter(
            title="Goblin Ambush",
            creatures=["Goblin", "Goblin Boss"],
            creature_count=8,
            difficulty=EncounterDifficulty.Medium,
            terrain="Forest clearing",
            objectives="Break through to the village",
        )
        assert enc.title == "Goblin Ambush"
        assert enc.creature_count == 8
        assert enc.difficulty == EncounterDifficulty.Medium

    def test_encounter_outcome(self):
        enc = Encounter(title="Test")
        enc.set_outcome("Victory! Party captured leader.", xp=200)
        assert enc.outcome == "Victory! Party captured leader."
        assert enc.xp_reward == 200


class TestSession:
    def test_plan_session(self):
        agent = DMLogAgent()
        session = agent.plan_session(
            session_number=1,
            title="Session 1: The Beginning",
            location="Tavern",
            party_members=["Alice", "Bob"],
            duration_minutes=180,
        )
        assert session.session_number == 1
        assert session.duration_minutes == 180
        assert "Alice" in session.party_members

    def test_session_total_xp(self):
        agent = DMLogAgent()
        enc1 = agent.build_encounter("E1", [], 1, xp_reward=100)
        enc2 = agent.build_encounter("E2", [], 1, xp_reward=150)
        session = agent.plan_session(1, encounters=[enc1, enc2])
        assert session.total_xp == 250

    def test_session_serialization(self):
        session = SessionNote(
            session_number=5,
            date=date(2024, 3, 15),
            title="Test Session",
            party_members=["P1", "P2"],
        )
        data = session.to_dict()
        restored = SessionNote.from_dict(data)
        assert restored.session_number == 5
        assert restored.title == "Test Session"


class TestStatistics:
    def test_campaign_stats(self):
        agent = DMLogAgent()
        agent.add_npc("Npc1")
        agent.add_npc("Npc2")
        agent.add_faction("Faction1")
        enc = agent.build_encounter("Enc1", ["Goblin"], 3, xp_reward=100)
        agent.plan_session(1, encounters=[enc])

        stats = agent.get_campaign_stats()
        assert stats["total_npcs"] == 2
        assert stats["total_factions"] == 1
        assert stats["total_encounters"] == 1
        assert stats["total_xp_awarded"] == 100


class TestExportImport:
    def test_export_import_json(self):
        agent = DMLogAgent()
        agent.add_npc("Test NPC", race="Elf")
        agent.add_faction("Test Faction")
        agent.add_location("Test Location")
        agent.plan_session(1, title="Test Session")

        exported = agent.export_json()
        agent2 = DMLogAgent()
        agent2.import_json(exported)

        assert len(agent2.npcs) == 1
        assert len(agent2.factions) == 1
        assert len(agent2.locations) == 1
        assert len(agent2.sessions) == 1
