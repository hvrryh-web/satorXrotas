# RadiantX — Esports Analytics Platform

A unified platform for esports analytics, news, and simulation.

## Repository Structure

```
/
├── website/          # Static site (deployable) — News, Stats, Analytics, Tournaments
├── simulation-game/  # Godot/C# simulation game (future) — Connected to website data
├── shared/           # Data pipelines, APIs, schemas used by both
└── README.md         # This file
```

## Quick Start

### Website
```bash
cd website
npm install
npm run dev
```

### Simulation Game
Open `simulation-game/project.godot` in Godot 4.x

## Architecture

- **Website**: Static HTML/CSS/JS with Tailwind, deployable anywhere
- **Simulation**: Godot engine with C# core for tactical FPS simulation
- **Shared**: Python data extraction pipeline (axiom-esports-data)

The simulation game will consume data from the shared pipeline, creating a bridge between real esports stats and simulated gameplay.
