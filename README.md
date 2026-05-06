# intel-agent

Personal intelligence aggregator running on a Raspberry Pi 4.
Pulls data from public APIs, processes each item with a local LLM, and delivers
a daily digest through a private Telegram bot — no open ports, no cloud dependency.

```
External APIs  →  Scheduler  →  Local LLM  →  PostgreSQL  →  Telegram bot
(every N hours)   (APScheduler)  (Ollama / gemma2:2b)         (private, polling)
```

## Data sources

| Source | Category | API key |
|--------|----------|---------|
| HackerNews | Tech | No |
| GitHub | Tech | Free |
| arXiv | Tech | No |
| TMDB | Entertainment | Free |
| RAWG | Entertainment | Free |
| Last.fm | Entertainment | Free |

## Stack

| Layer | Technology |
|-------|-----------|
| Collection | Python 3.11 + httpx + APScheduler |
| Processing | Ollama + gemma2:2b |
| Database | PostgreSQL 16 |
| Interface | Telegram bot (python-telegram-bot) |
| Infrastructure | Docker Compose |
| Remote access | Tailscale (no open ports) |

## Setup

### 1. Clone and configure

```bash
git clone <repo>
cd intel-agent
cp .env.example .env
```

Edit `.env` with your credentials:

```env
DB_PASSWORD=your-secure-password

# Telegram — get token from @BotFather, user ID from @userinfobot
TELEGRAM_TOKEN=...
TELEGRAM_ALLOWED_USER_ID=123456789

# Optional API keys (sources without a key are skipped)
GITHUB_TOKEN=ghp_...
TMDB_API_KEY=...
RAWG_API_KEY=...
LASTFM_API_KEY=...
```

### 2. Start services

```bash
docker compose up -d
```

### 3. Pull the LLM model (first run only)

```bash
docker compose exec ollama ollama pull gemma2:2b
```

### 4. Check everything is running

```bash
docker compose logs collector --tail 30
docker compose logs bot --tail 30
```

## Bot commands

| Command | Description |
|---------|-------------|
| `/hoy` | Today's digest grouped by category |
| `/tech` | Latest tech items (AI, frontend, infra) |
| `/gaming` | Latest gaming items |
| `/music` | Latest music trends |
| `/films` | Latest movies and TV shows |
| `/buscar <text>` | Search items by title |
| `/estado` | Last run time for each source |

## Project structure

```
intel-agent/
├── collector/
│   ├── sources/        # One file per source
│   │   ├── hn.py
│   │   ├── github.py
│   │   ├── arxiv.py
│   │   ├── tmdb.py
│   │   ├── rawg.py
│   │   └── lastfm.py
│   ├── processor.py    # Ollama integration
│   ├── scheduler.py    # Periodic jobs
│   └── main.py
├── bot/
│   ├── config.py
│   ├── db.py
│   └── main.py
├── db/
│   └── init.sql
├── docker-compose.yml
└── .env.example
```

## Database schema

```
sources   — registered sources with last run timestamp
items     — collected items with LLM-generated summary, category and tags
digests   — daily digests (auto-generated)
```

## License

MIT
