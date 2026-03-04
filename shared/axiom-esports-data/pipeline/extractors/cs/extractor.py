import asyncio
import logging
import re
from datetime import datetime
from typing import AsyncIterator, Dict, Optional

from bs4 import BeautifulSoup

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class CSExtractor(BaseExtractor):
    """Counter-Strike data extractor from HLTV."""
    
    BASE_URL = "https://www.hltv.org"
    
    def __init__(self, rate_limiter, db_pool, coordinator_url: str):
        super().__init__(
            game_type="cs",
            source="hltv",
            rate_limiter=rate_limiter,
            db_pool=db_pool,
            coordinator_url=coordinator_url
        )
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': 'Mozilla/5.0 (compatible; AxiomBot/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def discover_matches(
        self,
        date_start: datetime,
        date_end: datetime,
        region: Optional[str] = None
    ) -> AsyncIterator[Dict]:
        """Discover CS matches from HLTV results page."""
        offset = 0
        while True:
            url = f"{self.BASE_URL}/results?offset={offset}"
            if region:
                url += f"&event={region}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HLTV results page failed: {response.status}")
                    break
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                result_links = soup.select('a.a-reset')
                if not result_links:
                    break
                
                for link in result_links:
                    href = link.get('href', '')
                    match_id = self._extract_match_id(href)
                    if match_id:
                        yield {
                            'id': match_id,
                            'url': f"{self.BASE_URL}{href}",
                            'source': 'hltv'
                        }
                
                offset += 100
                await asyncio.sleep(2)  # Rate limiting
    
    def _extract_match_id(self, href: str) -> Optional[str]:
        """Extract match ID from HLTV URL."""
        match = re.search(r'/matches/(\d+)/', href)
        return match.group(1) if match else None
    
    async def extract_match_detail(self, match_id: str) -> Dict:
        """Extract detailed CS match data from HLTV."""
        url = f"{self.BASE_URL}/matches/{match_id}/match"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch match {match_id}: {response.status}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract match data
            match_data = {
                'id': match_id,
                'game': 'cs',
                'source': 'hltv',
                'team_a': self._extract_team_name(soup, 1),
                'team_b': self._extract_team_name(soup, 2),
                'score_a': self._extract_score(soup, 1),
                'score_b': self._extract_score(soup, 2),
                'maps': self._extract_map_scores(soup),
                'date': self._extract_date(soup),
                'event': self._extract_event(soup),
                'players': self._extract_player_stats(soup),
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            return match_data
    
    def _extract_team_name(self, soup: BeautifulSoup, team_num: int) -> str:
        """Extract team name from match page."""
        selector = f'.team{team_num}-gradient .teamName'
        elem = soup.select_one(selector)
        return elem.text.strip() if elem else 'Unknown'
    
    def _extract_score(self, soup: BeautifulSoup, team_num: int) -> int:
        """Extract team score."""
        selector = f'.team{team_num}-gradient .score'
        elem = soup.select_one(selector)
        return int(elem.text.strip()) if elem else 0
    
    def _extract_map_scores(self, soup: BeautifulSoup) -> list:
        """Extract individual map scores."""
        maps = []
        map_elements = soup.select('.mapholder')
        
        for map_elem in map_elements:
            map_name = map_elem.select_one('.mapname')
            if map_name:
                maps.append({
                    'name': map_name.text.strip(),
                    'score_a': self._extract_map_score(map_elem, 1),
                    'score_b': self._extract_map_score(map_elem, 2)
                })
        
        return maps
    
    def _extract_map_score(self, map_elem, team_num: int) -> int:
        """Extract score for specific map."""
        selector = f'.results-team{team_num} .results-team-score'
        elem = map_elem.select_one(selector)
        return int(elem.text.strip()) if elem else 0
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract match date."""
        date_elem = soup.select_one('.date')
        if date_elem:
            return date_elem.get('data-unix', '')
        return ''
    
    def _extract_event(self, soup: BeautifulSoup) -> str:
        """Extract event/tournament name."""
        event_elem = soup.select_one('.event a')
        return event_elem.text.strip() if event_elem else 'Unknown'
    
    def _extract_player_stats(self, soup: BeautifulSoup) -> list:
        """Extract individual player statistics."""
        players = []
        
        # HLTV has stats tables for each team
        stats_tables = soup.select('.stats-table')
        
        for table in stats_tables:
            rows = table.select('tbody tr')
            for row in rows:
                player_cell = row.select_one('.player a')
                if player_cell:
                    players.append({
                        'name': player_cell.text.strip(),
                        'kills': self._extract_stat(row, 'kills'),
                        'deaths': self._extract_stat(row, 'deaths'),
                        'adr': self._extract_stat(row, 'adr'),
                        'kast': self._extract_stat(row, 'kast'),
                        'rating': self._extract_stat(row, 'rating')
                    })
        
        return players
    
    def _extract_stat(self, row, stat_name: str) -> float:
        """Extract specific statistic from row."""
        cell = row.select_one(f'.{stat_name}')
        if cell:
            try:
                return float(cell.text.strip())
            except ValueError:
                return 0.0
        return 0.0
    
    async def extract_player_stats(
        self,
        player_id: str,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None
    ) -> Dict:
        """Extract CS player statistics."""
        url = f"{self.BASE_URL}/stats/players/{player_id}/player"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch player {player_id}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            return {
                'id': player_id,
                'game': 'cs',
                'name': self._extract_player_name(soup),
                'team': self._extract_player_team(soup),
                'stats': self._extract_career_stats(soup),
                'extracted_at': datetime.utcnow().isoformat()
            }
    
    def _extract_player_name(self, soup: BeautifulSoup) -> str:
        """Extract player name."""
        name_elem = soup.select_one('.playerName')
        return name_elem.text.strip() if name_elem else 'Unknown'
    
    def _extract_player_team(self, soup: BeautifulSoup) -> str:
        """Extract current team."""
        team_elem = soup.select_one('.playerTeam')
        return team_elem.text.strip() if team_elem else 'Free Agent'
    
    def _extract_career_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract career statistics."""
        stats = {}
        stat_rows = soup.select('.stats-row')
        
        for row in stat_rows:
            label = row.select_one('.stats-label')
            value = row.select_one('.stats-value')
            
            if label and value:
                stats[label.text.strip().lower().replace(' ', '_')] = value.text.strip()
        
        return stats
    
    async def validate_data(self, data: Dict) -> bool:
        """Validate CS match data."""
        required_fields = ['id', 'team_a', 'team_b', 'players']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # Validate player stats
        if len(data['players']) < 2:  # At least 2 players
            return False
        
        return True
