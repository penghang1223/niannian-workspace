# OpenClaw Status Line

A beautiful and functional status bar system for OpenClaw, inspired by ccstatusline but built specifically for OpenClaw's needs.

## Features

- **Token Usage Tracking**: Monitor your token consumption in real-time
- **Session Clock**: Track how long your current session has been running
- **Project Context**: See which project you're currently working on
- **Cost Tracking**: Estimate your API costs for the session
- **Git Integration**: Display your current git branch
- **Agent Status**: Show active agents and their status
- **Model Information**: Display the current model being used

## Architecture

```
openclaw-statusline/
├── src/
│   ├── openclaw-statusline.ts  # Main entry point
│   ├── tui/                    # TUI components (future)
│   ├── widgets/                # Individual status components
│   │   ├── Agent.ts           # Agent status widget
│   │   ├── Model.ts           # Model information widget
│   │   ├── Tokens.ts          # Token usage widget
│   │   ├── Cost.ts            # Cost tracking widget
│   │   ├── SessionClock.ts    # Session duration widget
│   │   ├── GitBranch.ts       # Git branch widget
│   │   └── Project.ts         # Project context widget
│   └── utils/
│       ├── config.ts          # Configuration management
│       ├── renderer.ts        # Rendering utilities
│       └── colors.ts          # Color utilities
```

## Installation

```bash
npm install openclaw-statusline
```

## Usage

```bash
# Run directly
npx openclaw-statusline

# Or build and run
npm run build
npm start
```

## Configuration

Create a `openclaw-statusline.json` file in your project root to customize:

```json
{
  "refreshInterval": 1000,
  "showCost": true,
  "showGit": true,
  "showAgent": true,
  "showModel": true,
  "theme": "default",
  "position": "bottom",
  "separator": " | ",
  "colors": {
    "token": "#00ff00",
    "clock": "#ffff00",
    "project": "#ff00ff",
    "cost": "#00ffff",
    "git": "#ffa500",
    "agent": "#ff0000",
    "model": "#800080"
  }
}
```

## Widgets

Each widget is designed to be modular and extensible:

- **Tokens**: Tracks token usage across different models and sessions
- **SessionClock**: Shows the duration of the current session
- **Project**: Displays the current project context
- **Cost**: Estimates API costs for the session
- **GitBranch**: Shows the current git branch
- **Agent**: Displays active agent status
- **Model**: Shows the current model being used

## Future Enhancements

- Interactive TUI configuration interface
- More advanced metrics (token speed, context monitoring)
- Custom widget support
- Integration with OpenClaw's plugin system
- Enhanced theming options

## License

MIT