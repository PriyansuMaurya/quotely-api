# Quotely API

A production-shaped FastAPI service for motivational quotes, built on the
[Quotely](https://pypi.org/project/quotely/) library.

[![CI](https://github.com/PriyansuMaurya/quotely-api/actions/workflows/ci.yml/badge.svg)](https://github.com/PriyansuMaurya/quotely-api/actions/workflows/ci.yml)

- **Random quotes** — one quote per call, optionally restricted to an author.
- **Filtered listing** — paginated quotes, filterable by author.
- **Health** — status, version, uptime and catalogue size.
- **Interactive documentation** — Swagger UI at `/docs`, ReDoc at `/redoc`.

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (the pinned interpreter comes from
`.python-version`).

```bash
uv sync                                  # install dependencies from uv.lock
uv run uvicorn app.main:app --reload     # serve on http://127.0.0.1:8000
```

Then open <http://127.0.0.1:8000/docs>.

## Frontend

A SvelteKit client lives in [`frontend/`](frontend/). It shows one random quote
with its author and refreshes on demand.

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

It calls this API, so the API must allow the frontend's origin. Locally the
defaults already cover `localhost:5173` (dev) and `localhost:4173` (preview). For
a deployed frontend, set:

```
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

on the Render service — comma-separate multiple origins. See
[`frontend/README.md`](frontend/README.md) for deployment steps.

## Endpoints

| Method | Path                        | Description                                     |
| ------ | --------------------------- | ----------------------------------------------- |
| `GET`  | `/api/v1/quotes/random`     | One random quote, optional `author` filter.     |
| `GET`  | `/api/v1/quotes`            | Paginated quotes, optional `author` filter.     |
| `GET`  | `/health`                   | Status, version, uptime and catalogue size.     |
| `GET`  | `/`                         | Service index with documentation links.         |
| `GET`  | `/docs`, `/redoc`           | Interactive API documentation.                  |
| `GET`  | `/openapi.json`             | The OpenAPI schema.                             |

### Examples

```bash
# A random quote
curl http://127.0.0.1:8000/api/v1/quotes/random
```

```json
{
  "text": "It always seems impossible until it's done.",
  "author": "Nelson Mandela",
  "quote": "\"It always seems impossible until it's done.\" - Nelson Mandela"
}
```

```bash
# A random quote from one author (case-insensitive, exact match)
curl "http://127.0.0.1:8000/api/v1/quotes/random?author=nelson%20mandela"

# A page of quotes, filtered by author
curl "http://127.0.0.1:8000/api/v1/quotes?author=Albert%20Einstein&limit=5&offset=0"
```

```json
{
  "items": [
    {
      "text": "Imagination is more important than knowledge.",
      "author": "Albert Einstein",
      "quote": "\"Imagination is more important than knowledge.\" - Albert Einstein"
    }
  ],
  "total": 22,
  "limit": 5,
  "offset": 0
}
```

### Parameters

| Parameter | Applies to   | Rules                                                       |
| --------- | ------------ | ----------------------------------------------------------- |
| `author`  | both quote endpoints | Case-insensitive, exact match. Surrounding whitespace ignored. |
| `limit`   | `/quotes`    | Integer, `1`–`100`, default `20`.                            |
| `offset`  | `/quotes`    | Integer, `>= 0`, default `0`.                                |

An unknown author returns an **empty page** from `/quotes` (the collection exists,
it just has no members) and a **404** from `/quotes/random` (there is no quote to
return).

## Response behaviour

**Every response carries an `X-Request-ID` header.** A value supplied by the caller
is reused when it matches `[A-Za-z0-9._-]{1,64}`; anything else is replaced, so
header content cannot be injected into the logs.

**Errors use two shapes, deliberately.**

Handled client errors keep FastAPI's native body, because that is what the
generated OpenAPI schema documents:

```json
{ "detail": "No quotes found for author 'Nobody'" }
```

Validation failures likewise return FastAPI's native `422` with a `detail` list.

Only unhandled server errors — which have no documented schema — use an envelope
with a stable code and the request id, without leaking internals:

```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected error occurred.",
    "request_id": "4f8c1a2b9d7e4c6a"
  }
}
```

Logs are one JSON object per line on stdout, carrying the same `request_id`:

```json
{"timestamp": "2026-10-30T18:22:41.512+00:00", "level": "INFO", "logger": "app.request", "message": "request completed", "request_id": "4f8c1a2b9d7e4c6a", "method": "GET", "path": "/api/v1/quotes/random", "status_code": 200, "duration_ms": 1.87}
```

## Configuration

All configuration is environment-driven, with working defaults:

| Variable            | Default              | Purpose                                          |
| ------------------- | -------------------- | ------------------------------------------------ |
| `ENVIRONMENT`       | `development`        | Reported by `/health`.                           |
| `LOG_LEVEL`         | `INFO`               | Root log level.                                  |
| `APP_NAME`          | `Quotely API`        | OpenAPI title.                                   |
| `QUOTES_DATA_FILE`  | `data/quotes.json`   | Path to the quote catalogue.                     |
| `DEFAULT_PAGE_SIZE` | `20`                 | Default `limit`.                                 |
| `MAX_PAGE_SIZE`     | `100`                | Maximum accepted `limit`.                        |

## Project structure

```
app/
├── main.py              # application factory, router wiring, lifespan logging
├── config.py            # environment-driven settings
├── models.py            # Pydantic schemas (also the OpenAPI contract)
├── quote_service.py     # eager catalogue load + query functions
├── errors.py            # exception handlers (native 4xx, enveloped 500)
├── logging_config.py    # JSON log formatter and request-id context
├── middleware/
│   └── request_id.py    # request id assignment, timing, access logging
└── routers/
    ├── quotes.py        # /quotes and /quotes/random
    └── health.py        # /health
data/quotes.json         # committed snapshot of the Quotely catalogue
scripts/sync_quotes.py   # regenerates that snapshot
tests/                   # pytest suite
frontend/                # SvelteKit client (see frontend/README.md)
```

## Data: the Quotely library and the snapshot

Quotely's public API returns a random quote (`get_random_quote()`, plus the
`random(quote)` helpers) but offers **no way to enumerate or filter the
catalogue**. Its data lives in `quotely.core.ALL_QUOTES`, a private symbol outside
`__all__`.

This service therefore uses both sources on purpose:

- `/quotes/random` **without** a filter calls Quotely's public `get_random_quote()`,
  keeping the library the runtime source of truth for the random endpoint.
- The list and author-filter endpoints read `data/quotes.json`, a committed
  snapshot generated from Quotely's catalogue.
- `tests/test_snapshot.py` asserts the committed snapshot equals the installed
  library's data, so the two cannot drift silently.

Regenerate the snapshot after upgrading Quotely:

```bash
uv run python -m scripts.sync_quotes
```

### Two caveats worth knowing

- **The dataset is vendored into this repository.** That copies Quotely's 508
  quotes (and their attributions) into this project rather than importing them at
  request time. Some attributions in public quote collections are contested or
  misattributed; the data is used as published by the library and is not
  independently verified here.
- **`ALL_QUOTES` is private.** Only `scripts/sync_quotes.py` and the drift test
  reference it, and both fail loudly if a future release moves or removes it. The
  running service never touches it.

## Testing

```bash
uv run pytest              # 43 tests
uv run pytest -v           # per-test output
```

The suite covers response shape, author filtering and its case-insensitivity,
pagination including out-of-range offsets, validation failures, request-id
propagation and sanitisation, the unhandled-error envelope, the served docs and
schema, snapshot integrity, and the drift check against Quotely.

## Deployment

### Render

[`render.yaml`](render.yaml) is a complete blueprint: free plan, Oregon region,
automatic deploys from `main`, health checks against `/health`.

- **Build:** `pip install uv && uv sync --frozen --no-dev`
- **Start:** `uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port $PORT`

`--frozen` fails the build if `uv.lock` disagrees with `pyproject.toml`, so
production can never resolve versions that differ from CI. `--no-dev` keeps test
dependencies out of the running image.

To deploy: Render Dashboard → **New** → **Blueprint** → select this repository.
Change the region or plan in `render.yaml` if needed.

**The free tier sleeps after 15 minutes of inactivity.** The first request after
idling takes up to a minute while the instance boots — that is the plan, not a
defect. Upgrade the plan if that latency matters.

### Keeping the free tier awake

[`.github/workflows/keep-alive.yml`](.github/workflows/keep-alive.yml) pings
`/health` every 10 minutes so the instance never reaches the 15-minute idle
trigger. Pinging `/health` rather than a quotes endpoint keeps the wake-up cheap:
it touches no data files.

The job is not fire-and-forget. It retries through the 502/503 a waking container
returns, allows 90 seconds for a cold start, and fails if the body's `status` is
anything but `ok` — a 200 that reports a broken service is still a broken
service. Run it on demand from **Actions → Keep-alive → Run workflow**, or point
it at another host by setting the `API_BASE_URL` repository variable.

Two limits of using GitHub for this, both worth knowing before relying on it:

- **Scheduled runs are best-effort.** Under load GitHub can start a `cron` job
  several minutes late, and the 10-minute interval is tuned to absorb that. If a
  run is ever delayed past 15 minutes, the next request pays a cold start.
- **GitHub disables `schedule` triggers on public repositories after 60 days
  without repository activity**, which would silently stop the pings. For a
  guarantee rather than a best effort, use an external monitor (UptimeRobot's
  free plan checks every 5 minutes) pointed at
  `https://<service>.onrender.com/health`.

Keeping one service awake around the clock uses roughly 730 of the 750 free
instance hours Render grants per month, leaving little headroom for a second
free service on the same account.

### Anywhere else

The app is a standard ASGI application:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

## License

MIT.
