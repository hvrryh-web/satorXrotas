# SATOR Web Platform

React frontend for the SATOR esports analytics platform.

## Features

- **Dashboard** — Overview of matches, players, and platform statistics
- **Player Explorer** — Search, filter, and analyze player performance metrics
- **Match History** — View live, upcoming, and finished matches
- **Analytics** — SimRating, RAR scores, and investment grades

## Tech Stack

- **Vite** — Build tool and dev server
- **React 18** — UI library with hooks
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling
- **TanStack Query** — Data fetching and caching
- **React Router** — Client-side routing
- **Recharts** — Data visualization

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# From the monorepo root
npm install

# Or directly in this package
cd shared/apps/sator-web
npm install
```

### Environment Setup

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file to set your API URL:

```env
VITE_API_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

The dev server will start at `http://localhost:3000`.

### Build

```bash
npm run build
```

Output will be in the `dist/` directory, ready for static hosting on Vercel, Netlify, etc.

### Type Checking

```bash
npm run typecheck
```

## Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── Layout/       # Header, Sidebar, Footer
│   ├── Players/      # PlayerList, PlayerCard, PlayerDetail
│   ├── Matches/      # MatchList, MatchCard
│   ├── Analytics/    # SimRatingChart, StatsTable
│   ├── SatorSphere.tsx
│   └── ErrorBoundary.tsx
├── hooks/            # Custom React hooks
│   ├── useApi.ts     # TanStack Query hooks
│   └── usePlayers.ts # Player-specific hooks
├── pages/            # Route components
│   ├── DashboardPage.tsx
│   ├── PlayersPage.tsx
│   ├── PlayerDetailPage.tsx
│   ├── MatchesPage.tsx
│   ├── MatchDetailPage.tsx
│   └── AnalyticsPage.tsx
├── services/         # API clients
│   └── api.ts
├── types/            # TypeScript types
│   └── index.ts
├── styles/           # Global styles
│   └── globals.css
├── main.tsx          # App entry point
└── App.tsx           # Router configuration
```

## API Integration

The app expects a REST API at `VITE_API_URL` with the following endpoints:

- `GET /api/players/` — List players with filters
- `GET /api/players/:id` — Get player details
- `GET /api/matches` — List matches
- `GET /api/matches/:id` — Get match details
- `GET /api/analytics/simrating/:id` — Get SimRating breakdown
- `GET /api/analytics/rar/:id` — Get RAR score
- `GET /api/analytics/investment/:id` — Get investment grade

## Design System

### Colors

- `--radiant-black: #0a0a0f` — Background
- `--radiant-card: #14141f` — Card backgrounds
- `--radiant-border: #2a2a3a` — Borders
- `--radiant-red: #ff4655` — Primary accent
- `--radiant-cyan: #00d4ff` — Secondary accent
- `--radiant-gold: #ffd700` — High values
- `--radiant-green: #00ff88` — Success

### Typography

- **Inter** — Primary font
- **JetBrains Mono** — Monospace for numbers/stats

## Deployment

### Vercel

1. Connect your GitHub repo to Vercel
2. Set root directory to `shared/apps/sator-web`
3. Set build command to `npm run build`
4. Set output directory to `dist`
5. Add environment variable `VITE_API_URL`

### Netlify

1. Connect your GitHub repo
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Add environment variable `VITE_API_URL`

## License

MIT — see LICENSE at repo root.
