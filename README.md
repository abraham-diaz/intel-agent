# intel-agent

Personal intelligence aggregator running on a Raspberry Pi 4.
Pulls data from public APIs, stores items in PostgreSQL, and delivers
a curated feed through a private Telegram bot — no open ports, no cloud dependency.

```
External APIs  →  Scheduler  →  PostgreSQL  →  Telegram bot
(every N hours)   (APScheduler)               (private, polling)
```

## Data sources

| Source | Category | API key |
|--------|----------|---------|
| HackerNews | tech-other | No |
| GitHub | tech-infra | Free |
| arXiv | tech-ai | No |
| TMDB | film-tv | Free |
| RAWG | gaming | Free |
| Last.fm | music | Free |

## Stack

| Layer | Technology |
|-------|-----------|
| Collection | Python 3.11 + httpx + APScheduler |
| Database | PostgreSQL 16 |
| Interface | Telegram bot (python-telegram-bot) |
| Infrastructure | Docker Compose |
| Remote access | Tailscale (no open ports) |

## Bot commands

| Command | Description |
|---------|-------------|
| `/hoy` | Today's digest grouped by category |
| `/tech` | Latest tech items (AI, infra, other) |
| `/gaming` | Latest gaming items |
| `/music` | Latest music trends |
| `/films` | Latest movies and TV shows |
| `/buscar <text>` | Search items by title |
| `/estado` | Last run time for each source |

Each item shows the title as a clickable link, a short description scraped from
the article's meta tags, the source (HN, GitHub, arXiv…) and relative time.

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

# Optional — sources without a key are skipped
GITHUB_TOKEN=ghp_...
TMDB_API_KEY=...
RAWG_API_KEY=...
LASTFM_API_KEY=...

# Items older than this are deleted automatically
ITEM_TTL_DAYS=7
```

### 2. Start services

```bash
docker compose up -d
```

### 3. Check everything is running

```bash
docker compose logs collector --tail 30
docker compose logs bot --tail 20
```

## Project structure

```
intel-agent/
├── collector/
│   ├── sources/        # One file per source
│   │   ├── hn.py       # Fetches top stories + scrapes meta descriptions
│   │   ├── github.py
│   │   ├── arxiv.py
│   │   ├── tmdb.py
│   │   ├── rawg.py
│   │   └── lastfm.py
│   ├── scheduler.py    # Periodic jobs + daily cleanup
│   └── main.py
├── bot/
│   ├── db.py
│   └── main.py
├── db/
│   └── init.sql
├── docker-compose.yml
└── .env.example
```

## Collection intervals

| Source | Interval |
|--------|----------|
| HackerNews | Every 2h |
| GitHub | Every 6h |
| Last.fm | Every 6h |
| arXiv | Every 12h |
| TMDB | Every 24h |
| RAWG | Every 24h |
| Cleanup (delete old items) | Every 24h |

## Database schema

```
sources   — registered sources with last run timestamp
items     — collected items with title, url, description and category
digests   — daily digests (reserved for future use)
```

## License

MIT
