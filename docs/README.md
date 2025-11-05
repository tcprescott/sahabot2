# SahaBot2 Documentation

Welcome to the SahaBot2 documentation! This directory contains all technical documentation, guides, and references for developers and administrators.

## 📚 Documentation Index

### 🎯 Getting Started

Start here if you're new to the codebase:

1. **[Architecture Guide](ARCHITECTURE.md)** - System architecture and component overview
2. **[Patterns & Conventions](PATTERNS.md)** - Code patterns and best practices
3. **[Adding Features Guide](ADDING_FEATURES.md)** - Step-by-step guides for common tasks

### 🏗️ Core Development Guides

Essential guides for UI and frontend development:

- **[BasePage Guide](core/BASEPAGE_GUIDE.md)** - Using the BasePage template for pages
- **[Components Guide](core/COMPONENTS_GUIDE.md)** - Reusable UI components
- **[Dialog Action Row Pattern](core/DIALOG_ACTION_ROW_PATTERN.md)** - Dialog button layout pattern
- **[JavaScript Guidelines](core/JAVASCRIPT_GUIDELINES.md)** - JavaScript organization and patterns

### ⚙️ System Documentation

Backend systems and architecture:

- **[Event System](systems/EVENT_SYSTEM.md)** - Async event bus and notification system
- **[Notification System](systems/NOTIFICATION_SYSTEM.md)** - Discord notification handlers
- **[Task Scheduler](systems/TASK_SCHEDULER.md)** - Background task scheduling
- **[Built-in Tasks](systems/BUILTIN_TASKS.md)** - Reference for built-in scheduled tasks

### 🔌 Integration Guides

External service integrations:

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

### 📖 Reference

Quick reference documentation:

- **[API Documentation](reference/API_SWAGGER_GUIDE.md)** - Using the Swagger API docs
- **[Known Issues](reference/KNOWN_ISSUES.md)** - Current known issues and workarounds

### 📋 Planning & Analysis

Current planning and reorganization documents:

- **[Copilot Instructions Reorganization](COPILOT_INSTRUCTIONS_REORGANIZATION.md)** - Plan for streamlining copilot instructions
- **[Documentation Cleanup Analysis](DOCS_CLEANUP_ANALYSIS.md)** - Analysis of documentation reorganization

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
