import asyncio
import logging
import re
from datetime import datetime
from typing import AsyncIterator, Dict, Optional

from bs4 import BeautifulSoup

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class ValorantExtractor(BaseExtractor):
    """Valorant data extractor from VLR.gg."""
    
    BASE_URL = "https://www.vlr.gg"
    
    def __init__(self, rate_limiter, db_pool, coordinator_url: str):
        super().__init__(
            game_type="valorant",
            source="vlr",
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
        """Discover Valorant matches from VLR.gg results page."""
        page = 1
        while True:
            url = f"{self.BASE_URL}/matches/results/?page={page}"
            if region:
                url += f"&region={region}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"VLR results page failed: {response.status}")
                    break
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # VLR.gg match cards
                match_links = soup.select('a.wf-module-item')
                if not match_links:
                    break
                
                for link in match_links:
                    href = link.get('href', '')
                    match_id = self._extract_match_id(href)
                    if match_id:
                        yield {
                            'id': match_id,
                            'url': f"{self.BASE_URL}{href}",
                            'source': 'vlr'
                        }
                
                page += 1
                await asyncio.sleep(2)  # Rate limiting
    
    def _extract_match_id(self, href: str) -> Optional[str]:
        """Extract match ID from VLR URL."""
        match = re.search(r'/(\d+)/', href)
        return match.group(1) if match else None
    
    async def extract_match_detail(self, match_id: str) -> Dict:
        """Extract detailed Valorant match data from VLR.gg."""
        url = f"{self.BASE_URL}/{match_id}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch match {match_id}: {response.status}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract match data
            match_data = {
                'id': match_id,
                'game': 'valorant',
                'source': 'vlr',
                'team_a': self._extract_team_name(soup, 1),
                'team_b': self._extract_team_name(soup, 2),
                'score_a': self._extract_score(soup, 1),
                'score_b': self._extract_score(soup, 2),
                'maps': self._extract_map_scores(soup),
                'date': self._extract_date(soup),
                'event': self._extract_event(soup),
                'players': self._extract_player_stats(soup),
                'agents': self._extract_agent_compositions(soup),
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            return match_data
    
    def _extract_team_name(self, soup: BeautifulSoup, team_num: int) -> str:
        """Extract team name from match page."""
        # VLR team names are in match-header vs mod-1/mod-2
        teams = soup.select('.match-header-vs .wf-title-med')
        if teams and len(teams) >= team_num:
            return teams[team_num - 1].text.strip()
        
        # Fallback selector
        selector = f'.match-header-vs.mod-{team_num} .wf-title-med'
        elem = soup.select_one(selector)
        return elem.text.strip() if elem else 'Unknown'
    
    def _extract_score(self, soup: BeautifulSoup, team_num: int) -> int:
        """Extract team score."""
        scores = soup.select('.match-header-vs .js-spoiler')
        if scores and len(scores) >= team_num:
            try:
                return int(scores[team_num - 1].text.strip())
            except ValueError:
                return 0
        return 0
    
    def _extract_map_scores(self, soup: BeautifulSoup) -> list:
        """Extract individual map scores."""
        maps = []
        map_elements = soup.select('.vm-stats-game')
        
        for map_elem in map_elements:
            map_name_elem = map_elem.select_one('.map')
            if map_name_elem:
                map_name = map_name_elem.text.strip()
                # Extract map-specific scores from team stats
                team_a_score = self._extract_map_team_score(map_elem, 1)
                team_b_score = self._extract_map_team_score(map_elem, 2)
                
                maps.append({
                    'name': map_name,
                    'score_a': team_a_score,
                    'score_b': team_b_score,
                    'duration': self._extract_map_duration(map_elem)
                })
        
        return maps
    
    def _extract_map_team_score(self, map_elem, team_num: int) -> int:
        """Extract team score for a specific map."""
        # VLR has different score displays
        score_elem = map_elem.select_one(f'.team{team_num} .score')
        if score_elem:
            try:
                return int(score_elem.text.strip())
            except ValueError:
                pass
        return 0
    
    def _extract_map_duration(self, map_elem) -> str:
        """Extract map duration."""
        duration_elem = map_elem.select_one('.map-duration')
        return duration_elem.text.strip() if duration_elem else ''
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract match date."""
        date_elem = soup.select_one('.match-header-date .moment-tz-convert')
        if date_elem:
            return date_elem.get('data-utc-ts', '')
        
        # Fallback
        date_elem = soup.select_one('.match-header-date')
        return date_elem.text.strip() if date_elem else ''
    
    def _extract_event(self, soup: BeautifulSoup) -> str:
        """Extract event/tournament name."""
        event_elem = soup.select_one('.match-header-event .match-header-event-series')
        if event_elem:
            return event_elem.text.strip()
        
        # Fallback
        event_elem = soup.select_one('.match-header-event')
        return event_elem.text.strip() if event_elem else 'Unknown'
    
    def _extract_agent_compositions(self, soup: BeautifulSoup) -> Dict:
        """Extract agent compositions for each team."""
        compositions = {'team_a': [], 'team_b': []}
        
        # VLR displays agents in team composition section
        comp_sections = soup.select('.compositions')
        
        for idx, section in enumerate(comp_sections[:2]):
            team_key = 'team_a' if idx == 0 else 'team_b'
            agents = section.select('.agent-icon')
            
            for agent in agents:
                agent_name = agent.get('title', '') or agent.get('alt', '')
                if agent_name:
                    compositions[team_key].append(agent_name)
        
        return compositions
    
    def _extract_player_stats(self, soup: BeautifulSoup) -> list:
        """Extract individual player statistics."""
        players = []
        
        # VLR has stats tables per map, aggregate from all
        stats_tables = soup.select('.wf-table-inset')
        
        for table in stats_tables:
            rows = table.select('tbody tr')
            for row in rows:
                player_cell = row.select_one('.text-of')
                if player_cell:
                    players.append({
                        'name': player_cell.text.strip(),
                        'agent': self._extract_player_agent(row),
                        'acs': self._extract_stat(row, 'acs'),
                        'kills': self._extract_stat(row, 'k'),
                        'deaths': self._extract_stat(row, 'd'),
                        'assists': self._extract_stat(row, 'a'),
                        'kd': self._extract_stat(row, 'kd'),
                        'adr': self._extract_stat(row, 'adr'),
                        'fk': self._extract_stat(row, 'fk'),
                        'fd': self._extract_stat(row, 'fd'),
                        'rating': self._extract_vlr_rating(row)
                    })
        
        return players
    
    def _extract_player_agent(self, row) -> str:
        """Extract agent played by player."""
        agent_img = row.select_one('.agent-icon img')
        if agent_img:
            return agent_img.get('title', '') or agent_img.get('alt', '')
        return ''
    
    def _extract_stat(self, row, stat_name: str) -> float:
        """Extract specific statistic from row."""
        # VLR stats are in td elements with specific classes or order
        cells = row.select('td')
        stat_map = {
            'acs': 2,
            'k': 3,
            'd': 4,
            'a': 5,
            'kd': 6,
            'adr': 7,
            'fk': 8,
            'fd': 9
        }
        
        idx = stat_map.get(stat_name)
        if idx is not None and len(cells) > idx:
            try:
                return float(cells[idx].text.strip())
            except ValueError:
                return 0.0
        return 0.0
    
    def _extract_vlr_rating(self, row) -> float:
        """Extract VLR rating (usually last column or specific class)."""
        rating_elem = row.select_one('.rating')
        if rating_elem:
            try:
                return float(rating_elem.text.strip())
            except ValueError:
                return 0.0
        
        # Try last cell as fallback
        cells = row.select('td')
        if cells:
            try:
                return float(cells[-1].text.strip())
            except ValueError:
                pass
        return 0.0
    
    async def extract_player_stats(
        self,
        player_id: str,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None
    ) -> Dict:
        """Extract Valorant player statistics."""
        url = f"{self.BASE_URL}/player/{player_id}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch player {player_id}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            return {
                'id': player_id,
                'game': 'valorant',
                'name': self._extract_player_name(soup),
                'team': self._extract_player_team(soup),
                'region': self._extract_player_region(soup),
                'stats': self._extract_career_stats(soup),
                'agents': self._extract_agent_stats(soup),
                'extracted_at': datetime.utcnow().isoformat()
            }
    
    def _extract_player_name(self, soup: BeautifulSoup) -> str:
        """Extract player name."""
        name_elem = soup.select_one('.player-header h1')
        return name_elem.text.strip() if name_elem else 'Unknown'
    
    def _extract_player_team(self, soup: BeautifulSoup) -> str:
        """Extract current team."""
        team_elem = soup.select_one('.player-header a[href*="/team/"]')
        return team_elem.text.strip() if team_elem else 'Free Agent'
    
    def _extract_player_region(self, soup: BeautifulSoup) -> str:
        """Extract player region."""
        region_elem = soup.select_one('.player-header .ge-text-light')
        return region_elem.text.strip() if region_elem else 'Unknown'
    
    def _extract_career_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract career statistics."""
        stats = {}
        stat_cards = soup.select('.player-stats-block')
        
        for card in stat_cards:
            label = card.select_one('.player-stats-block-title')
            value = card.select_one('.player-stats-block-value')
            
            if label and value:
                key = label.text.strip().lower().replace(' ', '_')
                stats[key] = value.text.strip()
        
        return stats
    
    def _extract_agent_stats(self, soup: BeautifulSoup) -> list:
        """Extract agent-specific statistics."""
        agents = []
        agent_rows = soup.select('.agent-stats-row')
        
        for row in agent_rows:
            agent_name = row.select_one('.agent-name')
            if agent_name:
                agents.append({
                    'agent': agent_name.text.strip(),
                    'playtime': self._extract_agent_stat(row, 'playtime'),
                    'win_rate': self._extract_agent_stat(row, 'win'),
                    'kda': self._extract_agent_stat(row, 'kda'),
                    'acs': self._extract_agent_stat(row, 'acs')
                })
        
        return agents
    
    def _extract_agent_stat(self, row, stat_name: str) -> str:
        """Extract specific agent stat."""
        cells = row.select('td')
        stat_map = {
            'playtime': 1,
            'win': 2,
            'kda': 3,
            'acs': 4
        }
        
        idx = stat_map.get(stat_name)
        if idx is not None and len(cells) > idx:
            return cells[idx].text.strip()
        return ''
    
    async def validate_data(self, data: Dict) -> bool:
        """Validate Valorant match data."""
        required_fields = ['id', 'team_a', 'team_b', 'players']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # Validate player stats
        if len(data['players']) < 2:  # At least 2 players
            return False
        
        # Valorant-specific: validate agents exist
        if 'agents' in data:
            agents = data['agents']
            if not agents.get('team_a') and not agents.get('team_b'):
                # Agents not always available, so this is a soft check
                pass
        
        return True
