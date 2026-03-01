# Data Collection Directory Structure

```
radiantx-static/
├── data/
│   ├── raw/                    # Immutable scraped data
│   │   ├── vlr/               # VLR.gg HTML dumps
│   │   ├── hltv/              # HLTV.org data
│   │   ├── riot/              # Riot Games API responses
│   │   └── liquipedia/        # Liquipedia wiki data
│   ├── processed/             # Cleaned, validated data
│   │   ├── players/           # Player stats JSON
│   │   ├── matches/           # Match records
│   │   ├── teams/             # Team aggregations
│   │   └── timelines/         # Time-series data
│   ├── archive/               # Historical snapshots
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── 2026/
│   ├── competitors/           # Competitor analysis
│   │   ├── vlr-gg/            # VLR.gg feature tracking
│   │   ├── thespike/          # thespike.gg analysis
│   │   ├── rib/               # rib.gg comparison
│   │   └── tracker/           # tracker.gg features
│   └── metrics/               # KPIs and measurements
│       ├── coverage/          # Data completeness
│       ├── accuracy/          # Validation scores
│       ├── latency/           # Update speed
│       └── usage/             # User analytics
├── src/
│   ├── scrapers/              # Data extraction
│   │   ├── vlr-client.js      # VLR.gg scraper
│   │   ├── hltv-client.js     # HLTV client
│   │   └── riot-api.js        # Riot Games API
│   ├── parsers/               # HTML/JSON parsers
│   │   ├── vlr-parser.js      # VLR.gg HTML parser
│   │   ├── match-parser.js    # Match data extractor
│   │   └── player-parser.js   # Player stats parser
│   ├── validators/            # Data quality checks
│   │   ├── schema-validator.js # JSON schema validation
│   │   ├── integrity-check.js  # SHA-256 checksums
│   │   └── anomaly-detector.js # Outlier detection
│   └── analytics/             # Metrics calculation
│       ├── sim-rating.js      # SimRating algorithm
│       ├── rar-score.js       # Role-adjusted rating
│       ├── investment-grade.js # A+ through D grading
│       └── trends.js          # Trend analysis
├── config/
│   ├── sources.json           # Data source configs
│   ├── schema.json            # KCRITR 37-field schema
│   ├── metrics.json           # KPI definitions
│   └── harvest-protocol.json  # Axiom protocol config
└── scripts/
    ├── daily-harvest.sh       # Daily data collection
    ├── weekly-analytics.sh    # Weekly metric recalc
    └── deploy-data.sh         # Deploy to site
```

## Data Sources to Monitor

| Source | Type | Priority | Status |
|--------|------|----------|--------|
| VLR.gg | Web scrape | P0 | Planned |
| HLTV.org | Web scrape | P1 | Planned |
| Riot Games API | Official API | P0 | Planned |
| Liquipedia | Wiki/API | P2 | Planned |
| Tracker.gg | Third-party | P2 | Research |

## Competitors to Analyze

| Competitor | Strengths | Gaps to Exploit |
|------------|-----------|-----------------|
| VLR.gg | Comprehensive, established | Mobile experience, visualization |
| thespike.gg | Clean UI, fast | Limited depth, no custom analytics |
| rib.gg | Advanced stats | Complex, not mobile-friendly |
| tracker.gg | Cross-game | Generic, not Valorant-specific |

## Key Metrics to Track

### Data Quality
- Coverage: % of pro matches captured
- Accuracy: Validation pass rate
- Freshness: Hours since last update
- Completeness: % of 37 fields populated

### User Engagement
- Page views
- Time on site
- Player search frequency
- Chart interactions

### Technical
- Scraper success rate
- API response times
- Build/deploy times
- Error rates
