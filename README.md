# SES Email Sender

A terminal-based email sending application powered by AWS SES, with a FastAPI backend and React-based TUI (Terminal User Interface).

![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Quick Start

```bash
# 1. Clone and install
git clone git@github.com:rish-kun/ses-emailer.git
cd ses-emailer

# 2. Install Python dependencies
uv sync

# 3. Install TypeScript dependencies
cd ts-tui && bun install && cd ..

# 4. Run the application
uv run python start.py
```

## Configuration

On first launch, go to **Settings** (`S` key) to configure:

1. **AWS Credentials** — Access Key, Secret Key, Region, Source Email
2. **Sender Settings** — Display name, Reply-To, Default TO address
3. **Batch Settings** — Batch size, delay between batches
4. **Test Recipients** — Pre-configured test email addresses

### Multiple Profiles

Create named profiles for different environments (production, staging, testing). Switch between profiles from the Settings screen.

Settings are stored in `config/settings.json` (excluded from git).

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit |
| `Ctrl+H` | Go to Home |
| `C` | Compose Email |
| `S` | Settings |
| `H` | History |
| `D` | Drafts |
| `Esc` | Back / Cancel |
| `↑↓` | Navigate lists |
| `Enter` | Select / Confirm |

## Architecture

```
┌──────────────────┐       HTTP/SSE        ┌──────────────────┐
│  TypeScript TUI  │ ◄──────────────────── │  FastAPI Backend  │
│  (Ink + React)   │     Bearer Token      │  (Python)         │
└──────────────────┘                       └──────────────────┘
        │                                           │
        │  start.py orchestrates both               │
        └───────────────────────────────────────────┘
```

- **Backend** (`api/`): FastAPI REST API wrapping the email sending, config management, and SQLite database operations
- **TUI** (`ts-tui/`): React-based terminal interface using [Ink](https://github.com/vadimdemedes/ink) and [@inkjs/ui](https://github.com/vadimdemedes/ink-ui)
- **Orchestrator** (`start.py`): Generates a one-time auth token, spawns both processes, handles cleanup

## Features

- 📧 **Compose Emails** — HTML or plain text with rich preview
- 📋 **Excel Import** — Load recipient lists from `.xlsx` files
- 📊 **Batch Sending** — Configurable batch size with rate limiting and real-time SSE progress
- 📜 **History** — Campaign list with search, stats, and detail views
- 📝 **Drafts** — Save and load email drafts
- ⚙️ **Multi-Profile Config** — Named configuration profiles for different AWS accounts/environments
- 🔒 **Secure** — Auto-generated Bearer token authentication between TUI and API
- 📄 **React Email Templates** — Use `.tsx` files for beautiful emails

## React Email Templates

Create email templates using React Email components.

### Adding Templates

1. Create `.tsx` files in `templates/` directory
2. First time: `cd templates && bun install`
3. Templates auto-detect — restart app to see new ones

### Template Example

```tsx
import { Html, Head, Body, Container, Text } from '@react-email/components';

export default function MyTemplate() {
  return (
    <Html>
      <Head />
      <Body>
        <Container>
          <Text>Your content here</Text>
        </Container>
      </Body>
    </Html>
  );
}
```

### Using Templates

- Press `Meta+2` in Compose screen to open Template tab
- Select from available templates (Welcome, Newsletter included)
- Preview renders automatically in the app

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Bun](https://bun.sh/) (TypeScript runtime)
- AWS SES account with verified sender email

## Project Structure

```
ses-emailer/
├── api/                    # FastAPI backend
│   ├── main.py             # App entry + CORS + health check
│   ├── auth.py             # Bearer token auth
│   └── routers/            # API endpoints
│       ├── config.py       # Config + profile management
│       ├── email.py        # Sending + file uploads
│       ├── history.py      # Campaign history
│       ├── drafts.py       # Draft CRUD
│       └── db.py           # DB management
├── ts-tui/                 # TypeScript TUI
│   ├── src/
│   │   ├── index.tsx       # Entry point
│   │   ├── App.tsx         # Router + layout
│   │   ├── api.ts          # API client
│   │   └── screens/        # UI screens
│   └── package.json
├── sending/                # Email logic (shared)
│   ├── db.py               # SQLite ORM
│   ├── emails.py           # MIME builder
│   ├── senders.py          # SES sender
│   └── email_list.py       # Excel parser
├── config/                 # Configuration
│   └── settings.py         # Multi-profile manager
├── start.py                # Orchestrator
└── pyproject.toml
```

## API Endpoints

All endpoints (except `/health`) require `Authorization: Bearer <token>`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/api/config` | Active profile config |
| PUT | `/api/config` | Update config |
| GET | `/api/config/profiles` | List profiles |
| POST | `/api/config/profiles` | Create profile |
| DELETE | `/api/config/profiles/{name}` | Delete profile |
| POST | `/api/config/profiles/{name}/activate` | Switch profile |
| POST | `/api/emails/send` | Send emails (SSE stream) |
| POST | `/api/emails/upload-excel` | Upload Excel |
| POST | `/api/emails/compare` | Compare recipients |
| GET | `/api/history` | List campaigns |
| GET | `/api/history/{id}` | Campaign detail |
| GET | `/api/history/stats` | Statistics |
| GET/POST/PUT/DELETE | `/api/drafts[/id]` | Draft CRUD |

## License

MIT License