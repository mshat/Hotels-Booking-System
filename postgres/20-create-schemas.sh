#!/usr/bin/env bash
set -e

export SCRIPT_PATH=/docker-entrypoint-initdb.d/
export PGPASSWORD=test
psql -U program -d services -f "$SCRIPT_PATH/schemes/schema.sql"


# psql -U program -d services -f "docker-entrypoint-initdb.d/schemes/test_data.sql" - нужно запустить вручную после первого запуска сервисов (они должны создать таблицы)
