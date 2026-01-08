# ruff: noqa: E402
import asyncio
from logging.config import fileConfig
import os
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from dotenv import load_dotenv


def load_env(cfg_name):
    if cfg_name in ("production",):
        return

    env_dic = {"development": ".env", "testing": ".env.test", "unittest": ".env.unittest"}
    envfile = env_dic.get(cfg_name)
    env_path = str(Path(__file__).parent.parent / envfile)
    load_dotenv(dotenv_path=env_path, override=True)


load_env(os.getenv("APP_ENV", "development"))


from app.config import settings  # noqa


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata


from app.models.base import Base

target_metadata = Base.metadata


config.set_main_option("sqlalchemy.url", settings.DB_MAIN_URL)


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    :param object: 一个SchemaItem对象,
    如Table, Column, Index, UniqueConstraint, ForeignKeyConstraint等
    :param name:   该对象的名称
    :param type_:  该对象的类型，
        表对象="table"，字段对象="column"，索引对象="index",
        唯一约束="unique_constraint",
        外键约束="foreign_key_constraint"
    :param reflected:
        True=基于表反射产生（即从数据库中加载的表）
        False=该对象来自本地模型数据,即models.Base.metadata
    :param compare_to: 与之比较的对象,没有则是None
    :return: bool
    """
    return not reflected  # 只反射本地模型数据,不反射数据库中的表


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
