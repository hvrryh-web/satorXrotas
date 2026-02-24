"""
Role Classifier — Maps agent picks to gameplay roles.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Agent-to-role mapping (Valorant agents as of 2026)
AGENT_ROLE_MAP = {
    # Duelists (Entry)
    "Jett": "Entry", "Reyna": "Entry", "Phoenix": "Entry",
    "Raze": "Entry", "Neon": "Entry", "Iso": "Entry", "Waylay": "Entry",

    # Controllers
    "Brimstone": "Controller", "Viper": "Controller", "Omen": "Controller",
    "Astra": "Controller", "Harbor": "Controller", "Clove": "Controller",

    # Initiators
    "Sova": "Initiator", "Breach": "Initiator", "Skye": "Initiator",
    "KAY/O": "Initiator", "Fade": "Initiator", "Gekko": "Initiator",
    "Vyse": "Initiator",

    # Sentinels
    "Sage": "Sentinel", "Cypher": "Sentinel", "Killjoy": "Sentinel",
    "Chamber": "Sentinel", "Deadlock": "Sentinel",
}

# IGL assignment: based on team captain data, not agent pick
IGL_AGENTS: set[str] = set()  # Populated from external IGL registry


class RoleClassifier:
    """
    Classifies player role from agent pick.
    IGL role requires external metadata — agent pick alone is insufficient.
    """

    def classify(self, agent: Optional[str]) -> Optional[str]:
        if not agent:
            return None
        role = AGENT_ROLE_MAP.get(agent)
        if not role:
            logger.warning("Unknown agent: %s — role unclassified", agent)
        return role

    def is_igl(self, player_name: str, team: str) -> bool:
        """
        Determines IGL status from external registry.
        Never inferred from agent pick alone (circular logic risk).
        """
        key = f"{player_name.lower()}:{team.lower()}"
        return key in IGL_AGENTS

    def classify_with_igl_check(
        self, agent: Optional[str], player_name: str, team: str
    ) -> Optional[str]:
        """Full role classification including IGL override."""
        if self.is_igl(player_name, team):
            return "IGL"
        return self.classify(agent)
