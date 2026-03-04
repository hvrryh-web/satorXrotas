#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Axiom Esports Database Setup Script
.DESCRIPTION
    Applies migrations and seeds the database for local development or production.
    Supports both local Docker and cloud databases (Supabase/Neon).
.PARAMETER Reset
    Clear existing seed data before seeding
.PARAMETER DryRun
    Show what would be done without making changes
.PARAMETER OnlyMigrations
    Only run migrations, skip seeding
.PARAMETER OnlySeed
    Only run seeding, skip migrations
.EXAMPLE
    .\setup.ps1                    # Full setup
    .\setup.ps1 -OnlyMigrations    # Just migrations
    .\setup.ps1 -OnlySeed          # Just seeding
    .\setup.ps1 -Reset             # Reset and re-seed
#>
[CmdletBinding()]
param(
    [switch]$Reset,
    [switch]$DryRun,
    [switch]$OnlyMigrations,
    [switch]$OnlySeed
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Axiom Esports Database Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Load environment variables
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Write-Host "Loading environment from $envFile" -ForegroundColor Gray
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

# Determine database connection
$databaseUrl = $env:DATABASE_URL
if (-not $databaseUrl) {
    $host = $env:POSTGRES_HOST -or "localhost"
    $port = $env:POSTGRES_PORT -or "5432"
    $db = $env:POSTGRES_DB -or "axiom_esports"
    $user = $env:POSTGRES_USER -or "axiom"
    $pass = $env:POSTGRES_PASSWORD -or "changeme"
    $databaseUrl = "postgresql://${user}:${pass}@${host}:${port}/${db}"
}

Write-Host "Database: $($databaseUrl -replace '://[^@]+@', '://***@')" -ForegroundColor Gray

# Wait for database to be ready
function Wait-Database {
    param([int]$Timeout = 60)
    Write-Host "Waiting for database..." -ForegroundColor Yellow -NoNewline
    $start = Get-Date
    while ((Get-Date) - $start).TotalSeconds -lt $Timeout {
        try {
            $result = psql $databaseUrl -c "SELECT 1" 2>$null
            if ($result -match "1") {
                Write-Host " READY" -ForegroundColor Green
                return $true
            }
        } catch {}
        Write-Host "." -ForegroundColor Yellow -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host " TIMEOUT" -ForegroundColor Red
    return $false
}

# Check if psql is available
$psqlAvailable = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlAvailable) {
    Write-Warning "psql not found in PATH. Migrations must be applied manually."
    Write-Host "Download from: https://www.postgresql.org/download/"
}

# Run migrations
if (-not $OnlySeed) {
    Write-Host "`nApplying migrations..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would apply migrations:" -ForegroundColor Cyan
        Get-ChildItem "$scriptDir\migrations\*.sql" | Sort-Object Name | ForEach-Object {
            Write-Host "  - $($_.Name)" -ForegroundColor Gray
        }
    }
    elseif ($psqlAvailable) {
        if (-not (Wait-Database)) {
            Write-Error "Database not available"
            exit 1
        }
        
        $migrations = Get-ChildItem "$scriptDir\migrations\*.sql" | Sort-Object Name
        foreach ($migration in $migrations) {
            Write-Host "  Applying $($migration.Name)..." -ForegroundColor Gray -NoNewline
            try {
                $output = psql $databaseUrl -f $migration.FullName 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host " OK" -ForegroundColor Green
                } else {
                    Write-Host " FAILED" -ForegroundColor Red
                    Write-Error $output
                }
            } catch {
                Write-Host " FAILED" -ForegroundColor Red
                Write-Error $_
            }
        }
        Write-Host "Migrations complete" -ForegroundColor Green
    }
    else {
        Write-Host "Skipping migrations (psql not available)" -ForegroundColor Yellow
    }
}

# Run seeder
if (-not $OnlyMigrations) {
    Write-Host "`nSeeding database..." -ForegroundColor Yellow
    
    $seedScript = Join-Path $scriptDir "seed_data\seed_database.py"
    
    if (-not (Test-Path $seedScript)) {
        Write-Error "Seed script not found: $seedScript"
        exit 1
    }
    
    $args = @()
    if ($Reset) { $args += "--reset" }
    if ($DryRun) { $args += "--dry-run" }
    
    try {
        & python $seedScript @args
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Seeding complete" -ForegroundColor Green
        } else {
            Write-Error "Seeding failed with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Error "Seeding failed: $_"
    }
}

# Verify
Write-Host "`nVerifying database..." -ForegroundColor Yellow
if ($psqlAvailable) {
    try {
        $stats = psql $databaseUrl -c "
SELECT 'player_performance' as table_name, count(*) as count FROM player_performance
UNION ALL
SELECT 'web_data_store', count(*) FROM web_data_store WHERE data_type = 'match_summary'
UNION ALL
SELECT 'sator_events', count(*) FROM sator_events
UNION ALL
SELECT 'arepo_markers', count(*) FROM arepo_markers;" 2>$null
        Write-Host "Database statistics:" -ForegroundColor Gray
        $stats | Select-Object -Skip 2 | Write-Host
    } catch {
        Write-Warning "Could not retrieve database statistics"
    }
}

Write-Host "`nSetup complete!" -ForegroundColor Green
