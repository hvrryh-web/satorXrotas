"""Tests for RoleClassifier agent-to-role mapping."""
import pytest

from extraction.src.parsers.role_classifier import RoleClassifier, AGENT_ROLE_MAP


class TestRoleClassifier:
    def test_known_duelist_classified(self):
        clf = RoleClassifier()
        assert clf.classify("Jett") == "Entry"
        assert clf.classify("Reyna") == "Entry"
        assert clf.classify("Raze") == "Entry"

    def test_known_controller_classified(self):
        clf = RoleClassifier()
        assert clf.classify("Viper") == "Controller"
        assert clf.classify("Brimstone") == "Controller"
        assert clf.classify("Omen") == "Controller"

    def test_known_initiator_classified(self):
        clf = RoleClassifier()
        assert clf.classify("Sova") == "Initiator"
        assert clf.classify("Breach") == "Initiator"
        assert clf.classify("Skye") == "Initiator"

    def test_known_sentinel_classified(self):
        clf = RoleClassifier()
        assert clf.classify("Killjoy") == "Sentinel"
        assert clf.classify("Cypher") == "Sentinel"
        assert clf.classify("Sage") == "Sentinel"

    def test_none_agent_returns_none(self):
        clf = RoleClassifier()
        assert clf.classify(None) is None

    def test_unknown_agent_returns_none(self):
        clf = RoleClassifier()
        result = clf.classify("UnknownHero9000")
        assert result is None

    def test_all_mapped_agents_have_valid_role(self):
        """Every agent in AGENT_ROLE_MAP must map to a recognised role string."""
        valid_roles = {"Entry", "Controller", "Initiator", "Sentinel", "IGL"}
        clf = RoleClassifier()
        for agent, expected_role in AGENT_ROLE_MAP.items():
            role = clf.classify(agent)
            assert role in valid_roles, f"Agent {agent} mapped to unexpected role {role}"

    def test_igl_override(self):
        """IGL registry override should return 'IGL' regardless of agent."""
        from extraction.src.parsers.role_classifier import IGL_AGENTS
        IGL_AGENTS.add("testplayer:team123")
        clf = RoleClassifier()
        assert clf.classify_with_igl_check("Jett", "testplayer", "team123") == "IGL"
        IGL_AGENTS.discard("testplayer:team123")

    def test_non_igl_returns_agent_role(self):
        clf = RoleClassifier()
        result = clf.classify_with_igl_check("Jett", "someone", "someteam")
        assert result == "Entry"
