# Repository Restructure Implementation — PowerShell Compatible
# Target: satorXrotas → Satire-deck-Veritas structure
# Phase: Archive existing, establish new hierarchy

## Current State Analysis
- Root folders: simulation-game, website, shared, tests, legacy, docs
- Root .md files: 15+ documentation files
- Git: Initialized, remote configured

## Implementation Steps (with PowerShell equivalents)

### STEP 1: Create pre-historic-legacy structure
# Bash:
mkdir -p pre-historic-legacy/{01-simulation-game,02-website,03-shared/apps,03-shared/axiom-esports-data,03-shared/packages,04-tests,05-legacy-docs}

# PowerShell:
$folders = @(
    "pre-historic-legacy\01-simulation-game",
    "pre-historic-legacy\02-website", 
    "pre-historic-legacy\03-shared\apps",
    "pre-historic-legacy\03-shared\axiom-esports-data",
    "pre-historic-legacy\03-shared\packages",
    "pre-historic-legacy\04-tests",
    "pre-historic-legacy\05-legacy-docs"
)
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force
}

### STEP 2: Move existing content to archive
# Bash:
mv simulation-game/* pre-historic-legacy/01-simulation-game/
mv website/* pre-historic-legacy/02-website/
mv shared/* pre-historic-legacy/03-shared/
mv tests/* pre-historic-legacy/04-tests/
mv legacy/* pre-historic-legacy/05-legacy-docs/

# PowerShell:
Move-Item -Path "simulation-game\*" -Destination "pre-historic-legacy\01-simulation-game\"
Move-Item -Path "website\*" -Destination "pre-historic-legacy\02-website\"
Move-Item -Path "shared\*" -Destination "pre-historic-legacy\03-shared\"
Move-Item -Path "tests\*" -Destination "pre-historic-legacy\04-tests\"
Move-Item -Path "legacy\*" -Destination "pre-historic-legacy\05-legacy-docs\"

### STEP 3: Move root .md files to legacy docs
# Bash:
mv *.md pre-historic-legacy/05-legacy-docs/

# PowerShell:
Get-ChildItem -Path "." -Filter "*.md" | Move-Item -Destination "pre-historic-legacy\05-legacy-docs\"

### STEP 4: Create new top-level structure
# Bash:
mkdir -p {context,frameworks/{1235-REVIEW,AGENT-COORDINATION,DESIGN-SYSTEM,WIREFRAME-PROTOCOL},tools/{prompts,templates,scripts},roles,active/{sprint-current,wireframes-v3,experiments},deliverables/{wireframes-v1,wireframes-v2,releases}}

# PowerShell:
$newFolders = @(
    "context",
    "frameworks\1235-REVIEW",
    "frameworks\AGENT-COORDINATION", 
    "frameworks\DESIGN-SYSTEM",
    "frameworks\WIREFRAME-PROTOCOL",
    "tools\prompts",
    "tools\templates",
    "tools\scripts",
    "roles",
    "active\sprint-current",
    "active\wireframes-v3",
    "active\experiments",
    "deliverables\wireframes-v1",
    "deliverables\wireframes-v2",
    "deliverables\releases"
)
foreach ($folder in $newFolders) {
    New-Item -ItemType Directory -Path $folder -Force
}

### STEP 5: Move docs/ content to appropriate new locations
# Context files → context/
# Framework files → frameworks/
# Role files → roles/
# Prompt files → tools/prompts/

### STEP 6: Create manifest files
# ARCHIVE-MANIFEST.md, MIGRATION-PLAN.md, REVIEW-SCHEDULE.md

### STEP 7: Update README.md
# Rewrite with new structure documentation
