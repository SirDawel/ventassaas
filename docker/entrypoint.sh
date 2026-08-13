#!/bin/sh
set -e

wait_for_db() {
  python - <<'PY'
import os
import time
import psycopg2

host = os.environ.get('DB_HOST', 'localhost')
port = int(os.environ.get('DB_PORT', '5432'))
name = os.environ.get('DB_NAME')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')

if not all([name, user, password]):
    raise SystemExit("DB_NAME, DB_USER y DB_PASSWORD son obligatorios")

for i in range(30):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=name, user=user, password=password)
        conn.close()
        print("Base de datos lista")
        break
    except Exception:
        print(f"Esperando base de datos... intento {i + 1}/30")
        time.sleep(2)
else:
    raise SystemExit("No fue posible conectar a la base de datos")
PY
}

if [ "${WAIT_FOR_DB:-1}" = "1" ]; then
  wait_for_db
fi

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate_schemas --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

ROLE="${1:-web}"

if [ "$ROLE" = "web" ]; then
  exec gunicorn VentasSys.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-3} \
    --timeout ${GUNICORN_TIMEOUT:-120}
elif [ "$ROLE" = "worker" ]; then
  exec celery -A VentasSys worker --loglevel=${CELERY_LOG_LEVEL:-INFO}
elif [ "$ROLE" = "beat" ]; then
  exec celery -A VentasSys beat --loglevel=${CELERY_LOG_LEVEL:-INFO}
else
  exec "$@"
fi
