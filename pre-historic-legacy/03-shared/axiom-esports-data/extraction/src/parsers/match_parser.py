"""
Match Parser — Extracts structured data from VLR.gg match HTML.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class RawMatchData:
    vlr_match_id: str
    tournament: Optional[str]
    map_name: Optional[str]
    match_date: Optional[str]
    patch_version: Optional[str]
    players: list[dict] = field(default_factory=list)  # Raw player rows


class MatchParser:
    """
    Parses VLR.gg match scorecard HTML into structured RawMatchData.
    Schema version: v2 (2023+).
    """

    def parse(self, html: str, vlr_match_id: str) -> Optional[RawMatchData]:
        """
        Parse match HTML. Returns None if HTML does not match expected schema.
        Schema drift is logged and triggers an alert via integrity_checker.
        """
        if not self._has_expected_structure(html):
            logger.error(
                "Schema validation failed for match %s — possible drift", vlr_match_id
            )
            return None

        return RawMatchData(
            vlr_match_id=vlr_match_id,
            tournament=self._extract_tournament(html),
            map_name=self._extract_map(html),
            match_date=self._extract_date(html),
            patch_version=self._extract_patch(html),
            players=self._extract_players(html),
        )

    def _has_expected_structure(self, html: str) -> bool:
        """Basic structural validation — checks for required HTML elements."""
        required_markers = ["vm-stats-game", "mod-player", "mod-stat"]
        return all(marker in html for marker in required_markers)

    def _extract_tournament(self, html: str) -> Optional[str]:
        match = re.search(r'class="match-header-event[^>]*>.*?<div[^>]*>(.*?)</div>', html, re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_map(self, html: str) -> Optional[str]:
        match = re.search(r'class="map"[^>]*>.*?<span>(.*?)</span>', html, re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_date(self, html: str) -> Optional[str]:
        match = re.search(r'data-utc-ts="(\d+)"', html)
        return match.group(1) if match else None

    def _extract_patch(self, html: str) -> Optional[str]:
        match = re.search(r'Patch (\d+\.\d+)', html)
        return match.group(1) if match else None

    def _extract_players(self, html: str) -> list[dict]:
        """Extract player stat rows via BeautifulSoup table parsing."""
        soup = BeautifulSoup(html, "lxml")
        players: list[dict] = []

        stat_columns = ["rating", "acs", "kills", "deaths", "assists",
                        "kast", "adr", "hs_pct", "first_blood", "clutch_win"]

        for game_section in soup.find_all(class_="vm-stats-game"):
            for row in game_section.find_all(class_="mod-player"):
                player: dict = {}

                # Player name
                name_tag = row.find(class_="mod-player")
                if name_tag is None:
                    name_tag = row
                alias = row.find("div", class_="text-of")
                player["player"] = alias.get_text(strip=True) if alias else ""

                # Team — nearest ancestor with team class or data attribute
                team_tag = row.find_parent(class_=re.compile(r"team"))
                player["team"] = team_tag.get("data-team-name", "") if team_tag else ""

                # Agent image alt text
                agent_img = row.find("img")
                player["agent"] = agent_img.get("alt", "").strip() if agent_img else ""

                # Stat cells — each .mod-stat td in order
                stat_cells = row.find_all(class_="mod-stat")
                for idx, cell in enumerate(stat_cells):
                    if idx >= len(stat_columns):
                        break
                    value = cell.get_text(strip=True)
                    player[stat_columns[idx]] = value

                if player.get("player"):
                    players.append(player)

        return players
