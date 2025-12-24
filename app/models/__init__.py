from pathlib import Path
import importlib, pkgutil

# 当前包路径
_package_path = Path(__file__).resolve().parent


# 动态导入
for _f, modname, ispkg in pkgutil.walk_packages([str(_package_path)], prefix=f"{__name__}."):
    if any(skip in modname for skip in (".base", ".__", "._")):
        continue
    importlib.import_module(modname)
