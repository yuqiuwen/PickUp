#!/bin/sh

# 1. 加上 set -e，一旦任何命令报错，脚本立即停止，防止错误继续扩散
set -e

# (仅可在开发环境下执行) alembic revision --autogenerate

if [ "$RUN_MIGRATIONS" = "1" ]; then
    echo "Running migrations..."
    alembic upgrade head
    echo ""
    echo "迁移后数据库版本:"
    alembic current
    echo "✅ 初始化完成，启动应用..."
fi

exec "$@"
