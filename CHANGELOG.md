# Changelog

All notable changes to the SATOR/RadiantX platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Major Platform Update

### 🎨 Added - Porcelain³ Design System
- **Design System**: Complete branded design system inspired by Ralph Lauren, Apple, Nike, 5 Gum
  - White hues: Pristine, Cream, Ash, Cloud, Dirty whites
  - Blue hues: Porcelain, Abyssal, Navy, Royal, Ultramarine, Neon, Frost, Pastel, Baby
  - Gold hues: Celestial, Metallic, Neon Yellows
  - Glass morphism effects with backdrop filters
  - Typography system (Playfair Display, Inter, JetBrains Mono)

### 🖥️ Added - Web Dashboard Platform
- **Landing Page**: Animated entry with SATOR³ branding
- **Loading Corridor**: 3D perspective corridor animation
- **Service Selection Page**: Quarterly grid with 5 service hubs
  - AdvancedAnalyticsHub (Gold)
  - Stats*ReferenceHub (Neon Blue)
  - InfoHub (Pastel Blue)
  - GameHub (Navy Blue)
  - HelpHub (Center, expandable)
- **HelpHub Component**:
  - Quick Start Guide (4-step onboarding)
  - User Guides (6 guide cards)
  - Troubleshooting (expandable FAQs)
  - System Health Dashboard (8 monitored services)
- **QuarterGrid Component**: Click & drag resizable 4-quadrant grid

### 🏗️ Added - Free-Tier Deployment Architecture
- **Zero-Cost Stack**:
  - Supabase (PostgreSQL) - 500MB storage
  - Render (FastAPI) - 750hrs/month
  - Vercel (React) - 100GB bandwidth
  - GitHub Pages (Static) - 1GB storage
  - GitHub Actions (CI/CD) - 2000 mins/month
- **Cold Start Mitigation**: Keepalive cron workflow
- **Deployment Configs**: render.yaml, vercel.json, GitHub Actions workflows

### 🔧 Added - FastAPI Backend
- **Main Application**: Production-ready FastAPI with CORS, health checks
- **Firewall Middleware**: Data partition enforcement (GAME_ONLY_FIELDS)
- **Database Integration**: Connection pooling (2-5), retry logic
- **Routes**: Players, Matches, Analytics endpoints
- **Docker Support**: Multi-stage Dockerfile

### 🎮 Added - Godot Game Integration
- **LiveSeasonModule.gd**: Match data extraction with firewall
- **ExportClient.gd**: HTTP client with retry logic
- **Data Partition Firewall**: Prevents game-internal data leakage
- **Test Suite**: Unit tests for sanitization

### 🗄️ Added - Database Infrastructure
- **Migrations**: 001-009 SQL migrations
  - Initial schema, SATOR Square layers, Dual storage
  - Extraction log, Staging system, Monitoring tables
  - Dual-game partitioning (CS + Valorant)
  - Dashboard tables, Alert/scheduler tables
- **Partitioned Tables**: List partitioning by game (cs/valorant)
- **TimescaleDB**: Hypertables for time-series data
- **Seed Scripts**: Database seeding with Python

### 📊 Added - Data Pipeline System
- **Orchestrator**: 8-stage pipeline (Discover → Fetch → Verify → Parse → Transform → Crossref → Store → Index)
- **Queue Manager**: Priority queues with game isolation
- **Agent Manager**: Worker lifecycle & health monitoring
- **Conflict Resolver**: Deduplication & content drift detection
- **Rate Limiter**: Per-source rate limiting
- **Scheduler**: Cron/webhook/manual triggers
- **Monitoring**: Prometheus-compatible metrics

### 🎯 Added - Dual-Game Collection
- **CS Extractor**: HLTV.org integration
- **Valorant Extractor**: VLR.gg integration
- **Agent Workers**: Async extraction workers
- **Database Partitioning**: Game-specific tables
- **Conflict Prevention**: Distributed locking, checksum validation

### 📈 Added - Developer Dashboard
- **System Monitoring**: 7-layer architecture
  - Infrastructure, API Services, Data Pipeline
  - Web Platform, Simulation, Security, External
- **Health Checks**: Database, API, Pipeline, Website collectors
- **Alert Manager**: Rule-based alerting with auto-resolution
- **Maintenance Scheduler**: Scheduled windows with notifications
- **CLI Tools**: Dashboard, maintenance, alerts management

### 📚 Added - Documentation
- **AGENTS.md**: Comprehensive project guide for AI agents
- **DEPLOYMENT_ARCHITECTURE.md**: Free-tier deployment guide
- **DEPLOYMENT_CHECKLIST.md**: Step-by-step deployment checklist
- **DUAL_GAME_ARCHITECTURE.md**: CS + Valorant collection architecture
- **SKILL_ARCHITECTURE_ANALYSIS.md**: Kimi skill system design

### 🔒 Added - Security
- **Data Partition Firewall**: 3 enforcement points
  - Game export (GDScript)
  - API middleware (Python)
  - Schema validation (TypeScript)
- **GAME_ONLY_FIELDS**: 8 blocked fields (internalAgentState, radarData, etc.)

### 🧪 Added - Testing
- **Integration Tests**: End-to-end pipeline tests
- **Firewall Tests**: Security validation
- **Determinism Tests**: Godot simulation tests

## [1.0.0] - Initial Release

### Added
- SATOR eXe platform foundation
- RadiantX Valorant dashboard
- Static website (HTML/CSS/JS)
- Basic CI/CD workflows

## Migration Guide

### From v1.0 to Unreleased
1. Apply new database migrations (001-009)
2. Set up new environment variables (see .env.example files)
3. Deploy FastAPI to Render
4. Deploy React app to Vercel
5. Configure GitHub Actions secrets

## Deprecated
- N/A

## Removed
- N/A

## Fixed
- N/A

## Security
- Implemented data partition firewall
- Added rate limiting
- Secured API endpoints
