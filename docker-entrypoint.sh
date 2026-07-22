#!/bin/sh
# Container startup: wait for PostgreSQL, migrate, bootstrap data, serve.
set -e

echo "Waiting for database..."
python - <<'EOF'
import os, sys, time
import psycopg

dsn = "host={h} port={p} dbname={d} user={u} password={pw}".format(
    h=os.environ.get("POSTGRES_HOST", "db"),
    p=os.environ.get("POSTGRES_PORT", "5432"),
    d=os.environ.get("POSTGRES_DB", "skycommons"),
    u=os.environ.get("POSTGRES_USER", "skycommons"),
    pw=os.environ["POSTGRES_PASSWORD"],
)
for attempt in range(30):
    try:
        psycopg.connect(dsn).close()
        sys.exit(0)
    except psycopg.OperationalError as e:
        last = e
        time.sleep(2)
print(f"Database never became ready: {last}", file=sys.stderr)
sys.exit(1)
EOF

python manage.py migrate --noinput
python manage.py bootstrap_data

exec gunicorn skycommons.wsgi:application --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" --access-logfile -
