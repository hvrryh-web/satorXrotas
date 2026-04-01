# Dual-Game Esports Data Collection Architecture

## Concurrent CS + Valorant Data Collection System

---

## 1. Overview

### System Purpose
This architecture enables **concurrent, non-interfering data collection** for Counter-Strike (CS) and Valorant professional esports data. The system is designed to handle high-volume, real-time data extraction from multiple sources while maintaining data integrity and preventing cross-contamination between games.

### Key Challenge: Preventing Overlap and Interference
When collecting data for two major esports titles simultaneously, several conflicts can arise:

| Conflict Type | Description | Risk Level |
|--------------|-------------|------------|
| **Data Contamination** | CS data mixed with Valorant records | Critical |
| **Resource Starvation** | One game monopolizing extraction agents | High |
| **Rate Limit Exhaustion** | Shared API limits hit by single game | High |
| **Database Lock Contention** | Concurrent writes causing deadlocks | Medium |
| **Job Duplication** | Same match extracted multiple times | Medium |
| **Schema Conflicts** | Shared tables with incompatible fields | Medium |

### Solution Approach: Partitioned Architecture with Central Coordination

```
┌─────────────────────────────────────────────────────────────┐
│                  CENTRAL JOB COORDINATOR                     │
│         (Single source of truth for all scheduling)          │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
        ┌──────▼──────┐                ┌──────▼──────┐
        │   CS QUEUE  │                │ VALORANT    │
        │             │                │ QUEUE       │
        └──────┬──────┘                └──────┬──────┘
               │                              │
        ┌──────▼──────┐                ┌──────▼──────┐
        │ CS AGENTS   │                │ VALORANT    │
        │ (Specialized)│               │ AGENTS      │
        └──────┬──────┘                └──────┬──────┘
               │                              │
        ┌──────▼──────┐                ┌──────▼──────┐
        │  CS DATA    │                │  VALORANT   │
        │  PARTITION  │                │  PARTITION  │
        └─────────────┘                └─────────────┘
```

**Core Principles:**
1. **Physical Partitioning**: Separate storage, queues, and database schemas per game
2. **Logical Coordination**: Central coordinator manages cross-cutting concerns
3. **Agent Specialization**: Agents declare game capabilities; only assigned compatible jobs
4. **Source Rate Limiting**: Per-source token buckets prevent API exhaustion
5. **Conflict Detection**: Write-ahead checks prevent duplicate processing

---

## 2. Data Partitioning Strategy

### 2.1 Game Partitioning

#### Raw Data Partitioning (File System)
```
/data/esports/
├── raw/
│   ├── cs/
│   │   ├── hltv/
│   │   │   ├── matches/
│   │   │   ├── players/
│   │   │   └── teams/
│   │   ├── liquipedia/
│   │   └── eslc/
│   └── valorant/
│       ├── vlr/
│       │   ├── matches/
│       │   ├── players/
│       │   └── teams/
│       ├── liquipedia/
│       └── rib/
├── processed/
│   ├── cs/
│   └── valorant/
└── archive/
    ├── cs/
    └── valorant/
```

#### Database Partitioning

**Game-Specific Tables (Isolated):**

| CS Tables | Valorant Tables | Purpose |
|-----------|-----------------|---------|
| `cs_matches` | `val_matches` | Match results and metadata |
| `cs_match_details` | `val_match_details` | Round-level data |
| `cs_players` | `val_players` | Player profiles |
| `cs_player_stats` | `val_player_stats` | Performance statistics |
| `cs_teams` | `val_teams` | Team information |
| `cs_team_rosters` | `val_team_rosters` | Active/inactive rosters |
| `cs_maps` | `val_maps` | Map pool and statistics |
| `cs_weapons` | `val_agents` | Game-specific entities |
| `cs_economy_logs` | `val_ability_usage` | Game-specific mechanics |

**Shared Tables (With game_type Column):**

```sql
-- Tournaments are cross-game but partitioned by game_type
CREATE TABLE tournaments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_type VARCHAR(10) NOT NULL CHECK (game_type IN ('cs', 'valorant')),
    name VARCHAR(200) NOT NULL,
    tier SMALLINT, -- S-Tier=1, A-Tier=2, etc.
    region VARCHAR(20),
    start_date DATE,
    end_date DATE,
    prize_pool_usd INTEGER,
    UNIQUE(name, game_type, start_date) -- Prevent duplicates across games
);

CREATE INDEX idx_tournaments_game ON tournaments(game_type);

-- Leagues/Competitions
CREATE TABLE leagues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_type VARCHAR(10) NOT NULL,
    name VARCHAR(200) NOT NULL,
    organizer VARCHAR(100),
    region VARCHAR(20),
    UNIQUE(name, game_type)
);

-- Sources are shared but tracked per game
CREATE TABLE data_sources (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500),
    supports_cs BOOLEAN DEFAULT FALSE,
    supports_valorant BOOLEAN DEFAULT FALSE,
    rate_limit_rpm INTEGER, -- requests per minute
    reliability_score DECIMAL(3,2)
);
```

### 2.2 Time Partitioning (Epochs)

Both games follow a three-epoch extraction model:

```
┌──────────────────────────────────────────────────────────────┐
│                     EPOCH I: HISTORIC                        │
│  (Lower Confidence - Bulk Backfill)                          │
│  • Matches > 2 years old                                     │
│  • Limited data availability                                 │
│  • Higher tolerance for missing fields                       │
│  • Lower extraction frequency                                │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    EPOCH II: MATURE                          │
│  (Full Fidelity - Standard Processing)                       │
│  • Matches 3 months to 2 years old                           │
│  • Complete data expected                                    │
│  • Cross-validation with multiple sources                    │
│  • Standard extraction frequency                             │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                   EPOCH III: CURRENT                         │
│  (Real-time - Incremental Updates)                           │
│  • Active tournaments and recent matches                     │
│  • High-frequency polling (5-15 minute intervals)            │
│  • Immediate processing pipeline                             │
│  • Alert on data gaps                                        │
└──────────────────────────────────────────────────────────────┘
```

**Epoch Configuration:**

```typescript
interface EpochConfig {
  epoch: 1 | 2 | 3;
  name: string;
  ageThresholdDays: { min: number; max: number | null };
  extractionIntervalMinutes: number;
  priority: number;
  validationLevel: 'lenient' | 'standard' | 'strict';
  retentionDays: number;
}

const EPOCH_CONFIGS: Record<number, EpochConfig> = {
  1: {
    epoch: 1,
    name: 'historic',
    ageThresholdDays: { min: 730, max: null }, // > 2 years
    extractionIntervalMinutes: 1440, // Daily
    priority: 1,
    validationLevel: 'lenient',
    retentionDays: 90
  },
  2: {
    epoch: 2,
    name: 'mature',
    ageThresholdDays: { min: 90, max: 730 }, // 3 months to 2 years
    extractionIntervalMinutes: 360, // Every 6 hours
    priority: 3,
    validationLevel: 'standard',
    retentionDays: 365
  },
  3: {
    epoch: 3,
    name: 'current',
    ageThresholdDays: { min: 0, max: 90 }, // < 3 months
    extractionIntervalMinutes: 5, // Every 5 minutes
    priority: 5,
    validationLevel: 'strict',
    retentionDays: 730
  }
};
```

### 2.3 Geographic Partitioning

```
┌─────────────────────────────────────────────────────────────┐
│                    GLOBAL REGIONS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │  AMERICAS   │  │    EMEA     │  │    APAC     │        │
│   │             │  │             │  │             │        │
│   │ • North Am  │  │ • Europe    │  │ • East Asia │        │
│   │ • Brazil    │  │ • CIS       │  │ • SEA       │        │
│   │ • LATAM     │  │ • MENA      │  │ • Oceania   │        │
│   │             │  │ • Africa    │  │             │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│   ┌─────────────────────────────────────────────────┐      │
│   │              CHINA (Valorant Only)               │      │
│   │   • Separate circuit due to publishing rights    │      │
│   │   • Different API endpoints (if available)       │      │
│   └─────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Region-Specific Considerations:**

| Region | CS Priority Sources | Valorant Priority Sources | Notes |
|--------|---------------------|---------------------------|-------|
| Americas | HLTV, ESL | VLR, RIB | NA has most tier-1 events |
| EMEA | HLTV, ESL | VLR, Liquipedia | Highest match volume |
| APAC | HLTV, 5EWin | VLR, Liquipedia | Fragmented ecosystem |
| China | 5EWin, HLTV | VLR (limited) | Separate tournament structure |

---

## 3. Central Job Coordinator Architecture

### 3.1 Coordinator Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                 CENTRAL JOB COORDINATOR                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ 1. JOB QUEUE    │    │ 2. AGENT        │                │
│  │    MANAGEMENT   │    │    ASSIGNMENT   │                │
│  │                 │    │                 │                │
│  │ • Priority sort │    │ • Capability    │                │
│  │ • Dependency    │    │   matching      │                │
│  │   resolution    │    │ • Load balancing│                │
│  │ • Queue depth   │    │ • Health checks │                │
│  │   monitoring    │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ 3. CONFLICT     │    │ 4. RATE LIMIT   │                │
│  │    DETECTION    │    │    MANAGEMENT   │                │
│  │                 │    │                 │                │
│  │ • Duplicate     │    │ • Token bucket  │                │
│  │   detection     │    │   per source    │                │
│  │ • Deduplication │    │ • Cross-game    │                │
│  │ • Drift detect  │    │   fair sharing  │                │
│  │                 │    │ • Burst handling│                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ 5. PROGRESS     │    │ 6. ERROR HANDLING│               │
│  │    TRACKING     │    │    & RETRY      │                │
│  │                 │    │                 │                │
│  │ • Real-time     │    │ • Exponential   │                │
│  │   dashboards    │    │   backoff       │                │
│  │ • Game-level    │    │ • Dead letter   │                │
│  │   metrics       │    │   queues        │                │
│  │ • SLA alerts    │    │ • Circuit       │                │
│  │                 │    │   breakers      │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Job Types

```typescript
// Enums for type safety
enum GameType {
  CS = 'cs',
  VALORANT = 'valorant'
}

enum DataSource {
  HLTV = 'hltv',
  VLR = 'vlr',
  LIQUIPEDIA = 'liquipedia',
  ESL = 'esl',
  RIB = 'rib',
  FIVE_E_WIN = '5ewin'
}

enum JobType {
  MATCH_LIST = 'match_list',           // Discover matches in date range
  MATCH_DETAIL = 'match_detail',       // Full match data + stats
  PLAYER_STATS = 'player_stats',       // Player performance data
  TEAM_ROSTER = 'team_roster',         // Current team lineups
  TOURNAMENT_INFO = 'tournament_info', // Tournament metadata
  RANKINGS = 'rankings',               // Team/player rankings
  LIVE_MATCH = 'live_match'            // Real-time score updates
}

enum JobStatus {
  PENDING = 'pending',
  ASSIGNED = 'assigned',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  RETRYING = 'retrying'
}

// Main Job Interface
interface ExtractionJob {
  // Identity
  id: string;                          // UUID v4
  game: GameType;
  source: DataSource;
  jobType: JobType;
  
  // Scheduling
  priority: number;                    // 1-10, higher = more urgent
  epoch: 1 | 2 | 3;
  region: string;                      // americas, emea, apac, china
  dateRange: {
    start: Date;
    end: Date;
  };
  
  // Status tracking
  status: JobStatus;
  assignedAgent: string | null;
  
  // Timestamps
  createdAt: Date;
  assignedAt: Date | null;
  startedAt: Date | null;
  completedAt: Date | null;
  
  // Retry handling
  retryCount: number;
  maxRetries: number;
  lastError: string | null;
  
  // Dependencies
  dependencies: string[];              // Job IDs that must complete first
  
  // Game-specific metadata
  metadata: {
    matchId?: string;
    tournamentId?: string;
    teamIds?: string[];
    playerIds?: string[];
    pageNumber?: number;
    customParams?: Record<string, unknown>;
  };
  
  // Processing results
  result?: {
    recordsExtracted: number;
    checksum: string;
    storagePath: string;
    processingTimeMs: number;
  };
}

// Job creation helper with defaults
function createJob(params: Partial<ExtractionJob>): ExtractionJob {
  return {
    id: crypto.randomUUID(),
    status: JobStatus.PENDING,
    assignedAgent: null,
    priority: 5,
    epoch: 2,
    retryCount: 0,
    maxRetries: 3,
    lastError: null,
    dependencies: [],
    metadata: {},
    assignedAt: null,
    startedAt: null,
    completedAt: null,
    ...params
  } as ExtractionJob;
}
```

---

## 4. Database Schema for Coordination

### 4.1 Job Queue Tables

```sql
-- ============================================
-- CORE JOB QUEUE
-- ============================================

CREATE TABLE extraction_jobs (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_type VARCHAR(10) NOT NULL CHECK (game_type IN ('cs', 'valorant')),
    source VARCHAR(50) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    
    -- Scheduling
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    epoch SMALLINT NOT NULL CHECK (epoch IN (1, 2, 3)),
    region VARCHAR(20) NOT NULL,
    date_start DATE,
    date_end DATE,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'assigned', 'processing', 'completed', 'failed', 'cancelled', 'retrying')),
    
    -- Assignment
    assigned_agent VARCHAR(100),
    assigned_at TIMESTAMPTZ,
    
    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Retry handling
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    
    -- Results
    records_extracted INTEGER,
    checksum VARCHAR(64),
    storage_path VARCHAR(500),
    processing_time_ms INTEGER,
    
    -- Flexible metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_date_range CHECK (date_start <= date_end OR date_start IS NULL OR date_end IS NULL)
);

-- Indexes for common queries
CREATE INDEX idx_jobs_status ON extraction_jobs(status);
CREATE INDEX idx_jobs_game_status ON extraction_jobs(game_type, status);
CREATE INDEX idx_jobs_priority ON extraction_jobs(priority DESC, created_at ASC) WHERE status = 'pending';
CREATE INDEX idx_jobs_agent ON extraction_jobs(assigned_agent) WHERE status IN ('assigned', 'processing');
CREATE INDEX idx_jobs_source ON extraction_jobs(source, game_type);
CREATE INDEX idx_jobs_epoch ON extraction_jobs(epoch, game_type);
CREATE INDEX idx_jobs_metadata ON extraction_jobs USING GIN(metadata);

-- ============================================
-- JOB DEPENDENCIES
-- ============================================

CREATE TABLE job_dependencies (
    job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    depends_on_job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (job_id, depends_on_job_id),
    -- Prevent self-dependency
    CONSTRAINT no_self_dep CHECK (job_id != depends_on_job_id)
);

CREATE INDEX idx_deps_job ON job_dependencies(job_id);
CREATE INDEX idx_deps_depends_on ON job_dependencies(depends_on_job_id);

-- ============================================
-- AGENT REGISTRY
-- ============================================

CREATE TABLE extraction_agents (
    id VARCHAR(100) PRIMARY KEY,
    
    -- Capabilities (agent declares what it can do)
    game_specialization VARCHAR(10)[] NOT NULL, -- ['cs'], ['valorant'], or ['cs', 'valorant']
    source_capabilities VARCHAR(50)[] NOT NULL,
    region_capabilities VARCHAR(20)[],
    max_concurrent_jobs INTEGER NOT NULL DEFAULT 1,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'idle' 
        CHECK (status IN ('idle', 'busy', 'paused', 'offline', 'error')),
    current_job_ids UUID[], -- Can handle multiple jobs if configured
    
    -- Health
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version VARCHAR(20), -- Agent software version
    ip_address INET,
    
    -- Rate limiting (per-agent limits)
    rate_limit_remaining INTEGER,
    rate_limit_resets_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_status ON extraction_agents(status);
CREATE INDEX idx_agents_heartbeat ON extraction_agents(last_heartbeat);

-- ============================================
-- SOURCE RATE LIMITS
-- ============================================

CREATE TABLE source_rate_limits (
    source VARCHAR(50) PRIMARY KEY,
    
    -- Limits
    requests_per_minute INTEGER NOT NULL,
    requests_per_hour INTEGER NOT NULL,
    requests_per_day INTEGER,
    concurrent_requests INTEGER NOT NULL DEFAULT 1,
    
    -- Current counters
    current_minute_count INTEGER NOT NULL DEFAULT 0,
    current_hour_count INTEGER NOT NULL DEFAULT 0,
    current_day_count INTEGER NOT NULL DEFAULT 0,
    
    -- Reset tracking
    minute_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hour_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    day_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Active connections
    active_connections INTEGER NOT NULL DEFAULT 0,
    
    -- Game-specific limits (fair sharing)
    cs_allocation_percent INTEGER NOT NULL DEFAULT 50 CHECK (cs_allocation_percent BETWEEN 0 AND 100),
    valorant_allocation_percent INTEGER GENERATED ALWAYS AS (100 - cs_allocation_percent) STORED,
    
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- RAW EXTRACTIONS (Deduplication)
-- ============================================

CREATE TABLE raw_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES extraction_jobs(id),
    
    -- Identification
    game_type VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(200) NOT NULL, -- ID from source system
    
    -- Content
    data JSONB NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA-256 of normalized data
    
    -- Storage
    raw_file_path VARCHAR(500),
    file_size_bytes INTEGER,
    
    -- Metadata
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_version INTEGER NOT NULL DEFAULT 1,
    previous_version_id UUID REFERENCES raw_extractions(id),
    
    -- Unique constraint for deduplication
    UNIQUE(game_type, source, source_id, checksum)
);

CREATE INDEX idx_raw_game_source ON raw_extractions(game_type, source);
CREATE INDEX idx_raw_source_id ON raw_extractions(source_id);
CREATE INDEX idx_raw_checksum ON raw_extractions(checksum);

-- ============================================
-- CONFLICT LOG
-- ============================================

CREATE TABLE extraction_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_extraction_id UUID NOT NULL REFERENCES raw_extractions(id),
    
    conflict_type VARCHAR(50) NOT NULL, -- 'checksum_mismatch', 'duplicate_job', 'version_drift'
    description TEXT NOT NULL,
    
    previous_checksum VARCHAR(64),
    new_checksum VARCHAR(64),
    
    resolution VARCHAR(20), -- 'accepted', 'rejected', 'manual_review'
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conflicts_unresolved ON extraction_conflicts(resolution) WHERE resolution IS NULL;

-- ============================================
-- METRICS & MONITORING
-- ============================================

CREATE TABLE job_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_type VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    epoch SMALLINT,
    region VARCHAR(20),
    
    -- Counts
    jobs_queued INTEGER NOT NULL DEFAULT 0,
    jobs_completed INTEGER NOT NULL DEFAULT 0,
    jobs_failed INTEGER NOT NULL DEFAULT 0,
    jobs_deduplicated INTEGER NOT NULL DEFAULT 0,
    
    -- Timing
    avg_processing_time_ms INTEGER,
    total_processing_time_ms BIGINT,
    
    -- Records
    records_extracted BIGINT,
    
    -- Time window
    window_start TIMESTAMPTZ NOT NULL,
    window_duration_minutes INTEGER NOT NULL DEFAULT 5,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metrics_game_time ON job_metrics(game_type, window_start DESC);
CREATE INDEX idx_metrics_source ON job_metrics(source, window_start DESC);
```

### 4.2 Helper Functions

```sql
-- Check if job dependencies are satisfied
CREATE OR REPLACE FUNCTION dependencies_completed(job_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 FROM job_dependencies jd
        JOIN extraction_jobs ej ON jd.depends_on_job_id = ej.id
        WHERE jd.job_id = job_uuid
        AND ej.status NOT IN ('completed')
    );
END;
$$ LANGUAGE plpgsql;

-- Update rate limit counters
CREATE OR REPLACE FUNCTION check_rate_limit(src VARCHAR(50), game VARCHAR(10))
RETURNS BOOLEAN AS $$
DECLARE
    limit_row source_rate_limits%ROWTYPE;
    game_allocation INTEGER;
BEGIN
    SELECT * INTO limit_row FROM source_rate_limits WHERE source = src;
    
    IF NOT FOUND THEN
        RETURN TRUE; -- No limit configured
    END IF;
    
    -- Reset counters if needed
    IF NOW() > limit_row.minute_reset_at + INTERVAL '1 minute' THEN
        UPDATE source_rate_limits 
        SET current_minute_count = 0, minute_reset_at = NOW()
        WHERE source = src;
        limit_row.current_minute_count := 0;
    END IF;
    
    IF NOW() > limit_row.hour_reset_at + INTERVAL '1 hour' THEN
        UPDATE source_rate_limits 
        SET current_hour_count = 0, hour_reset_at = NOW()
        WHERE source = src;
        limit_row.current_hour_count := 0;
    END IF;
    
    -- Check game-specific allocation
    game_allocation := CASE 
        WHEN game = 'cs' THEN limit_row.cs_allocation_percent 
        ELSE limit_row.valorant_allocation_percent 
    END;
    
    -- Calculate game-specific limits
    RETURN limit_row.current_minute_count < (limit_row.requests_per_minute * game_allocation / 100)
       AND limit_row.current_hour_count < (limit_row.requests_per_hour * game_allocation / 100)
       AND limit_row.active_connections < limit_row.concurrent_requests;
END;
$$ LANGUAGE plpgsql;

-- Increment rate limit counter
CREATE OR REPLACE FUNCTION increment_rate_limit(src VARCHAR(50))
RETURNS VOID AS $$
BEGIN
    UPDATE source_rate_limits 
    SET current_minute_count = current_minute_count + 1,
        current_hour_count = current_hour_count + 1,
        active_connections = active_connections + 1,
        updated_at = NOW()
    WHERE source = src;
END;
$$ LANGUAGE plpgsql;

-- Release rate limit connection
CREATE OR REPLACE FUNCTION release_rate_limit_connection(src VARCHAR(50))
RETURNS VOID AS $$
BEGIN
    UPDATE source_rate_limits 
    SET active_connections = GREATEST(0, active_connections - 1),
        updated_at = NOW()
    WHERE source = src;
END;
$$ LANGUAGE plpgsql;

-- Find pending jobs eligible for assignment
CREATE OR REPLACE FUNCTION get_assignable_jobs(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    job_id UUID,
    game_type VARCHAR(10),
    source VARCHAR(50),
    job_type VARCHAR(50),
    priority INTEGER,
    region VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ej.id,
        ej.game_type,
        ej.source,
        ej.job_type,
        ej.priority,
        ej.region
    FROM extraction_jobs ej
    WHERE ej.status = 'pending'
      AND dependencies_completed(ej.id)
      AND check_rate_limit(ej.source, ej.game_type)
    ORDER BY ej.priority DESC, ej.created_at ASC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

---

## 5. Conflict Prevention Mechanisms

### 5.1 Job Deduplication

```python
# job_deduplication.py
from datetime import datetime
from typing import Optional
import hashlib
import json

class JobDeduplicator:
    """Prevents duplicate jobs for the same data extraction."""
    
    def __init__(self, db_pool, redis_client):
        self.db = db_pool
        self.redis = redis_client
    
    async def generate_job_fingerprint(
        self,
        game: str,
        source: str,
        job_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        region: Optional[str] = None,
        metadata: dict = None
    ) -> str:
        """Generate unique fingerprint for a job."""
        fingerprint_data = {
            'game': game,
            'source': source,
            'job_type': job_type,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'region': region,
            'metadata_keys': sorted(metadata.keys()) if metadata else []
        }
        return hashlib.sha256(
            json.dumps(fingerprint_data, sort_keys=True).encode()
        ).hexdigest()[:32]
    
    async def check_existing_job(
        self,
        game: str,
        source: str,
        job_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Optional[dict]:
        """Check if an equivalent job already exists."""
        
        # Fast path: Check Redis cache
        fingerprint = await self.generate_job_fingerprint(
            game, source, job_type, start_date, end_date
        )
        cached = await self.redis.get(f"job:fingerprint:{fingerprint}")
        if cached:
            return json.loads(cached)
        
        # Database check with broader criteria
        existing = await self.db.fetchrow(
            """
            SELECT id, status, created_at, assigned_agent
            FROM extraction_jobs 
            WHERE game_type = $1 
              AND source = $2 
              AND job_type = $3 
              AND (
                  (date_start = $4 AND date_end = $5)
                  OR (date_start <= $4 AND date_end >= $5)  -- Overlapping range
              )
              AND status IN ('pending', 'assigned', 'processing', 'completed')
              AND created_at > NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            game, source, job_type, start_date, end_date
        )
        
        if existing:
            # Cache result for 5 minutes
            await self.redis.setex(
                f"job:fingerprint:{fingerprint}",
                300,
                json.dumps(dict(existing))
            )
        
        return existing
    
    async def create_job_if_unique(
        self,
        game: str,
        source: str,
        job_type: str,
        priority: int,
        epoch: int,
        region: str,
        date_range: dict,
        metadata: dict = None
    ) -> Optional[str]:
        """
        Create a job only if no equivalent exists.
        Returns job ID if created, None if duplicate found.
        """
        
        # Check for existing job
        existing = await self.check_existing_job(
            game, source, job_type, 
            date_range.get('start'), 
            date_range.get('end')
        )
        
        if existing:
            status = existing['status']
            
            # If completed recently, skip
            if status == 'completed':
                logger.info(f"Skipping duplicate job - already completed: {existing['id']}")
                return None
            
            # If pending/assigned/processing, return existing ID
            if status in ('pending', 'assigned', 'processing'):
                logger.info(f"Job already in queue: {existing['id']} ({status})")
                return existing['id']
        
        # Acquire distributed lock for creation
        lock_key = f"job:create:{game}:{source}:{job_type}"
        async with self.redis.lock(lock_key, timeout=10):
            # Double-check after acquiring lock
            existing = await self.check_existing_job(
                game, source, job_type,
                date_range.get('start'),
                date_range.get('end')
            )
            
            if existing and existing['status'] in ('pending', 'assigned', 'processing', 'completed'):
                return None
            
            # Create new job
            job_id = await self.db.fetchval(
                """
                INSERT INTO extraction_jobs (
                    game_type, source, job_type, priority, epoch, region,
                    date_start, date_end, status, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending', $9)
                RETURNING id
                """,
                game, source, job_type, priority, epoch, region,
                date_range.get('start'),
                date_range.get('end'),
                json.dumps(metadata or {})
            )
            
            # Cache the fingerprint
            fingerprint = await self.generate_job_fingerprint(
                game, source, job_type,
                date_range.get('start'),
                date_range.get('end')
            )
            await self.redis.setex(
                f"job:fingerprint:{fingerprint}",
                300,
                json.dumps({'id': str(job_id), 'status': 'pending'})
            )
            
            logger.info(f"Created new job: {job_id}")
            return job_id
```

### 5.2 Distributed Locking

```python
# distributed_locking.py
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

class DistributedLockManager:
    """Redis-based distributed locking for critical sections."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get_lock_key(
        self,
        game: str,
        source: str,
        resource_type: str,
        resource_id: str
    ) -> str:
        """Generate standardized lock key."""
        return f"lock:{game}:{source}:{resource_type}:{resource_id}"
    
    @asynccontextmanager
    async def acquire_extraction_lock(
        self,
        game: str,
        source: str,
        resource_type: str,
        resource_id: str,
        timeout_seconds: int = 300,
        blocking_timeout: int = 10
    ):
        """
        Acquire a distributed lock for data extraction.
        
        Usage:
            async with lock_manager.acquire_extraction_lock('cs', 'hltv', 'match', '12345'):
                await extract_match_data()
        """
        lock_key = self.get_lock_key(game, source, resource_type, resource_id)
        lock = self.redis.lock(
            lock_key,
            timeout=timeout_seconds,
            thread_local=False
        )
        
        acquired = await lock.acquire(
            blocking=True,
            blocking_timeout=blocking_timeout
        )
        
        if not acquired:
            raise LockAcquisitionError(f"Could not acquire lock: {lock_key}")
        
        try:
            yield lock
        finally:
            try:
                await lock.release()
            except Exception as e:
                logger.warning(f"Lock release failed (may have expired): {e}")
    
    async def is_locked(
        self,
        game: str,
        source: str,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """Check if a resource is currently locked."""
        lock_key = self.get_lock_key(game, source, resource_type, resource_id)
        return await self.redis.exists(lock_key) > 0
    
    async def extend_lock(
        self,
        lock,
        additional_time: int
    ) -> bool:
        """Extend an existing lock (for long-running operations)."""
        try:
            return await lock.reacquire()
        except Exception:
            return False

class LockAcquisitionError(Exception):
    """Raised when lock cannot be acquired."""
    pass
```

### 5.3 Write-Ahead Conflict Detection

```python
# conflict_detection.py
import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class ConflictType(Enum):
    CHECKSUM_MISMATCH = "checksum_mismatch"
    DUPLICATE_JOB = "duplicate_job"
    VERSION_DRIFT = "version_drift"
    SCHEMA_MISMATCH = "schema_mismatch"

class ConflictDetector:
    """Detects and handles data conflicts before write operations."""
    
    def __init__(self, db_pool):
        self.db = db_pool
    
    def compute_checksum(self, data: Dict[str, Any]) -> str:
        """Compute normalized SHA-256 checksum of data."""
        # Normalize: sort keys, convert dates to ISO format
        normalized = self._normalize_for_checksum(data)
        return hashlib.sha256(
            json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode('utf-8')
        ).hexdigest()
    
    def _normalize_for_checksum(self, obj: Any) -> Any:
        """Recursively normalize data for consistent checksums."""
        if isinstance(obj, dict):
            return {k: self._normalize_for_checksum(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            return [self._normalize_for_checksum(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        else:
            return str(obj)
    
    async def check_for_conflict(
        self,
        game: str,
        source: str,
        source_id: str,
        new_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if writing this data would create a conflict.
        Returns conflict details or None if no conflict.
        """
        new_checksum = self.compute_checksum(new_data)
        
        # Check for existing record
        existing = await self.db.fetchrow(
            """
            SELECT id, checksum, data, extracted_at, content_version
            FROM raw_extractions 
            WHERE game_type = $1 
              AND source = $2 
              AND source_id = $3
            ORDER BY content_version DESC
            LIMIT 1
            """,
            game, source, source_id
        )
        
        if not existing:
            # No existing record - no conflict
            return None
        
        if existing['checksum'] == new_checksum:
            # Exact duplicate - not a conflict, just skip
            return {
                'type': ConflictType.DUPLICATE_JOB,
                'existing_id': existing['id'],
                'action': 'skip',
                'message': 'Identical data already exists'
            }
        
        # Checksum mismatch - content drift detected
        return {
            'type': ConflictType.CHECKSUM_MISMATCH,
            'existing_id': existing['id'],
            'previous_checksum': existing['checksum'],
            'new_checksum': new_checksum,
            'previous_version': existing['content_version'],
            'previous_extracted_at': existing['extracted_at'],
            'action': 'requires_resolution',
            'message': 'Data has changed since last extraction'
        }
    
    async def resolve_conflict(
        self,
        conflict: Dict[str, Any],
        new_data: Dict[str, Any],
        job_id: str,
        resolution_strategy: str = 'auto'
    ) -> str:
        """
        Resolve a detected conflict.
        
        Strategies:
        - 'auto': Accept newer data if significantly different
        - 'manual': Queue for human review
        - 'keep_existing': Reject new data
        - 'force_update': Always accept new data
        """
        
        if resolution_strategy == 'keep_existing':
            await self._log_conflict(conflict, job_id, 'rejected')
            return conflict['existing_id']
        
        if resolution_strategy == 'manual':
            await self._queue_for_manual_review(conflict, new_data, job_id)
            return conflict['existing_id']
        
        if resolution_strategy == 'force_update':
            return await self._create_new_version(conflict, new_data, job_id)
        
        # Auto resolution: Check if changes are significant
        if await self._is_significant_change(conflict, new_data):
            return await self._create_new_version(conflict, new_data, job_id)
        else:
            # Minor change, just update metadata
            await self._update_metadata_only(conflict, job_id)
            return conflict['existing_id']
    
    async def _is_significant_change(
        self,
        conflict: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> bool:
        """Determine if changes are significant enough to warrant a new version."""
        existing = await self.db.fetchrow(
            "SELECT data FROM raw_extractions WHERE id = $1",
            conflict['existing_id']
        )
        
        if not existing:
            return True
        
        old_data = existing['data']
        
        # Compare key fields that indicate significant changes
        significant_fields = [
            'score', 'winner', 'result', 'status', 
            'maps', 'players', 'statistics'
        ]
        
        for field in significant_fields:
            if field in new_data or field in old_data:
                old_val = old_data.get(field)
                new_val = new_data.get(field)
                if old_val != new_val:
                    return True
        
        return False
    
    async def _create_new_version(
        self,
        conflict: Dict[str, Any],
        new_data: Dict[str, Any],
        job_id: str
    ) -> str:
        """Create a new version of the extraction."""
        new_checksum = conflict['new_checksum']
        previous_version = conflict.get('previous_version', 1)
        
        new_id = await self.db.fetchval(
            """
            INSERT INTO raw_extractions (
                job_id, game_type, source, source_id,
                data, checksum, previous_version_id, content_version
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            job_id,
            new_data.get('_game_type'),
            new_data.get('_source'),
            new_data.get('_source_id'),
            json.dumps(new_data),
            new_checksum,
            conflict['existing_id'],
            previous_version + 1
        )
        
        await self._log_conflict(conflict, job_id, 'accepted', str(new_id))
        return new_id
    
    async def _log_conflict(
        self,
        conflict: Dict[str, Any],
        job_id: str,
        resolution: str,
        new_id: Optional[str] = None
    ):
        """Log conflict to database."""
        await self.db.execute(
            """
            INSERT INTO extraction_conflicts (
                raw_extraction_id, conflict_type, description,
                previous_checksum, new_checksum, resolution, resolved_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
            conflict['existing_id'],
            conflict['type'].value,
            conflict['message'],
            conflict.get('previous_checksum'),
            conflict.get('new_checksum'),
            resolution
        )
```

---

## 6. Async Agent Worker Model

### 6.1 Agent Types

```python
# agent_types.py
from enum import Enum, auto
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

class AgentType(Enum):
    """Specialized agent types for different extraction tasks."""
    SCOUT = auto()       # Discovers new matches/events
    DETAIL = auto()      # Fetches detailed match data
    PLAYER = auto()      # Collects player statistics
    TEAM = auto()        # Collects team/roster information
    VALIDATOR = auto()   # Cross-references and validates
    LIVE = auto()        # Real-time match updates

@dataclass
class AgentCapabilities:
    """Defines what an agent can do."""
    games: List[str]                    # ['cs'], ['valorant'], or both
    sources: List[str]                  # ['hltv', 'vlr', ...]
    agent_types: List[AgentType]        # What jobs it can handle
    regions: List[str]                  # Geographic coverage
    max_concurrent_jobs: int = 1
    supports_live: bool = False         # Can handle live match updates

@dataclass
class AgentState:
    """Current state of an agent."""
    id: str
    status: str                         # idle, busy, paused, offline, error
    current_jobs: List[str]
    last_heartbeat: datetime
    version: str
    ip_address: Optional[str]
    rate_limit_remaining: Dict[str, int]  # Per-source remaining quota

class ScoutAgent:
    """
    Scout Agent: Discovers new content to extract.
    
    Responsibilities:
    - Poll source APIs for new matches
    - Discover tournaments and events
    - Identify upcoming matches for pre-fetching
    - Generate MATCH_LIST jobs
    """
    
    AGENT_TYPE = AgentType.SCOUT
    
    async def discover_matches(
        self,
        source: str,
        date_range: Dict[str, datetime],
        region: str
    ) -> List[Dict[str, Any]]:
        """Discover matches in the specified range."""
        pass
    
    async def discover_tournaments(
        self,
        source: str,
        game: str
    ) -> List[Dict[str, Any]]:
        """Discover active and upcoming tournaments."""
        pass

class DetailAgent:
    """
    Detail Agent: Fetches comprehensive match data.
    
    Responsibilities:
    - Extract full match statistics
    - Download demos/replays when available
    - Parse round-level data
    - Store to raw partition
    """
    
    AGENT_TYPE = AgentType.DETAIL
    
    async def extract_match_detail(
        self,
        source: str,
        source_match_id: str,
        game: str
    ) -> Dict[str, Any]:
        """Extract detailed match information."""
        pass
    
    async def download_demo(
        self,
        demo_url: str,
        storage_path: str
    ) -> str:
        """Download match demo file."""
        pass

class PlayerAgent:
    """
    Player Agent: Collects player-specific data.
    
    Responsibilities:
    - Extract player profiles
    - Collect career statistics
    - Track team history
    - Monitor rank changes
    """
    
    AGENT_TYPE = AgentType.PLAYER
    
    async def extract_player_profile(
        self,
        source: str,
        player_id: str,
        game: str
    ) -> Dict[str, Any]:
        """Extract player profile and stats."""
        pass
    
    async def extract_player_matches(
        self,
        source: str,
        player_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Extract recent matches for a player."""
        pass

class ValidationAgent:
    """
    Validation Agent: Ensures data quality and consistency.
    
    Responsibilities:
    - Cross-reference multiple sources
    - Detect anomalies
    - Fill missing data
    - Flag suspicious results
    """
    
    AGENT_TYPE = AgentType.VALIDATOR
    
    async def validate_match(
        self,
        game: str,
        match_id: str,
        sources: List[str]
    ) -> Dict[str, Any]:
        """Validate match data across sources."""
        pass
    
    async def detect_anomalies(
        self,
        game: str,
        time_window: Dict[str, datetime]
    ) -> List[Dict[str, Any]]:
        """Detect anomalous data patterns."""
        pass
```

### 6.2 Agent Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT LIFECYCLE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐                │
│    │  START  │────▶│ REGISTER│────▶│ HEARTBEAT│               │
│    │         │     │         │     │          │                │
│    └─────────┘     └────┬────┘     └────┬─────┘                │
│                         │               │                       │
│                         ▼               │                       │
│    ┌─────────────────────────────────┐  │                       │
│    │      AGENT REGISTRY UPDATE      │  │                       │
│    │ • capabilities recorded         │  │                       │
│    │ • assigned unique ID            │  │                       │
│    │ • initial status: idle          │  │                       │
│    └─────────────────────────────────┘  │                       │
│                                         │                       │
│                         ┌───────────────┘                       │
│                         ▼                                       │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐                │
│    │ REPORT  │◀────│ PROCESS │◀────│JOB REQ  │                │
│    │         │     │         │     │         │                │
│    └────┬────┘     └─────────┘     └─────────┘                │
│         │                                                       │
│         └──────────────────┬──────────────────┐                │
│                            ▼                  │                │
│    ┌────────────────────────────────────────┐ │                │
│    │           JOB COMPLETION               │ │                │
│    │ • results stored                       │ │                │
│    │ • metrics recorded                     │─┘                │
│    │ • status returned to idle              │                   │
│    └────────────────────────────────────────┘                   │
│                            │                                    │
│                            ▼                                    │
│         ┌────────────────────────────────────┐                 │
│         │       SHUTDOWN / FAILURE           │                 │
│         │ • cleanup current jobs             │                 │
│         │ • reassign pending work            │                 │
│         │ • archive logs                     │                 │
│         └────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Agent Isolation

```python
# agent_isolation.py
from contextlib import asynccontextmanager
import asyncpg

class AgentIsolationManager:
    """
    Ensures agents operate in isolated contexts.
    Prevents cross-game contamination and resource conflicts.
    """
    
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.agent_pools: Dict[str, asyncpg.Pool] = {}
    
    @asynccontextmanager
    async def get_agent_connection(self, agent_id: str, game: str):
        """
        Get isolated database connection for an agent.
        Each agent gets its own connection pool.
        """
        pool_key = f"{agent_id}:{game}"
        
        if pool_key not in self.agent_pools:
            # Create dedicated pool for this agent-game combination
            self.agent_pools[pool_key] = await asyncpg.create_pool(
                **self.db_config,
                min_size=1,
                max_size=3,
                command_timeout=60,
                server_settings={
                    'application_name': f'agent:{agent_id}:{game}'
                }
            )
        
        pool = self.agent_pools[pool_key]
        async with pool.acquire() as conn:
            # Set search path to game-specific schema
            await conn.execute(f"SET search_path TO {game}, public")
            yield conn
    
    async def enforce_game_isolation(
        self,
        agent_id: str,
        allowed_games: List[str]
    ):
        """
        Enforce that agent only accesses its declared game partitions.
        Called during job assignment validation.
        """
        # Verify agent capabilities match requested game
        agent = await self.get_agent_info(agent_id)
        
        for game in allowed_games:
            if game not in agent['game_specialization']:
                raise GameAccessDeniedError(
                    f"Agent {agent_id} not authorized for game: {game}"
                )
    
    async def isolate_storage_path(
        self,
        game: str,
        source: str,
        job_type: str
    ) -> str:
        """Generate isolated storage path for raw data."""
        from datetime import datetime
        
        now = datetime.utcnow()
        return (
            f"/data/esports/raw/{game}/{source}/{job_type}/"
            f"{now.year}/{now.month:02d}/{now.day:02d}/"
        )
    
    async def cleanup_agent_resources(self, agent_id: str):
        """Cleanup resources when agent shuts down."""
        # Close agent-specific connection pools
        for key in list(self.agent_pools.keys()):
            if key.startswith(f"{agent_id}:"):
                pool = self.agent_pools.pop(key)
                await pool.close()
        
        # Release any held locks
        # (Handled by Redis key expiration, but we can force cleanup)

class GameAccessDeniedError(Exception):
    """Raised when agent attempts to access unauthorized game."""
    pass
```

---

## 7. Queue Distribution Algorithm

### 7.1 Core Distribution Logic

```python
# queue_distribution.py
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class JobAssignment:
    job_id: str
    agent_id: str
    game: str
    source: str
    expected_duration_ms: int

class QueueDistributor:
    """
    Distributes pending jobs to available agents.
    Optimizes for fairness, priority, and resource utilization.
    """
    
    def __init__(self, db_pool, redis_client):
        self.db = db_pool
        self.redis = redis_client
        
        # Distribution configuration
        self.max_jobs_per_agent = 5
        self.assignment_batch_size = 20
        self.fair_share_window_hours = 24
    
    async def distribute_jobs(self) -> List[JobAssignment]:
        """
        Main distribution routine.
        Returns list of (job_id, agent_id) assignments.
        """
        async with self.db.transaction():
            # 1. Get pending jobs with resolved dependencies
            pending_jobs = await self._get_pending_jobs()
            
            if not pending_jobs:
                return []
            
            # 2. Get available agents
            available_agents = await self._get_available_agents()
            
            if not available_agents:
                logger.warning("No available agents for job distribution")
                return []
            
            # 3. Match jobs to agents
            assignments = await self._match_jobs_to_agents(
                pending_jobs, 
                available_agents
            )
            
            # 4. Apply fairness adjustments
            fair_assignments = await self._apply_fairness_constraints(
                assignments
            )
            
            # 5. Persist assignments
            await self._persist_assignments(fair_assignments)
            
            return fair_assignments
    
    async def _get_pending_jobs(self) -> List[Dict]:
        """Get pending jobs with resolved dependencies, ordered by priority."""
        return await self.db.fetch(
            """
            SELECT 
                ej.id,
                ej.game_type,
                ej.source,
                ej.job_type,
                ej.priority,
                ej.epoch,
                ej.region,
                ej.metadata
            FROM extraction_jobs ej
            WHERE ej.status = 'pending'
              AND dependencies_completed(ej.id)
              AND check_rate_limit(ej.source, ej.game_type)
            ORDER BY 
                ej.priority DESC,
                CASE ej.epoch
                    WHEN 3 THEN 1  -- Current first
                    WHEN 2 THEN 2  -- Mature second
                    WHEN 1 THEN 3  -- Historic last
                END,
                ej.created_at ASC
            LIMIT $1
            """,
            self.assignment_batch_size
        )
    
    async def _get_available_agents(self) -> List[Dict]:
        """Get agents ready to accept new jobs."""
        return await self.db.fetch(
            """
            SELECT 
                ea.id,
                ea.game_specialization,
                ea.source_capabilities,
                ea.region_capabilities,
                ea.max_concurrent_jobs,
                ea.rate_limit_remaining,
                COALESCE(
                    (SELECT COUNT(*) 
                     FROM extraction_jobs ej 
                     WHERE ej.assigned_agent = ea.id 
                       AND ej.status IN ('assigned', 'processing')),
                    0
                ) as current_load
            FROM extraction_agents ea
            WHERE ea.status = 'idle'
              AND ea.last_heartbeat > NOW() - INTERVAL '2 minutes'
            ORDER BY current_load ASC
            """
        )
    
    async def _match_jobs_to_agents(
        self,
        jobs: List[Dict],
        agents: List[Dict]
    ) -> List[JobAssignment]:
        """Match jobs to suitable agents based on capabilities."""
        assignments = []
        agent_load = {a['id']: a['current_load'] for a in agents}
        
        for job in jobs:
            suitable_agents = self._filter_suitable_agents(job, agents)
            
            if not suitable_agents:
                logger.debug(f"No suitable agent for job {job['id']}")
                continue
            
            # Score agents based on multiple factors
            scored_agents = []
            for agent in suitable_agents:
                score = self._score_agent_for_job(agent, job, agent_load)
                scored_agents.append((score, agent))
            
            # Pick best agent
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            best_agent = scored_agents[0][1]
            
            assignment = JobAssignment(
                job_id=str(job['id']),
                agent_id=best_agent['id'],
                game=job['game_type'],
                source=job['source'],
                expected_duration_ms=self._estimate_duration(job)
            )
            
            assignments.append(assignment)
            agent_load[best_agent['id']] += 1
            
            # Remove agent from pool if at capacity
            if agent_load[best_agent['id']] >= best_agent['max_concurrent_jobs']:
                agents = [a for a in agents if a['id'] != best_agent['id']]
        
        return assignments
    
    def _filter_suitable_agents(
        self,
        job: Dict,
        agents: List[Dict]
    ) -> List[Dict]:
        """Filter agents that can handle this job."""
        return [
            a for a in agents
            if job['game_type'] in a['game_specialization']
            and job['source'] in a['source_capabilities']
            and (not a['region_capabilities'] or 
                 job['region'] in a['region_capabilities'])
            and a['current_load'] < a['max_concurrent_jobs']
        ]
    
    def _score_agent_for_job(
        self,
        agent: Dict,
        job: Dict,
        agent_load: Dict[str, int]
    ) -> float:
        """Score an agent's suitability for a job (higher = better)."""
        score = 0.0
        
        # Prefer less loaded agents (load balancing)
        current_load = agent_load.get(agent['id'], 0)
        max_load = agent['max_concurrent_jobs']
        load_ratio = current_load / max_load if max_load > 0 else 1
        score += (1 - load_ratio) * 40  # 40% weight
        
        # Prefer agents with game specialization (single-game > multi-game)
        if len(agent['game_specialization']) == 1:
            score += 20  # 20% weight for specialists
        
        # Prefer agents with source expertise
        source_count = len(agent['source_capabilities'])
        if source_count <= 2:  # Focused agent
            score += 15
        
        # Prefer agents with lower recent job count (fairness)
        recent_jobs = self._get_recent_job_count_sync(agent['id'])
        score += max(0, 25 - recent_jobs)  # 25% weight, decreases with load
        
        return score
    
    def _get_recent_job_count_sync(self, agent_id: str) -> int:
        """Get job count for agent in last 24h (cached)."""
        # In production, this would be cached/memoized
        return 0  # Simplified
    
    async def _apply_fairness_constraints(
        self,
        assignments: List[JobAssignment]
    ) -> List[JobAssignment]:
        """
        Ensure fair distribution between games.
        Prevents one game from starving the other.
        """
        # Count assignments per game
        game_counts = {}
        for a in assignments:
            game_counts[a.game] = game_counts.get(a.game, 0) + 1
        
        # Check fairness ratio
        total = len(assignments)
        if total == 0:
            return assignments
        
        cs_ratio = game_counts.get('cs', 0) / total
        val_ratio = game_counts.get('valorant', 0) / total
        
        # If severely imbalanced, adjust
        if cs_ratio > 0.7:
            # Too many CS jobs, defer some to next cycle
            return self._defer_excess_jobs(assignments, 'cs', target_ratio=0.6)
        elif val_ratio > 0.7:
            return self._defer_excess_jobs(assignments, 'valorant', target_ratio=0.6)
        
        return assignments
    
    def _defer_excess_jobs(
        self,
        assignments: List[JobAssignment],
        game: str,
        target_ratio: float
    ) -> List[JobAssignment]:
        """Defer excess jobs of a particular game to maintain fairness."""
        total = len(assignments)
        game_count = sum(1 for a in assignments if a.game == game)
        target_count = int(total * target_ratio)
        excess = game_count - target_count
        
        if excess <= 0:
            return assignments
        
        # Sort game assignments by priority (lower first to defer)
        game_assignments = [
            a for a in assignments if a.game == game
        ]
        game_assignments.sort(key=lambda a: a.expected_duration_ms)
        
        # Remove lowest priority excess assignments
        to_defer = set(a.job_id for a in game_assignments[:excess])
        
        return [a for a in assignments if a.job_id not in to_defer]
    
    async def _persist_assignments(
        self,
        assignments: List[JobAssignment]
    ):
        """Write assignments to database and notify agents."""
        for assignment in assignments:
            await self.db.execute(
                """
                UPDATE extraction_jobs
                SET status = 'assigned',
                    assigned_agent = $1,
                    assigned_at = NOW()
                WHERE id = $2
                  AND status = 'pending'  -- Only if still pending
                """,
                assignment.agent_id,
                assignment.job_id
            )
            
            # Notify agent via Redis pub/sub
            await self.redis.publish(
                f"agent:{assignment.agent_id}:jobs",
                json.dumps({
                    'job_id': assignment.job_id,
                    'game': assignment.game,
                    'source': assignment.source,
                    'assigned_at': datetime.utcnow().isoformat()
                })
            )
    
    def _estimate_duration(self, job: Dict) -> int:
        """Estimate job processing time in milliseconds."""
        base_times = {
            'match_list': 30000,      # 30s
            'match_detail': 120000,   # 2m
            'player_stats': 60000,    # 1m
            'team_roster': 45000,     # 45s
            'tournament_info': 30000, # 30s
            'rankings': 60000,        # 1m
            'live_match': 10000       # 10s
        }
        return base_times.get(job['job_type'], 60000)
```

---

## 8. Monitoring & Observability

### 8.1 Metrics to Track

```yaml
# metrics_configuration.yaml
metrics:
  # Job-level metrics
  jobs:
    - name: jobs_queued_total
      type: counter
      labels: [game, source, job_type]
      description: Total jobs queued
    
    - name: jobs_completed_total
      type: counter
      labels: [game, source, job_type, epoch]
      description: Total jobs completed successfully
    
    - name: jobs_failed_total
      type: counter
      labels: [game, source, job_type, error_type]
      description: Total job failures
    
    - name: jobs_duration_seconds
      type: histogram
      labels: [game, source, job_type]
      buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600]
      description: Job processing duration
    
    - name: jobs_queue_depth
      type: gauge
      labels: [game, status]
      description: Current number of jobs in queue
    
    - name: jobs_deduplicated_total
      type: counter
      labels: [game, source]
      description: Jobs skipped due to deduplication
  
  # Agent-level metrics
  agents:
    - name: agents_registered
      type: gauge
      labels: [game, status]
      description: Number of registered agents
    
    - name: agent_jobs_active
      type: gauge
      labels: [agent_id, game]
      description: Jobs currently being processed by agent
    
    - name: agent_heartbeat_seconds
      type: gauge
      labels: [agent_id]
      description: Seconds since last agent heartbeat
    
    - name: agent_utilization_ratio
      type: gauge
      labels: [agent_id, game]
      description: Agent utilization (0-1)
  
  # Source-level metrics
  sources:
    - name: source_requests_total
      type: counter
      labels: [source, game, endpoint]
      description: Total requests made to source
    
    - name: source_rate_limit_remaining
      type: gauge
      labels: [source, game]
      description: Remaining rate limit quota
    
    - name: source_response_time_seconds
      type: histogram
      labels: [source, endpoint]
      buckets: [0.1, 0.5, 1, 2, 5, 10]
      description: Source API response time
    
    - name: source_errors_total
      type: counter
      labels: [source, error_code]
      description: Source API errors
  
  # Data quality metrics
  quality:
    - name: data_records_extracted_total
      type: counter
      labels: [game, source, entity_type]
      description: Total records extracted
    
    - name: data_conflicts_detected_total
      type: counter
      labels: [game, source, conflict_type]
      description: Data conflicts detected
    
    - name: data_freshness_seconds
      type: gauge
      labels: [game, entity_type]
      description: Age of most recent data
    
    - name: data_completeness_ratio
      type: gauge
      labels: [game, source, entity_type]
      description: Data completeness score (0-1)
  
  # System metrics
  system:
    - name: db_connection_pool_active
      type: gauge
      labels: [pool_name]
      description: Active database connections
    
    - name: redis_operation_duration_seconds
      type: histogram
      labels: [operation]
      description: Redis operation duration
    
    - name: storage_bytes_total
      type: gauge
      labels: [game, storage_tier]
      description: Total storage used
```

### 8.2 Alert Conditions

```python
# alerting_rules.py
from dataclasses import dataclass
from typing import List, Callable, Any
from enum import Enum

class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class AlertRule:
    name: str
    severity: AlertSeverity
    condition: str
    threshold: Any
    duration: str
    description: str
    action: str

ALERT_RULES: List[AlertRule] = [
    # Queue depth alerts
    AlertRule(
        name="queue_depth_critical",
        severity=AlertSeverity.CRITICAL,
        condition="jobs_queue_depth",
        threshold=1000,
        duration="5m",
        description="Job queue depth exceeds 1000 jobs",
        action="Scale up agents or investigate bottlenecks"
    ),
    AlertRule(
        name="queue_depth_warning",
        severity=AlertSeverity.WARNING,
        condition="jobs_queue_depth",
        threshold=500,
        duration="10m",
        description="Job queue depth exceeds 500 jobs",
        action="Monitor queue growth trend"
    ),
    
    # Agent health alerts
    AlertRule(
        name="agent_heartbeat_missed",
        severity=AlertSeverity.CRITICAL,
        condition="agent_heartbeat_seconds",
        threshold=300,  # 5 minutes
        duration="1m",
        description="Agent has not sent heartbeat in 5 minutes",
        action="Check agent logs, reassign jobs if necessary"
    ),
    AlertRule(
        name="agent_heartbeat_warning",
        severity=AlertSeverity.WARNING,
        condition="agent_heartbeat_seconds",
        threshold=120,  # 2 minutes
        duration="2m",
        description="Agent heartbeat delayed",
        action="Monitor agent status"
    ),
    
    # Rate limit alerts
    AlertRule(
        name="rate_limit_critical",
        severity=AlertSeverity.CRITICAL,
        condition="source_rate_limit_remaining",
        threshold=0.10,  # 10%
        duration="1m",
        description="Rate limit below 10% for source",
        action="Pause non-essential extractions, alert on-call"
    ),
    AlertRule(
        name="rate_limit_warning",
        severity=AlertSeverity.WARNING,
        condition="source_rate_limit_remaining",
        threshold=0.25,  # 25%
        duration="5m",
        description="Rate limit below 25% for source",
        action="Reduce extraction frequency"
    ),
    
    # Error rate alerts
    AlertRule(
        name="error_rate_critical",
        severity=AlertSeverity.CRITICAL,
        condition="jobs_failed_total / jobs_completed_total",
        threshold=0.10,  # 10%
        duration="10m",
        description="Job failure rate exceeds 10%",
        action="Investigate source health, check for API changes"
    ),
    AlertRule(
        name="error_rate_warning",
        severity=AlertSeverity.WARNING,
        condition="jobs_failed_total / jobs_completed_total",
        threshold=0.05,  # 5%
        duration="15m",
        description="Job failure rate exceeds 5%",
        action="Review recent errors for patterns"
    ),
    
    # Data freshness alerts
    AlertRule(
        name="data_staleness_critical",
        severity=AlertSeverity.CRITICAL,
        condition="data_freshness_seconds",
        threshold=86400,  # 24 hours
        duration="5m",
        description="Data not updated in 24 hours",
        action="Verify extraction pipeline is functioning"
    ),
    AlertRule(
        name="live_data_staleness",
        severity=AlertSeverity.CRITICAL,
        condition="data_freshness_seconds",
        threshold=1800,  # 30 minutes
        duration="2m",
        description="Live match data stale for 30 minutes",
        action="Check live match agent health"
    ),
    
    # Conflict alerts
    AlertRule(
        name="conflict_rate_high",
        severity=AlertSeverity.WARNING,
        condition="data_conflicts_detected_total",
        threshold=50,
        duration="1h",
        description="High number of data conflicts detected",
        action="Review source consistency, check for API drift"
    ),
    
    # Resource alerts
    AlertRule(
        name="storage_usage_high",
        severity=AlertSeverity.WARNING,
        condition="storage_bytes_total",
        threshold="1TB",
        duration="1h",
        description="Storage usage exceeding threshold",
        action="Archive old data or expand storage"
    ),
]

class AlertManager:
    """Manages alert evaluation and notification."""
    
    def __init__(self, metrics_client, notification_channels):
        self.metrics = metrics_client
        self.channels = notification_channels
    
    async def evaluate_rules(self):
        """Evaluate all alert rules against current metrics."""
        for rule in ALERT_RULES:
            triggered = await self._evaluate_rule(rule)
            if triggered:
                await self._send_alert(rule)
    
    async def _evaluate_rule(self, rule: AlertRule) -> bool:
        """Evaluate a single alert rule."""
        # Query metrics backend (Prometheus, etc.)
        value = await self.metrics.query(rule.condition, duration=rule.duration)
        
        if isinstance(rule.threshold, (int, float)):
            return value > rule.threshold
        elif isinstance(rule.threshold, str):
            # Handle unit strings like "1TB"
            return self._compare_with_units(value, rule.threshold)
        
        return False
    
    async def _send_alert(self, rule: AlertRule):
        """Send alert through configured channels."""
        message = f"""
🚨 ALERT: {rule.name}
Severity: {rule.severity.value}
Description: {rule.description}
Action: {rule.action}
        """
        
        for channel in self.channels:
            await channel.send(message)
```

### 8.3 Dashboard Layout

```yaml
# dashboard_layout.yaml
dashboards:
  - name: "Dual-Game Overview"
    description: "High-level view of both games"
    panels:
      - title: "Jobs per Game (Last Hour)"
        type: time_series
        query: 'sum(rate(jobs_completed_total[5m])) by (game)'
        
      - title: "Queue Depth by Game"
        type: gauge
        query: 'jobs_queue_depth'
        thresholds:
          - value: 500, color: yellow
          - value: 1000, color: red
      
      - title: "Agent Utilization"
        type: bar_gauge
        query: 'avg(agent_utilization_ratio) by (game)'
      
      - title: "Data Freshness"
        type: stat
        query: 'data_freshness_seconds / 3600'
        unit: "hours"
      
      - title: "Error Rate by Game"
        type: time_series
        query: |
          sum(rate(jobs_failed_total[5m])) by (game) 
          / 
          sum(rate(jobs_completed_total[5m])) by (game)
  
  - name: "CS:GO Extraction"
    description: "Counter-Strike specific metrics"
    panels:
      - title: "HLTV Rate Limit"
        type: graph
        query: 'source_rate_limit_remaining{source="hltv",game="cs"}'
      
      - title: "Matches Extracted by Source"
        type: pie_chart
        query: 'sum(data_records_extracted_total{game="cs"}) by (source)'
      
      - title: "Epoch III Jobs (Current)"
        type: table
        query: 'jobs_queue_depth{game="cs",epoch="3"}'
      
      - title: "Processing Latency"
        type: heatmap
        query: 'jobs_duration_seconds_bucket{game="cs"}'
  
  - name: "Valorant Extraction"
    description: "Valorant specific metrics"
    panels:
      - title: "VLR Rate Limit"
        type: graph
        query: 'source_rate_limit_remaining{source="vlr",game="valorant"}'
      
      - title: "Matches Extracted by Source"
        type: pie_chart
        query: 'sum(data_records_extracted_total{game="valorant"}) by (source)'
      
      - title: "Live Match Status"
        type: table
        query: 'jobs_queue_depth{game="valorant",job_type="live_match"}'
      
      - title: "China Region Lag"
        type: stat
        query: 'data_freshness_seconds{game="valorant",region="china"}'
  
  - name: "Agent Health"
    description: "Per-agent monitoring"
    panels:
      - title: "Agent Status Grid"
        type: table
        columns:
          - Agent ID
          - Game
          - Status
          - Last Heartbeat
          - Current Jobs
          - Uptime
      
      - title: "Heartbeat Latency"
        type: time_series
        query: 'agent_heartbeat_seconds'
      
      - title: "Job Assignment Rate"
        type: graph
        query: 'rate(jobs_completed_total[5m]) by (agent_id)'
```

---

## 9. Failure Recovery

### 9.1 Job Retry Strategy

```python
# retry_strategy.py
from dataclasses import dataclass
from typing import List, Optional, Callable
from datetime import datetime, timedelta
import asyncio

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 4
    delays: List[int] = None  # Seconds between retries
    exponential_base: float = 2.0
    max_delay_seconds: int = 3600  # 1 hour
    retryable_errors: List[str] = None
    
    def __post_init__(self):
        if self.delays is None:
            # Default: 1min, 5min, 15min, 1hr
            self.delays = [60, 300, 900, 3600]
        if self.retryable_errors is None:
            self.retryable_errors = [
                'connection_error',
                'timeout',
                'rate_limit_exceeded',
                'temporary_failure',
                '503',
                '502',
                '504'
            ]

class RetryManager:
    """Manages job retry logic with exponential backoff."""
    
    def __init__(self, db_pool, config: RetryConfig = None):
        self.db = db_pool
        self.config = config or RetryConfig()
    
    async def handle_job_failure(
        self,
        job_id: str,
        error: Exception,
        error_details: dict = None
    ) -> bool:
        """
        Handle a job failure. Returns True if job should be retried.
        """
        job = await self._get_job(job_id)
        
        if not job:
            logger.error(f"Job {job_id} not found for retry handling")
            return False
        
        # Check if error is retryable
        error_type = self._classify_error(error)
        
        if error_type not in self.config.retryable_errors:
            # Non-retryable error, mark as failed immediately
            await self._mark_permanently_failed(job_id, error, error_type)
            return False
        
        # Check retry count
        current_retry = job.get('retry_count', 0)
        
        if current_retry >= self.config.max_retries:
            await self._mark_max_retries_exceeded(job_id, error)
            return False
        
        # Schedule retry
        delay = self._calculate_delay(current_retry)
        await self._schedule_retry(job_id, current_retry + 1, delay, error)
        
        logger.info(
            f"Scheduled retry {current_retry + 1}/{self.config.max_retries} "
            f"for job {job_id} in {delay}s"
        )
        return True
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for retry decisions."""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Connection errors
        if any(x in error_str for x in ['connection', 'timeout', 'refused', 'reset']):
            return 'connection_error'
        
        # Rate limiting
        if any(x in error_str for x in ['rate limit', 'too many requests', '429']):
            return 'rate_limit_exceeded'
        
        # Server errors
        if any(x in error_str for x in ['503', '502', '504', 'service unavailable']):
            return '503'
        
        # Parsing errors (usually not retryable)
        if any(x in error_str for x in ['parse', 'json', 'xml', 'html']):
            return 'parse_error'
        
        # Data errors (not retryable)
        if any(x in error_str for x in ['not found', 'invalid', 'missing']):
            return 'data_error'
        
        return 'unknown'
    
    def _calculate_delay(self, retry_count: int) -> int:
        """Calculate delay before next retry."""
        if retry_count < len(self.config.delays):
            return self.config.delays[retry_count]
        
        # Exponential backoff for beyond configured delays
        base = self.config.delays[-1] if self.config.delays else 60
        delay = int(base * (self.config.exponential_base ** 
                           (retry_count - len(self.config.delays) + 1)))
        
        return min(delay, self.config.max_delay_seconds)
    
    async def _schedule_retry(
        self,
        job_id: str,
        new_retry_count: int,
        delay_seconds: int,
        error: Exception
    ):
        """Schedule a job retry with delay."""
        scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        await self.db.execute(
            """
            UPDATE extraction_jobs
            SET status = 'retrying',
                retry_count = $1,
                error_message = $2,
                metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{retry_scheduled_at}',
                    to_jsonb($3)
                )
            WHERE id = $4
            """,
            new_retry_count,
            str(error)[:500],  # Truncate long errors
            scheduled_time.isoformat(),
            job_id
        )
        
        # Add to delayed queue (Redis sorted set)
        await self.redis.zadd(
            'delayed_jobs',
            {job_id: scheduled_time.timestamp()}
        )
    
    async def process_delayed_jobs(self):
        """Background task to move delayed jobs back to pending."""
        while True:
            now = datetime.utcnow().timestamp()
            
            # Get jobs that are ready to retry
            ready_jobs = await self.redis.zrangebyscore(
                'delayed_jobs',
                0,
                now
            )
            
            for job_id in ready_jobs:
                # Move to pending
                await self.db.execute(
                    """
                    UPDATE extraction_jobs
                    SET status = 'pending',
                        assigned_agent = NULL,
                        assigned_at = NULL,
                        started_at = NULL
                    WHERE id = $1 AND status = 'retrying'
                    """,
                    job_id
                )
                
                # Remove from delayed queue
                await self.redis.zrem('delayed_jobs', job_id)
                
                logger.info(f"Job {job_id} moved from retrying to pending")
            
            # Sleep before next check
            await asyncio.sleep(30)
    
    async def _mark_permanently_failed(
        self,
        job_id: str,
        error: Exception,
        error_type: str
    ):
        """Mark job as permanently failed (non-retryable)."""
        await self.db.execute(
            """
            UPDATE extraction_jobs
            SET status = 'failed',
                error_message = $1,
                completed_at = NOW(),
                metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{failure_reason}',
                    to_jsonb($2)
                )
            WHERE id = $3
            """,
            str(error)[:500],
            f"non_retryable:{error_type}",
            job_id
        )
    
    async def _mark_max_retries_exceeded(self, job_id: str, error: Exception):
        """Mark job as failed due to max retries exceeded."""
        await self.db.execute(
            """
            UPDATE extraction_jobs
            SET status = 'failed',
                error_message = $1,
                completed_at = NOW(),
                metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{failure_reason}',
                    '"max_retries_exceeded"'::jsonb
                )
            WHERE id = $2
            """,
            str(error)[:500],
            job_id
        )
        
        # Alert on persistent failures
        await self._alert_max_retries(job_id)
```

### 9.2 Agent Failure Handling

```python
# agent_failure_handler.py
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio

class AgentFailureHandler:
    """Handles agent failures and recovery."""
    
    def __init__(self, db_pool, redis_client, coordinator):
        self.db = db_pool
        self.redis = redis_client
        self.coordinator = coordinator
        self.heartbeat_timeout = timedelta(minutes=5)
    
    async def monitor_agent_health(self):
        """Background task to monitor agent heartbeats."""
        while True:
            await self._check_agent_heartbeats()
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _check_agent_heartbeats(self):
        """Check for agents that have missed heartbeats."""
        cutoff = datetime.utcnow() - self.heartbeat_timeout
        
        failed_agents = await self.db.fetch(
            """
            SELECT id, current_job_ids, game_specialization
            FROM extraction_agents
            WHERE last_heartbeat < $1
              AND status IN ('idle', 'busy')
            """,
            cutoff
        )
        
        for agent in failed_agents:
            await self._handle_agent_failure(
                agent['id'],
                agent['current_job_ids'] or [],
                agent['game_specialization']
            )
    
    async def _handle_agent_failure(
        self,
        agent_id: str,
        current_jobs: List[str],
        game_specialization: List[str]
    ):
        """Handle a detected agent failure."""
        logger.error(f"Agent {agent_id} failed - missed heartbeat")
        
        # 1. Mark agent as offline
        await self.db.execute(
            """
            UPDATE extraction_agents
            SET status = 'offline',
                current_job_ids = NULL
            WHERE id = $1
            """,
            agent_id
        )
        
        # 2. Reassign in-progress jobs
        for job_id in current_jobs:
            await self._reassign_job(job_id, agent_id)
        
        # 3. Notify monitoring
        await self._alert_agent_failure(agent_id, len(current_jobs))
        
        # 4. Archive agent logs
        await self._archive_agent_logs(agent_id)
    
    async def _reassign_job(self, job_id: str, from_agent: str):
        """Reassign a job from a failed agent."""
        # Get job details
        job = await self.db.fetchrow(
            "SELECT * FROM extraction_jobs WHERE id = $1",
            job_id
        )
        
        if not job:
            return
        
        # Only reassign if still in processing/assigned state
        if job['status'] not in ('processing', 'assigned'):
            return
        
        # Increment retry count since this is a failure
        new_retry_count = (job.get('retry_count', 0) + 1)
        
        if new_retry_count > 3:  # Max retries
            await self.db.execute(
                """
                UPDATE extraction_jobs
                SET status = 'failed',
                    error_message = 'Agent failure - max retries exceeded',
                    completed_at = NOW()
                WHERE id = $1
                """,
                job_id
            )
        else:
            # Reset to pending for reassignment
            await self.db.execute(
                """
                UPDATE extraction_jobs
                SET status = 'pending',
                    assigned_agent = NULL,
                    assigned_at = NULL,
                    started_at = NULL,
                    retry_count = $2,
                    error_message = 'Agent failure - reassigning'
                WHERE id = $1
                """,
                job_id,
                new_retry_count
            )
            
            logger.info(f"Reassigned job {job_id} from failed agent {from_agent}")
    
    async def _archive_agent_logs(self, agent_id: str):
        """Archive logs from failed agent for debugging."""
        # In production, this would collect logs from agent's log aggregation
        archive_path = f"/data/logs/archive/{agent_id}/{datetime.utcnow():%Y%m%d_%H%M%S}"
        
        await self.db.execute(
            """
            INSERT INTO agent_failure_logs (
                agent_id, archived_at, log_path, metadata
            ) VALUES ($1, NOW(), $2, $3)
            """,
            agent_id,
            archive_path,
            json.dumps({
                'failure_time': datetime.utcnow().isoformat(),
                'reason': 'missed_heartbeat'
            })
        )
    
    async def recover_agent(self, agent_id: str):
        """Mark a recovered agent as available again."""
        await self.db.execute(
            """
            UPDATE extraction_agents
            SET status = 'idle',
                last_heartbeat = NOW()
            WHERE id = $1
            """,
            agent_id
        )
        
        logger.info(f"Agent {agent_id} recovered and marked as idle")
```

---

## 10. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CENTRAL JOB COORDINATOR                           │   │
│  │                    ═══════════════════════                           │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │   SCHEDULER  │  │  DISPATCHER  │  │   MONITOR    │               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ • Priority   │  │ • Agent      │  │ • Heartbeats │               │   │
│  │  │   Queue      │  │   Matching   │  │ • Metrics    │               │   │
│  │  │ • Dependency │  │ • Rate Limit │  │ • Alerts     │               │   │
│  │  │   Resolution │  │   Check      │  │ • Recovery   │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │                    DATABASE LAYER                            │    │   │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │    │   │
│  │  │  │Job Queue  │  │  Agents   │  │ Rate      │  │ Conflicts │ │    │   │
│  │  │  │Tables     │  │  Registry │  │ Limits    │  │ Log       │ │    │   │
│  │  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘ │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                    ┌──────────────┼──────────────┐                         │
│                    │              │              │                         │
│              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐                  │
│              │   CS      │  │ SHARED    │  │ VALORANT  │                  │
│              │   QUEUE   │  │ RESOURCES │  │ QUEUE     │                  │
│              └─────┬─────┘  └───────────┘  └─────┬─────┘                  │
│                    │                               │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │         GAME PARTITION        │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │                               │                        │
│              ┌─────▼─────┐                 ┌─────▼─────┐                  │
│              │   CS      │                 │ VALORANT  │                  │
│              │  AGENTS   │                 │  AGENTS   │                  │
│              │ ═════════ │                 │ ═════════ │                  │
│              │           │                 │           │                  │
│              │ • Scouts  │                 │ • Scouts  │                  │
│              │ • Detail  │                 │ • Detail  │                  │
│              │ • Player  │                 │ • Player  │                  │
│              │ • Live    │                 │ • Live    │                  │
│              └─────┬─────┘                 └─────┬─────┘                  │
│                    │                               │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │      AGENT GAME ISOLATION     │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │                               │                        │
│              ┌─────▼─────┐                 ┌─────▼─────┐                  │
│              │ CS DATA   │                 │ VALORANT  │                  │
│              │ SOURCES   │                 │ DATA      │                  │
│              │ ═════════ │                 │ SOURCES   │                  │
│              │           │                 │ ═════════ │                  │
│              │ • HLTV    │                 │ • VLR     │                  │
│              │ • ESL     │                 │ • RIB     │                  │
│              │ • Liquip. │                 │ • Liquip. │                  │
│              └─────┬─────┘                 └─────┬─────┘                  │
│                    │                               │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │       EXTERNAL SOURCES        │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │                               │                        │
│              ┌─────▼─────┐                 ┌─────▼─────┐                  │
│              │  RAW CS   │                 │ RAW VAL   │                  │
│              │  STORAGE  │                 │ STORAGE   │                  │
│              │ ═════════ │                 │ ═════════ │                  │
│              │           │                 │           │                  │
│              │/raw/cs/   │                 │/raw/val/  │                  │
│              │ • hltv    │                 │ • vlr     │                  │
│              │ • matches │                 │ • matches │                  │
│              │ • players │                 │ • players │                  │
│              │ • teams   │                 │ • teams   │                  │
│              └─────┬─────┘                 └─────┬─────┘                  │
│                    │                               │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │      RAW DATA PARTITION       │                        │
│  ══════════════════╪═══════════════════════════════╪══════════════════════ │
│                    │                               │                        │
│              ┌─────▼─────┐                 ┌─────▼─────┐                  │
│              │   CS      │                 │ VALORANT  │                  │
│              │ DATABASE  │                 │ DATABASE  │                  │
│              │ ═════════ │                 │ ═════════ │                  │
│              │           │                 │           │                  │
│              │cs_matches │                 │val_matches│                  │
│              │cs_players │                 │val_players│                  │
│              │cs_teams   │                 │val_teams  │                  │
│              └───────────┘                 └───────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SHARED TABLES (Cross-Game)                        │   │
│  │  • tournaments (with game_type column)                               │   │
│  │  • leagues (with game_type column)                                   │   │
│  │  • data_sources                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Sequence

```
1. SCHEDULING PHASE
═══════════════════════════════════════════════════════════════

   Coordinator                    Scheduler
        │                            │
        │◀───── Time Trigger ───────▶│  (Every N minutes based on epoch)
        │                            │
        │  ┌─────────────────────────┴─────────────────────────┐
        │  │ Generate jobs for CS + Valorant                    │
        │  │ • Check existing jobs (deduplication)             │
        │  │ • Create missing jobs                             │
        │  │ • Set priorities based on epoch                   │
        │  └─────────────────────────┬─────────────────────────┘
        │                            │
        ◀──── Jobs Inserted ────────┤
        │         into DB            │
        │                            │

2. ASSIGNMENT PHASE
═══════════════════════════════════════════════════════════════

   Coordinator                    Dispatcher              Agents
        │                            │                      │
        │◀──── Scan Interval ───────▶│                      │
        │                            │                      │
        │  ┌─────────────────────────┴─────┐                │
        │  │ Query pending jobs              │                │
        │  │ Filter by dependencies          │                │
        │  │ Check rate limits               │                │
        │  └─────────────────────────┬─────┘                │
        │                            │                      │
        │  ┌─────────────────────────┴─────┐                │
        │  │ Query available agents          │                │
        │  │ Filter by capabilities          │                │
        │  │ Check health (heartbeat)        │                │
        │  └─────────────────────────┬─────┘                │
        │                            │                      │
        │  ┌─────────────────────────┴─────────────────────────┐
        │  │ MATCH: Assign jobs to suitable agents             │
        │  │ • CS jobs → CS-capable agents                     │
        │  │ • Valorant jobs → Valorant-capable agents         │
        │  │ • Apply fairness (prevent starvation)             │
        │  └─────────────────────────┬─────────────────────────┘
        │                            │                      │
        │                            │──── Job Assignment ─▶│
        │                            │   (via Redis pub/sub)│
        │                            │                      │

3. EXTRACTION PHASE
═══════════════════════════════════════════════════════════════

     Agent                     Source API                Raw Storage
        │                            │                          │
        │◀──── Receive Job ──────────┤                          │
        │                            │                          │
        │  ┌─────────────────────────┴─────────────────────────┐
        │  │ Acquire distributed lock                           │
        │  │ Check for existing data (conflict detection)       │
        │  └─────────────────────────┬─────────────────────────┘
        │                            │                          │
        │──── API Request ──────────▶│                          │
        │                            │                          │
        │◀──── Response ─────────────┤                          │
        │                            │                          │
        │  ┌─────────────────────────────────────────────────────┐
        │  │ Process response                                    │
        │  │ • Normalize data                                   │
        │  │ • Compute checksum                                 │
        │  │ • Detect conflicts                                 │
        │  └─────────────────────────┬─────────────────────────┘
        │                            │                          │
        │                            │                          │
        │────────────────────────────┼───── Write Raw Data ────▶│
        │                            │     (partitioned by game)│
        │                            │                          │
        │◀───────────────────────────┼────── Confirm Write ─────┤
        │                            │                          │
        │  Update job status: COMPLETED                          │
        │  Release lock                                          │
        │                            │                          │

4. VALIDATION PHASE (Async)
═══════════════════════════════════════════════════════════════

   Validation Agent                    Data
        │                               │
        │◀──── Scheduled Check ────────┤
        │                               │
        │  ┌───────────────────────────┴─────────────────────┐
        │  │ Cross-reference sources                          │
        │  │ • Compare HLTV vs Liquipedia (CS)                │
        │  │ • Compare VLR vs RIB (Valorant)                  │
        │  └───────────────────────────┬─────────────────────┘
        │                               │
        │  ┌───────────────────────────┴─────────────────────┐
        │  │ Detect anomalies                                 │
        │  │ • Score mismatches                               │
        │  │ • Impossible statistics                          │
        │  │ • Missing required fields                        │
        │  └───────────────────────────┬─────────────────────┘
        │                               │
        │──── Flag Issues ─────────────▶│ (to conflict log)
        │                               │

5. CONSUMPTION PHASE
═══════════════════════════════════════════════════════════════

   Downstream Systems              Processed Data
        │                               │
        │◀──── Query Request ──────────┤
        │                               │
        │  ┌───────────────────────────┴─────────────────────┐
        │  │ Read from game-specific tables                   │
        │  │ • cs_* for Counter-Strike                        │
        │  │ • val_* for Valorant                             │
        │  │ • shared tables with game_type filter            │
        │  └───────────────────────────┬─────────────────────┘
        │                               │
        ◀──── Query Results ──────────┤
        │                               │
```

---

## Appendix A: Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Set up database schema (PostgreSQL)
- [ ] Implement job queue tables and functions
- [ ] Set up Redis for caching and pub/sub
- [ ] Create basic agent registration API
- [ ] Implement heartbeat monitoring

### Phase 2: Core Coordination (Week 3-4)
- [ ] Build job scheduler with epoch awareness
- [ ] Implement queue distribution algorithm
- [ ] Add rate limiting per source
- [ ] Create agent capability matching
- [ ] Implement distributed locking

### Phase 3: Conflict Prevention (Week 5-6)
- [ ] Build job deduplication system
- [ ] Implement write-ahead conflict detection
- [ ] Add data versioning for raw extractions
- [ ] Create conflict resolution workflows
- [ ] Build validation agent framework

### Phase 4: Monitoring & Reliability (Week 7-8)
- [ ] Set up metrics collection (Prometheus)
- [ ] Create alert rules and notification system
- [ ] Build dashboards (Grafana)
- [ ] Implement retry strategies
- [ ] Add agent failure recovery

### Phase 5: Scaling & Optimization (Week 9-10)
- [ ] Horizontal scaling for agents
- [ ] Database query optimization
- [ ] Cache layer optimization
- [ ] Load testing and tuning
- [ ] Documentation and runbooks

---

## Appendix B: Configuration Reference

```yaml
# coordinator-config.yaml
coordinator:
  scheduling:
    interval_seconds: 30
    batch_size: 50
    max_queue_depth: 10000
  
  fairness:
    cs_allocation_percent: 50
    target_latency_seconds:
      epoch_1: 86400    # 24 hours
      epoch_2: 21600    # 6 hours
      epoch_3: 300      # 5 minutes
  
  rate_limits:
    hltv:
      rpm: 30
      rph: 500
      concurrent: 2
    vlr:
      rpm: 60
      rph: 1000
      concurrent: 3
    liquipedia:
      rpm: 30
      rph: 300
      concurrent: 2
  
  agent:
    heartbeat_timeout_seconds: 120
    max_jobs_per_agent: 5
    cooldown_seconds: 60
  
  retry:
    max_retries: 4
    delays: [60, 300, 900, 3600]
    exponential_base: 2.0
```

---

*Document Version: 1.0*
*Last Updated: 2024*
*Status: Architecture Specification*
