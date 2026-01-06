# pickup


## 目录结构
```bash
.
├── alembic                 # 数据迁移版本
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
├── alembic.ini
├── app                     # app核心目录
│   ├── __init__.py         # 初始化
│   ├── celery.py           # celery 初始化
│   ├── common              # 公共目录
│   ├── config              # 配置文件
│   ├── constant.py         # 全局枚举
│   ├── core                # 核心依赖
│   ├── database            # db相关
│   ├── ext                 # 插件
│   ├── middlewares         # 中间件
│   ├── models              # model层
│   ├── repo                # repo层
│   ├── routers             # 路由层
│   ├── schemas             # 数据schema
│   ├── services            # service层
│   ├── tasks               # celery task
│   ├── tests               # 测试
│   └── utils               # 工具包
├── deployment              # 部署脚本
│   ├── deploy-docker.sh
│   └── deploy-docker.test.sh
├── docker-compose.dev.yml
├── docker-compose.yml
├── docker-entrypoint.sh
├── Dockerfile
├── docs
│   ├── EMAIL_SIGNUP.md
│   └── init.sql
├── gunicorn.conf.py
├── gunicorn.conf.test.py
├── LICENSE
├── manage.py               # 执行入口
├── pyproject.toml
├── README.md
├── requirements.txt
├── scripts
│   └── db-migrate.sh
├── test.py
└── uv.lock
```

接口版本定义在 routers.v1/__init__.py 中 `API_PREFIX`，若未定义将使用目录名称，如： v1


## Depolyment
```bash
uv sync

source .venv/bin/activate

# 本地用.env文件管理环境变量，生产不会读取env文件，由运行环境注入
copy .env.example .env


# 数据库迁移，可直接用alembic，也可用scripts/db-migrate.sh脚本执行
## 开发环境
export APP_ENV=development
alembic revision --autogenerate -m ""
alembic upgrade head

## 测试环境
export APP_ENV=testing
alembic upgrade head



## 使用脚本
### 生成迁移
./scripts/migrate.sh development generate "add users"

### 执行迁移
./scripts/migrate.sh development upgrade

### 回退迁移
./scripts/migrate.sh development downgrade
```
