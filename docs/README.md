# SahaBot2 Documentation

Welcome to the SahaBot2 documentation! This directory contains all technical documentation, guides, and references for developers and administrators.

## 📚 Documentation Index

### 🎯 Getting Started

Start here if you're new to the codebase:

1. **[Architecture Guide](ARCHITECTURE.md)** - System architecture and component overview
2. **[Patterns & Conventions](PATTERNS.md)** - Code patterns and best practices
3. **[Adding Features Guide](ADDING_FEATURES.md)** - Step-by-step guides for common tasks

### 🏗️ Core Development Guides

Essential guides for UI, backend, and architecture development:

- **[BasePage Guide](core/BASEPAGE_GUIDE.md)** - Using the BasePage template for pages
- **[Components Guide](core/COMPONENTS_GUIDE.md)** - Reusable UI components
- **[Dialog Action Row Pattern](core/DIALOG_ACTION_ROW_PATTERN.md)** - Dialog button layout pattern
- **[JavaScript Guidelines](core/JAVASCRIPT_GUIDELINES.md)** - JavaScript organization and patterns
- **[Repository Pattern Guide](core/REPOSITORIES_PATTERN.md)** - Data access layer patterns and examples

### ⚙️ System Documentation

Backend systems and architecture:

- **[Event System](systems/EVENT_SYSTEM.md)** - Async event bus and notification system
- **[Notification System](systems/NOTIFICATION_SYSTEM.md)** - Discord notification handlers
- **[Task Scheduler](systems/TASK_SCHEDULER.md)** - Background task scheduling
- **[Built-in Tasks](systems/BUILTIN_TASKS.md)** - Reference for built-in scheduled tasks

### 🚀 Operations & Deployment

Deployment, configuration, and troubleshooting:

- **[Environment Variables Reference](reference/ENVIRONMENT_VARIABLES.md)** - Complete configuration reference
- **[Troubleshooting Guide](operations/TROUBLESHOOTING_GUIDE.md)** - Common issues and debugging procedures
- **[Deployment Guide](operations/DEPLOYMENT_GUIDE.md)** - Production deployment, scaling, and operations

### 🔌 Integration Guides

External service integrations:

- **[Discord OAuth2 Token Refresh](integrations/DISCORD_TOKEN_REFRESH.md)** - Automatic token refresh implementation
- **[RaceTime.gg Integration](integrations/RACETIME_INTEGRATION.md)** - RaceTime.gg API integration
- **[RaceTime Chat Commands](integrations/RACETIME_CHAT_COMMANDS_QUICKSTART.md)** - Bot commands quick reference
- **[Discord Channel Permissions](integrations/DISCORD_CHANNEL_PERMISSIONS.md)** - Required Discord permissions
- **[Discord Scheduled Events](integrations/DISCORD_SCHEDULED_EVENTS.md)** - Discord event integration

### 👥 User & Admin Guides

End-user and administrator documentation:

#### Admin Guides
- **[Live Races Admin Guide](guides/admin/LIVE_RACES.md)** - Managing live race features

#### User Guides
- **[Async Tournaments Guide](guides/user/ASYNC_TOURNAMENT_END_USER_GUIDE.md)** - End user tournament guide
- **[Live Races User Guide](guides/user/USER_GUIDE_LIVE_RACES.md)** - Using live race features

### Reference

Quick reference documentation:

- **[Services Reference](reference/SERVICES_REFERENCE.md)** - Complete reference for all 33 services with methods and examples
- **[API Endpoints Reference](reference/API_ENDPOINTS_REFERENCE.md)** - All 65+ REST endpoints with parameters and responses
- **[Database Models Reference](reference/DATABASE_MODELS_REFERENCE.md)** - All 30+ models with fields, relationships, and indexes
- **[API Documentation](reference/API_SWAGGER_GUIDE.md)** - Using the Swagger API docs
- **[Known Issues](reference/KNOWN_ISSUES.md)** - Current known issues and workarounds

### ✨ Phase 1 Documentation Initiative

Phase 1 documentation initiative completed with 8 comprehensive reference guides and planning documents.

#### 📖 Reference Documentation (8 Documents - 13,000+ Lines)
- **[SERVICES_REFERENCE.md](reference/SERVICES_REFERENCE.md)** - All 33 services with methods, patterns, and examples
- **[API_ENDPOINTS_REFERENCE.md](reference/API_ENDPOINTS_REFERENCE.md)** - All 65+ REST endpoints with parameters and responses
- **[DATABASE_MODELS_REFERENCE.md](reference/DATABASE_MODELS_REFERENCE.md)** - All 30+ ORM models with relationships
- **[ENVIRONMENT_VARIABLES.md](reference/ENVIRONMENT_VARIABLES.md)** - All 18 environment variables and configuration
- **[REPOSITORIES_PATTERN.md](core/REPOSITORIES_PATTERN.md)** - All 15+ repository patterns with CRUD examples
- **[TROUBLESHOOTING_GUIDE.md](operations/TROUBLESHOOTING_GUIDE.md)** - 50+ troubleshooting scenarios and solutions
- **[DEPLOYMENT_GUIDE.md](operations/DEPLOYMENT_GUIDE.md)** - Complete deployment lifecycle for all environments

#### 📊 Phase 1 Summary & Review Documents
- **[Phase 1 Visual Summary](PHASE_1_VISUAL_SUMMARY.md)** - At-a-glance overview with charts and statistics
- **[Phase 1 Completion Summary](PHASE_1_COMPLETION_SUMMARY.md)** - Detailed summary of deliverables and metrics
- **[Phase 1 Quick Reference](PHASE_1_QUICK_REFERENCE.md)** - Navigation shortcuts and "I need to..." paths
- **[Phase 1 Review Checklist](PHASE_1_REVIEW_CHECKLIST.md)** - How to review and provide feedback

#### 📋 Documentation Analysis (Pre-Phase 1)
- **[Documentation Gap Analysis](DOCUMENTATION_GAP_ANALYSIS.md)** - Analysis of missing/incomplete documentation
- **[Documentation Gap Summary](DOCUMENTATION_GAP_SUMMARY.md)** - Executive summary with priorities
- **[Documentation Checklist](DOCUMENTATION_CHECKLIST.md)** - Tracking checklist (100+ items)

### 📋 Planning & Analysis

Current planning and reorganization documents:

- **[Copilot Instructions Reorganization](COPILOT_INSTRUCTIONS_REORGANIZATION.md)** - Plan for streamlining copilot instructions
- **[Documentation Cleanup Analysis](DOCS_CLEANUP_ANALYSIS.md)** - Analysis of documentation reorganization
- **[Documentation Gap Analysis](DOCUMENTATION_GAP_ANALYSIS.md)** - Comprehensive analysis of all undocumented services, APIs, and models
- **[Documentation Checklist](DOCUMENTATION_CHECKLIST.md)** - Complete tracking list for documentation work (100+ items to document)

### 📦 Archive

Historical documentation (completed implementations, migrations, and analyses):

- **[archive/completed/](archive/completed/)** - Completed implementation and refactoring docs
- **[archive/migrations/](archive/migrations/)** - Historical migration plans
- **[archive/analysis/](archive/analysis/)** - One-time analysis documents

## 🚀 Quick Links

### For New Developers
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
2. Review [PATTERNS.md](PATTERNS.md) for coding conventions
3. Use [ADDING_FEATURES.md](ADDING_FEATURES.md) as a reference when building features

### For UI Development
- Start with [BasePage Guide](core/BASEPAGE_GUIDE.md)
- Reference [Components Guide](core/COMPONENTS_GUIDE.md) for reusable UI elements
- Follow [JavaScript Guidelines](core/JAVASCRIPT_GUIDELINES.md) for frontend code

### For Backend Development
- Understand the [Event System](systems/EVENT_SYSTEM.md)
- Learn the [Notification System](systems/NOTIFICATION_SYSTEM.md)
- Reference [Task Scheduler](systems/TASK_SCHEDULER.md) for background jobs

### For Integration Work
- RaceTime.gg: [Integration Guide](integrations/RACETIME_INTEGRATION.md)
- Discord: [Channel Permissions](integrations/DISCORD_CHANNEL_PERMISSIONS.md) and [Scheduled Events](integrations/DISCORD_SCHEDULED_EVENTS.md)

## 📝 Documentation Standards

When creating or updating documentation:

1. **Be concise**: Get to the point quickly
2. **Use examples**: Show code, not just descriptions
3. **Keep it current**: Update docs when code changes
4. **Link related docs**: Help readers find related information
5. **Use proper markdown**: Headers, code blocks, lists, etc.

## 🤝 Contributing to Documentation

Found outdated documentation? See something missing?

1. Update the relevant file
2. Keep the same format and style
3. Test any code examples
4. Update the index (this file) if adding new docs

---

**Last Updated**: November 4, 2025
