import os
from pathlib import Path
from dotenv import load_dotenv


def load_env(cfg_name=None):
    if not cfg_name:
        cfg_name = os.getenv("APP_ENV", "development")

    if cfg_name in ("production",):
        return

    env_dic = {"development": ".env", "testing": ".env.test", "unittest": ".env.unittest"}
    envfile = env_dic.get(cfg_name)
    load_dotenv(dotenv_path=envfile, override=True)

    return cfg_name
