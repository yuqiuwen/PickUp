import os
from pathlib import Path

from dotenv import load_dotenv


app_env = os.getenv("APP_ENV", "development")


def load_env(cfg_name):
    if cfg_name in ("production",):
        return

    env_dic = {"development": ".env", "testing": ".env.test", "unittest": ".env.unittest"}
    envfile = env_dic.get(cfg_name)
    env_path = str(Path(__file__).parent.parent / envfile)
    load_dotenv(dotenv_path=env_path, override=True)


load_env(app_env)

from app import create_app  # noqa

app = create_app(app_env)
