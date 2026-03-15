# Checking Celery and fixing server-stats 503 in production

The admin dashboard **server-stats** API returns **503** when there is no `ServerStatsSnapshot` in the database. That snapshot is filled by the Celery Beat task `pages.tasks.refresh_server_stats` every few seconds. If the task never runs (worker or beat down, or task failing), the API stays 503.

## 1. Fix 503 immediately (one-off refresh)

Run the same logic as the task once from the **web** container (no Celery needed):

```bash
make celery-refresh-stats
```

Or:

```bash
make manage ARGS="refresh_server_stats_snapshot"
```

This creates/updates the snapshot so the API returns 200 until the next time the snapshot would have been updated by the task (or run the command again). Use this while you fix worker/beat.

## 2. Check if worker and beat are running

On the production server (where Docker Compose runs):

```bash
# Use the same compose files as deploy
export COMPOSE_FILE=compose.yaml:compose.production.yaml

# List running containers; you should see adlab-worker and adlab-beat (or similar)
docker compose ps

# If worker or beat are missing, start them
docker compose up -d worker beat
```

## 3. Check worker and beat logs

```bash
export COMPOSE_FILE=compose.yaml:compose.production.yaml

# Last 100 lines of worker log (look for errors or "refresh_server_stats")
docker compose logs --tail=100 worker

# Last 100 lines of beat log (look for "Sending due task refresh-server-stats")
docker compose logs --tail=100 beat
```

Beat may show only "beat: Starting..." for up to one minute (or up to `CELERY_BEAT_MAX_LOOP_INTERVAL` seconds) before the first "Sending due task" line; that is normal, not a hang.

If the task is failing, the worker log will show the exception (e.g. missing `get_media_bucket_stats`, Docker socket permission, etc.).

## 4. Verify Redis and schedule

```bash
# Redis reachable from app (use manage.py so Django settings load)
docker compose exec web python3 manage.py shell -c "
from django.core.cache import cache
cache.set('ping', 1, 5)
assert cache.get('ping') == 1
print('Redis OK')
"

# Registered periodic tasks (run in web container)
docker compose exec web python3 manage.py shell -c "
from django.conf import settings
for name, entry in settings.CELERY_BEAT_SCHEDULE.items():
    print(name, entry['task'], entry['schedule'])
"
```

## 5. Manually trigger the task (via worker)

If worker is running and you want to trigger the task once over the queue:

```bash
docker compose exec worker celery -A config call pages.tasks.refresh_server_stats
```

## 6. Common causes of “tasks not running”

| Symptom | Likely cause |
|--------|----------------|
| Containers `worker` / `beat` not in `docker compose ps` | They were not started (e.g. profile or compose file). Start with `docker compose up -d worker beat`. |
| Beat runs but worker never gets tasks | Redis URL or broker misconfiguration; worker not connected to same Redis. Check `CELERY_BROKER_URL` and worker logs. |
| Task runs but snapshot still empty (503) | Task raises an exception (e.g. import error, Docker/psutil error). Check worker logs for `refresh_server_stats failed`. |
| 503 after deploy | Migrations run after app start, or beat/worker start before `ServerStatsSnapshot` table exists. Deploy script should run migrations before starting app services; then run `make celery-refresh-stats` once if needed. |
| Beat sends tasks but worker never runs them | Schedule had `"queue": "default"` while the worker consumes the default queue named `"celery"`. Use `"queue": "celery"` in `CELERY_BEAT_SCHEDULE` options (or omit so tasks go to the celery queue). |
| Beat log shows only "beat: Starting..." for a long time | By default beat wakes at most every 60s. Wait ~1 minute for the first "Sending due task refresh-server-stats". If you need more frequent logs, set `CELERY_BEAT_MAX_LOOP_INTERVAL` (seconds) in the environment. |
| Beat stalls at "Starting..." with no further logs (even after 5+ min) | The beat volume used to mount over the whole app dir (`celerybeat:/app/src`), which could hide app code or block the scheduler. It now mounts only at `celerybeat:/app/src/celerybeat_data` with schedule file `-s .../celerybeat-schedule`. Redeploy and restart beat. To start clean: `docker compose down beat && docker volume rm laboratory-system_celerybeat 2>/dev/null; docker compose up -d beat`. |

## 7. Quick checklist on the server

```bash
export COMPOSE_FILE=compose.yaml:compose.production.yaml

# 1. Containers up?
docker compose ps

# 2. One-off refresh (fixes 503 now)
make celery-refresh-stats

# 3. Worker logs
docker compose logs --tail=50 worker

# 4. Beat logs
docker compose logs --tail=50 beat
```
