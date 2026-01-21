import secrets
from time import time
from typing import Literal

from fastapi import HTTPException
from redis import retry
from app.constant import AnniversaryType, InviteState, InviteTargetType, SettingsSwitch
from app.core.exception import APIException, PermissionDenied, UserNotFoundError
from app.core.loggers import app_logger
from app.ext.jwt import TokenUserInfo
from app.models.invite import InviteModel
from app.repo.anniversary import anniv_member_repo, anniv_repo
from app.repo.user import share_group_repo, user_repo
from app.schemas.anniversary import CreateAnnivSchema, InviteFieldSchema
from app.repo.invite import invite_repo
from app.services.email import email_service
from app.services.user import UserService
from app.utils.dater import DT


class InviteService:
    def __init__(self, ttype: InviteTargetType):
        self.ttype = ttype

    async def create_invite(
        self,
        session,
        tid: str,
        inviter_id: int,
        data: InviteFieldSchema,
        expires_after: int,
        commit=True,
    ):
        """创建邀请

        Args:
            tid(str): 邀请的资源对象id，如纪念日id
            inviter_id (int): 邀请者id
            data (InviteFieldSchema): 邀请数据
            expires_after(int): 过期时间（秒）

        Returns:
            _type_: _description_
        """
        invite_items = []

        async def do_create_user_invite(
            _ttype: Literal[1, 2], _tid: str | int, user_id: int = None, account: str = None
        ) -> dict:
            """build one user invite

            Args:
                user_id (int): user id
                ttype (Literal[1, 2]): 1-group 2-member
                tid (str | int): group_id / user_id
                account (str ): email ...

            Returns:
                dict: invite record
            """

            # 暂时不考虑用户量，批量发邀请

            # invite users
            if user_id:
                user = await UserService.check_user_exist(session, "id", user_id)
                if not user:
                    return

                # 查询用户偏好设置：是否接受纪念日邀请
                if self.ttype == InviteTargetType.ANNIVERSARY:
                    unaccept_invite = UserService.get_me_one_setting(
                        user_id, "privacy_unaccept_anniv_invite"
                    )
                    if unaccept_invite == SettingsSwitch.ON:
                        return

                invitee_email = user.email
            else:
                invitee_email = account

            body = {
                "ttype": self.ttype,
                "tid": tid,
                "inviter_id": inviter_id,
                "invitee_user_id": user_id,
                "invitee_email": invitee_email,
                "state": InviteState.PENDING,
                "token": secrets.token_urlsafe(32),
                "expires_at": DT.now_ts() + expires_after,
                "message": data.message,
                "meta": {"ttype": _ttype, "tid": _tid},
            }

            invite_items.append(body)
            return body

        # 注册用户
        for invitee_user_id in data.invite_app_users:
            await do_create_user_invite(2, invitee_user_id, invitee_user_id)

        # 组
        if data.invite_groups:
            group_owner_mapping = UserService.get_group_owner_mapping(
                session, group_id=data.invite_groups
            )
            for gid, uid in group_owner_mapping.items():
                await do_create_user_invite(1, gid, uid)

        # 未注册用户
        for item in data.invite_external_users:
            await do_create_user_invite(2, None, None, item["account"])

        # create invite records
        ret = await invite_repo.batch_add(session, invite_items, commit=commit)

        return ret

    async def publish_invite_job(self, tid: str):
        from app.tasks.anniv_task import send_email_invite

        send_email_invite.delay(ttype=self.ttype, tid=tid)

    async def process_send_invite(self, session, tid: str):
        # 获取待发送的邀请
        invites: list[InviteModel] = await invite_repo.list(
            ttype=self.ttype,
            tid=tid,
            state=InviteState.PENDING,
            expires_at_range=[DT.now_ts(), None],
        )
        if not invites:
            return

        for item in invites:
            user_ids = [item.inviter_id]
            if item.invitee_user_id:
                user_ids.append(item.invitee_user_id)

            try:
                user_name_mapping = await UserService.get_user_name_mapping(session, user_ids)
                anniv = await anniv_repo.retrieve_or_404(session, item.tid)
                await email_service.send_anniv_invite_email(
                    item.invitee_email,
                    user_name_mapping.get(item.inviter_id, ""),
                    user_name_mapping.get(item.invitee_user_id, ""),
                    anniv.name,
                    anniv.event_date,
                )
            except Exception as e:
                app_logger.error(f"邀请邮件发送失败：{e}")
                continue

    @staticmethod
    async def handle_invite(
        session,
        action: Literal["accept", "decline"],
        cur_user: TokenUserInfo | None = None,
        invite_id: str | None = None,
        raw_token: str | None = None,
    ):
        invite = await invite_repo.retrieve(session, invite_id, raw_token)

        now = DT.now()
        if invite.expires_at and now > invite.expires_at:
            raise APIException(errmsg="邮件链接已过期")

        if cur_user and invite.invitee_user_id != cur_user.id:
            raise PermissionDenied()

        if invite.state != InviteState.SENT:
            raise APIException(errmsg="当前状态不可操作")

        if invite.state == InviteState.ACCEPTED and action == "accept":
            raise APIException(errmsg="已接受邀请")
        if invite.state == InviteState.DECLINED and action == "decline":
            raise APIException(errmsg="已拒绝邀请")

        user = UserService.check_user_exist(session, "email", invite.invitee_email)
        if not user:
            raise UserNotFoundError()

        # 更新状态
        if action == "accept":
            invite.state = InviteState.ACCEPTED

            # 把 invitee 加入纪念日参与者表
            ## 获取邀请的目标对象类型：1group 2member，如果是group，tid=当前用户所在组id；如果是member，tid=当前用户id
            ## 注意：invite_ttype 不是 InviteModel.ttype
            invite_ttype = invite.meta.get("ttype")
            invite_tid = invite.meta.get("tid")
            if invite_ttype == 2:
                invite_tid = cur_user and cur_user.id or None
            else:
                share_group = await share_group_repo.retrieve(invite_tid)
                if share_group.owner_id != cur_user.id:
                    raise PermissionDenied(errmsg="您已不属于此组成员")

            anniv_member = [{"ttype": invite_ttype, "tid": invite_tid, "anniv_id": invite.tid}]
            anniv_member_repo.batch_add(session, anniv_member, commit=False)
        else:
            invite.state = InviteState.DECLINED

        invite.utime = now
        invite.responded_at = now

        await session.commit()

        # TODO 给 inviter 发送“对方已接受/已拒绝”的站内通知 / 邮件
        # ...

        return invite
