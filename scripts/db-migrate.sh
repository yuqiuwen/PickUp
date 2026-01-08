#!/usr/bin/env bash

:<<!
### 生成迁移
./scripts/db-migrate.sh development generate "add users"

### 执行迁移
./scripts/db-migrate.sh development upgrade

### 回退迁移
./scripts/db-migrate.sh development downgrade
!



ENV=${1:-development}
export APP_ENV=$ENV

case "$2" in
    "generate")
        alembic revision --autogenerate -m "$3"
        ;;
    "upgrade")
        alembic upgrade head
        ;;
    "downgrade")
        alembic downgrade -1
        ;;
    *)
        echo "Usage: $0 [environment] [generate|upgrade|downgrade] [message]"
        exit 1
        ;;
esac
