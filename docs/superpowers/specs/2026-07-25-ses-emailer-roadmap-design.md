# SES Emailer — Improvement Roadmap

**Date:** 2026-07-25
**Status:** Approved (full roadmap; P0 implemented first)

## Context

SES Emailer is a terminal-based bulk email tool on AWS SES, recently rewritten
(see `Task.md`) from a monolithic Python CLI into a **Python FastAPI backend**
(`api/`, `sending/`, `config/`) + **TypeScript/Ink TUI** (`ts-tui/`), wired
together by `start.py` with a one-time bearer token. It supports HTML/plain
composition, React-Email `.tsx` templates, Excel recipient import, rate-limited
batch sending with live SSE progress, campaign history, drafts, and multi-profile
config.

Two deep explorations surfaced a working-but-fragile app: the send loop runs
blocking I/O on the async event loop, recipients are never validated or
de-duplicated at send time, a failed-email retry feature is modelled in the DB
but never wired up, there is dead/legacy code and a broken `requirements.txt`,
and there are **zero tests** with CI that only builds the marketing site.

The goal: keep the current architecture (it was just built and fits the use case)
and improve it in **prioritized phases** — fix the foundation first (P0), then
layer the highest-value features (P1), then nice-to-haves (P2).

The design decisions below were chosen by the user: prioritized mix, all four P1
features, full roadmap scope.

---

## P0 — Foundation (implemented first)

Goal: correctness, reliability, security, and a safety net. Low risk, high value,
and a precondition for every later feature.

### Reliability
- **Non-blocking sends.** The SSE generator in `api/routers/email.py` calls
  blocking `boto3` `send_email` and SQLite writes directly on the event loop,
  freezing the whole API during a send. Move each SES call and DB write into a
  worker thread via `asyncio.to_thread(...)` so the loop stays responsive.
- **Record all failures.** Today only `ClientError` batches are logged to
  `failed_emails`; a generic `Exception` increments the counter but records
  nothing (`email.py:208`). Log every failed recipient with its reason.
- **No silent swallowing.** Replace bare `except Exception: pass` around
  `db.add_email` and attachment reads with logged warnings surfaced in the SSE
  stream.

### Correctness
- **Recipient validation.** New `sending/validation.py` with `is_valid_email` /
  `partition_valid`. Invalid addresses are filtered before sending and reported
  back (count + list) in the `start` SSE event, rather than handed to SES.
- **Optional dedup on send.** `SendRequest` gains `skip_already_sent: bool`.
  When set, the send path calls the existing `db.compare_recipients` and skips
  addresses already sent for this subject, reporting how many were skipped.
  (The capability exists in `sending/db.py:181` but was never called on send.)
- **Excel parser fix.** `sending/email_list.py:19` does `item[0] != " "` which
  crashes on numeric/NaN cells (ints aren't subscriptable) and is only masked by
  a broad `except` returning `[]`. Rewrite to coerce to `str`, strip, and keep
  only valid emails via `sending/validation.py`. Fix the misleading default
  `column_index=6` → `0` to match the API layer.

### Persistence
- **DB path is honored & centralized.** `sending/db.py:10-11` accepts
  `file_name` but hardcodes `"emails.db"` and is CWD-relative. Honor the param,
  add a `SES_DB_PATH` env override resolved to an absolute path anchored at the
  project root, enable **WAL mode** + `check_same_thread=False`, and add an index
  on `sent_emails(email_id, sent_to)` to keep dedup/summary queries fast.

### Security
- **Constant-time token compare.** `api/auth.py:27` uses `!=`; switch to
  `secrets.compare_digest`.
- **Scoped CORS.** `api/main.py:23` uses `allow_origins=["*"]` with
  credentials; restrict to `http://127.0.0.1` / `http://localhost` origins.
- **Secrets note.** Document that AWS keys live plaintext in
  `config/settings.json` (gitignored) and that the currently-present key pair
  should be rotated. (No code change forces this; it is a README/ops note.)

### Cleanup
- Delete dead/legacy code: `sending/senders.py` (broken `from emails import`,
  blocking `input()`, stub methods — imported nowhere), root `main.py` (3-line
  leftover), and the committed `.git_diff.txt`.
- Remove the no-op stub methods (`add_sent`/`check_sent`/`EmailSent.mark_sent`)
  from `sending/emails.py`.
- Replace the broken `requirements.txt` (non-portable `file:///AppleInternal/...`
  wheels) with a clean, portable list mirroring `pyproject.toml`, and note `uv`
  as the primary path.

### Tests + CI
- Add `pytest` + `ruff` as a dev dependency group in `pyproject.toml`.
- Tests (`tests/`): `sending/validation.py`, `sending/db.py` (drafts, sent,
  compare, failed-email lifecycle), `sending/email_list.py` parsing (incl. the
  numeric-cell regression), `config/settings.py` (profile CRUD + legacy
  migration), and API smoke tests via FastAPI `TestClient` with `boto3` mocked
  (send happy-path, validation filtering, auth rejection, retry).
- `.github/workflows/ci.yml`: run `ruff check` + `pytest` on the backend and
  `tsc --noEmit` on `ts-tui`, on push/PR — separate from the existing
  landing-page Pages deploy.

### Retry (completes a half-built feature)
- **Endpoint** `POST /api/history/{campaign_id}/retry` (SSE, mirrors the send
  stream) that pulls `db.get_unretried_failed_emails` for the campaign's email
  IDs, re-sends them through the shared send path, and marks each
  `mark_failed_email_retried` on success.
- **TUI**: `retryCampaign` in `ts-tui/src/api.ts`; a retry action in
  `HistoryScreen` when a campaign has unretried failures.

### Docs
- Update the README endpoint table (add `templates`, `shutdown`, `retry`), fix
  the `requirements.txt` guidance, and note the secret-rotation item.

---

## P1 — High-value features (phased, on the current stack)

Each is its own spec → plan → implement cycle; sketched here for ordering.

### 1. Mail-merge personalization — ✅ IMPLEMENTED (branch `feature/mail-merge-personalization`)
Per-recipient `{{name}}`/`{{column}}` substitution so a BCC blast becomes
individual personalized emails.
- `sending/personalize.py`: `{{token}}` extraction + case-insensitive render +
  missing-field detection (unit tested).
- `sending/email_list.py:scrape_excel_rows` + `POST /api/emails/upload-excel-rows`
  parse Excel/CSV into `{email, fields}` rows keyed by header names.
- `SendRequest` gains `personalize` + `recipient_fields`; `send_event_stream`
  sends **one rendered email per recipient** (To:, per-recipient failure
  granularity) when tokens are present, else falls back to the BCC batch. The
  `start` SSE event reports `personalized` + `fields`.
- TUI: `ts-tui/src/personalize.ts` (client mirror), Excel import captures fields,
  a Preview personalization panel (detected fields, sample render, missing-field
  warning, on/off toggle), and a Personalized badge on the Send screen.
- Tests: `tests/test_personalize.py`, rows parsing, and API send/HTTP coverage.

### 2. Scheduling / background queue — ✅ IMPLEMENTED (branch `feature/scheduling-queue`)
Schedule campaigns and survive TUI disconnects.
- **Job model**: a `jobs` table (id, type, status, name, payload, scheduled_at,
  total/sent/failed counters, timestamps) with statuses `scheduled`, `pending`,
  `running`, `completed`, `failed`, `canceled`, plus the enqueue/claim/progress/
  cancel/requeue DB methods in `sending/db.py`.
- **In-process async worker** (`api/worker.py`) started via the FastAPI lifespan
  in `api/main.py`. It claims due jobs (pending, or scheduled and past their
  `scheduled_at`), runs them through the **shared send pipeline** (so it reuses
  validation, dedup, and mail-merge personalization), and records progress. Since
  the worker runs independently of any client, a queued/scheduled send survives
  the TUI disconnecting. On startup it **requeues interrupted (running) jobs** to
  pending (crash recovery), and running jobs can be **canceled cooperatively**.
- **Endpoints** (`api/routers/jobs.py`, all bearer-authed): `POST /api/jobs`
  (enqueue/schedule; body mirrors the send request plus optional `scheduled_at`
  and `name`), `GET /api/jobs` (list, newest first), `GET /api/jobs/{id}` (status
  + progress), `POST /api/jobs/{id}/cancel`, and `GET /api/jobs/{id}/stream`
  (reconnect-safe SSE that polls job state).
- **TUI**: a new Queue screen (Home `J`) listing jobs with live-refreshing
  progress and a Cancel action (`C`); Compose gains `Ctrl+J` to queue or schedule
  the current email (optional "Schedule (ISO)" field), while `Ctrl+E` still does
  an immediate live send.

### 3. Bounce & complaint tracking
Protect sender reputation.
- Configure an **SES configuration set** + **SNS topic**; expose a public
  webhook `POST /api/ses/notifications` (SNS subscription-confirm + signature
  verification) that records bounces/complaints into a `suppression` table.
- Suppressed addresses are auto-filtered at send time (reuse the P0 validation
  pipeline). TUI surfaces suppression list + per-campaign bounce/complaint counts.
- Requires a publicly reachable endpoint (documented deploy note) — the only
  feature that reaches beyond localhost.

### 4. Analytics dashboard
- Open/click tracking via SES configuration-set event publishing (opens =
  tracking pixel, clicks = link wrapping) into an `events` table; richer
  per-campaign stats (sent/delivered/opened/clicked/bounced, rates, timeline)
  in the History screen, and optionally surfaced in the landing site as a static
  demo.

---

## P2 — Nice-to-haves

- **TUI statefulness/polish**: stop `console.clear()` wiping screen state on
  `Ctrl+H`; preserve Compose state across navigation; dynamic resize/scroll so
  content fits any terminal size (this was an original `Task.md` goal).
- **AWS profile / SSO credential source** instead of raw keys in JSON;
  OS-keychain option for secrets.
- **Send-quota / throttle awareness** (respect SES rate + daily quota instead of
  a fixed sleep).
- **History pagination + indexes** (grouped summary is recomputed in Python on
  every call).
- **CSV import parity**, template variables preview, and a dry-run/preview-send.
- **Packaging**: single `uvx`/`bunx` entry, optional Dockerfile.

---

## Verification (P0)

1. `uv run ruff check .` and `uv run pytest` pass (CI runs both).
2. `uv run python -c "from api.main import app"` imports cleanly (no dead-code
   import errors).
3. Manual: `uv run python start.py`, send to a small test list — API stays
   responsive during the inter-batch delay; invalid addresses are filtered and
   reported; re-sending the same subject with dedup on skips known recipients; a
   campaign with failures shows a working Retry action in History.
4. `cd ts-tui && bunx tsc --noEmit` passes.
