# WorkmAIn - Work Management AI

An intelligent personal work management system that captures notes, tracks time, and generates AI-powered reports.

## Features

- 📝 Smart note capture with tagging
- ⏱️ Time tracking with Clockify integration
- 🤖 AI-powered report generation (Claude & Gemini)
- 📊 Automated daily and weekly reports
- 🔔 Smart notifications and reminders
- 🔗 Integrations: Google Docs, Outlook, Slack, Clockify

## Quick Start
```bash
# Install
pip install -r requirements.txt
pip install -e .

# Start using
workmain notes add "Completed security audit" -t cr
workmain time add "Bug fix" 2h -T 1430
workmain reports preview daily_internal
```

## Documentation

See [docs/setup_guide.md](docs/setup_guide.md) for detailed setup instructions.

## License

MIT License
