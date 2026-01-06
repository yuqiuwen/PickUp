from fastapi import Depends

from app.ext.auth import get_current_user
from app.models.user import User


def require_roles(*required_roles: str):
    # 使用方式：current_user: User = Depends(require_roles("admin", "operator")),

    # 如果函数中无需用到user，可以写到router中：
    # @router.get("/health", dependencies=[Depends(require_roles("admin"))])

    async def dependency(user: User = Depends(get_current_user)) -> User:
        """
        在这里写：当前 user 是否包含 required_roles 之一/全部 的判断，
        如果不满足就 raise HTTPException(403)。
        """

        # 占位：伪代码
        # user_role_names = {role.name for role in user.roles}
        # if not some_check(user_role_names, required_roles):
        #     raise HTTPException(status_code=403, detail="Forbidden")
        return user  # 返回 user，方便在路由里继续用

    return dependency


def require_perms(*required_perms: str):
    # 使用方式
    # @router.get("/orders")
    # async def list_orders(
    #     user: User = Depends(require_perms("order:read")),
    # ):
    #     ...

    async def dependency(user: User = Depends(get_current_user)) -> User:
        """
        在这里写：当前 user 是否拥有 required_perms 的判断逻辑。
        """
        # 占位：从 user.roles 里聚合所有 permissions.code 然后判断
        # user_perm_codes = {...}
        # if not some_check(user_perm_codes, required_perms):
        #     raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return dependency
