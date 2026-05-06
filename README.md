# intel-agent

Agregador de inteligencia personal que corre en una Raspberry Pi 4.
Recolecta datos de APIs públicas y webs, los procesa con un LLM local
y los almacena para consultarlos cuando quieras desde cualquier dispositivo
de tu red Tailscale.

## Idea general

En vez de abrir decenas de pestañas cada día para estar al día, la raspi
lo hace por ti en segundo plano. El LLM resume y clasifica cada item antes
de guardarlo, así cuando consultas ya tienes la información digerida.

```
Fuentes externas  →  Scheduler  →  LLM local  →  PostgreSQL  →  Web UI
(cada X horas)         (APScheduler)  (Ollama / gemma2:2b)        (Tailscale)
```

## Fuentes integradas

| Fuente | Categoría | API key |
|--------|-----------|---------|
| HackerNews | Tech | No |
| GitHub | Tech | Free |
| arXiv | Tech | No |
| TMDB | Entretenimiento | Free |
| RAWG | Entretenimiento | Free |
| Last.fm | Entretenimiento | Free |

## Stack

| Capa | Tecnología |
|------|-----------|
| Recolección | Python 3.11 + httpx + APScheduler |
| Procesado | Ollama + gemma2:2b |
| Base de datos | PostgreSQL 16 |
| API / UI | FastAPI |
| Infraestructura | Docker Compose |
| Acceso remoto | Tailscale (sin puertos abiertos) |

## Requisitos

- Docker y Docker Compose
- Python 3.11+ (solo para desarrollo local)
- Cuenta en Tailscale (para acceso remoto a la raspi)

## Setup

### 1. Clonar y configurar variables de entorno

```bash
git clone <repo>
cd intel-agent
cp .env.example .env
```

Editar `.env` con tus API keys:

```env
DB_PASSWORD=tu-password-seguro

# APIs (las que no tienen key se dejan vacías)
GITHUB_TOKEN=ghp_...
TMDB_API_KEY=...
RAWG_API_KEY=...
LASTFM_API_KEY=...
```

### 2. Arrancar en local (desarrollo)

```bash
docker compose up db ollama
# En otro terminal:
cd collector && pip install -r requirements.txt
python main.py
```

### 3. Desplegar en la raspi

```bash
# Desde tu PC, copiar el proyecto a la raspi
rsync -av --exclude='.git' ./ pi@<tailscale-ip>:~/intel-agent/

# En la raspi
cd intel-agent
docker compose up -d
```

### 4. Primer arranque de Ollama

```bash
docker compose exec ollama ollama pull gemma2:2b
```

## Schema de base de datos

```sql
sources   — fuentes configuradas (HN, GitHub, TMDB...)
items     — items recolectados y procesados por el LLM
digests   — resúmenes diarios generados automáticamente
```

Ver `db/init.sql` para el schema completo.

## API endpoints

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Web UI de consulta |
| `/api/items` | GET | Lista items con filtros |
| `/api/items/search` | POST | Búsqueda semántica |
| `/api/digest/today` | GET | Digest del día |
| `/api/sources` | GET | Estado de las fuentes |

## Estructura del proyecto

```
intel-agent/
├── collector/
│   ├── sources/        # Un fichero por fuente
│   │   ├── hn.py
│   │   ├── github.py
│   │   ├── arxiv.py
│   │   ├── tmdb.py
│   │   ├── rawg.py
│   │   └── lastfm.py
│   ├── processor.py    # Integración con Ollama
│   ├── scheduler.py    # Jobs periódicos
│   └── main.py
├── api/
│   ├── routes/
│   │   ├── items.py
│   │   └── digest.py
│   └── main.py
├── db/
│   └── init.sql
├── docker-compose.yml
├── .env.example
├── README.md
└── CLAUDE.md
```

## Licencia

MIT
