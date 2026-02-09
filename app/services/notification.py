from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List
from typing_extensions import DefaultDict
from app.constant import ResourceType, SysActionEnum, SysAnnounceActionEnum
from app.core.types import TActionEnum
from app.ext.jwt import TokenUserInfo
from app.repo.anniversary import anniv_repo
from app.repo.notification import (
    announce_ntfy_repo,
    remind_ntfy_cursor_repo,
    remind_ntfy_repo,
    sys_ntfy_repo,
)
from app.repo.user import user_repo
from app.schemas.anniversary import AnnivFeedItem
from app.schemas.notification import (
    AnnounceNotifyItem,
    QueryRemindNotifySchema,
    RemindNotifyItem,
    SysNotifyItem,
)
from app.services.cache.user import UnReadMsgCntCache
from app.utils.dater import DT


class BaseNtfyService(ABC):
    @abstractmethod
    async def list(self, *args, **kwargs):
        pass

    async def get_targets(self, session, t: List[tuple[ResourceType, str]]):
        grouped: DefaultDict[ResourceType, list[str]] = defaultdict(list)
        for ttype, value in t:
            grouped[ttype].append(value)

        result_mapping: DefaultDict[ResourceType, dict] = defaultdict(dict)

        for ttype, tids in grouped.items():
            match ttype:
                case ResourceType.ANNIV:
                    target_mapping = await self.get_anniv_mapping(session, tids)
                case _:
                    target_mapping = {}

            result_mapping[ttype] = target_mapping

        return result_mapping

    async def get_anniv_mapping(self, session, tids: List[str]):
        items = await anniv_repo.get_anniv_by_id(session, tids)
        return {i.id: AnnivFeedItem.model_validate(i, strict=False) for i in items}

    async def update_cursor(session, user: TokenUserInfo, data: dict[TActionEnum, int]):
        return await remind_ntfy_cursor_repo.edit(session, user.id, data)

    def calc_max_id_by_action(self, items) -> dict[int, int]:
        m: dict[int, int] = {}
        for row in items:
            a = row.action
            m[a] = max(m.get(a, 0), row.id)
        return m


class RemindNtfyService(BaseNtfyService):
    async def list(self, session, user: TokenUserInfo, params: QueryRemindNotifySchema):
        cur_uid = user.id
        paged = await remind_ntfy_repo.list(session, cur_uid, params)
        rows = paged.items

        uids = {uid for row in rows for uid in row.from_uids} | {cur_uid}

        target_map = await self.get_targets(session, [(row.ttype, row.tid) for row in rows])
        users_map = await user_repo.get_user_mapping(
            session, uids, only_cols=user_repo.BASE_USER_COLS
        )
        items = []
        max_id_map: dict[int, int] = {}
        for item in rows:
            a = item.action
            max_id_map[a] = max(max_id_map.get(a, 0), item.id)
            ntfy = RemindNotifyItem.model_validate(item, strict=False)
            ntfy.target = target_map[item.ttype].get(item.tid)
            ntfy.to_user = users_map.get(cur_uid)
            ntfy.from_users = [users_map[uid] for uid in item.from_uids if uid in users_map]

            items.append(ntfy)

        paged.items = items
        paged.max_id_map = max_id_map

        return paged

    async def get_unread_msgcounts(self, session, uid: int) -> dict:
        cache = UnReadMsgCntCache(uid)
        data = await cache.get()
        if not data:
            data = await remind_ntfy_cursor_repo.get_unread_count(session, uid)
            await cache.add(data.model_dump())

        return data

    async def reset_all_msgcounts(self, session, uid: int):
        now = DT.now_ts()

        remind_map = await remind_ntfy_repo.get_lastest_id(session, uid, now)
        sys_id = await sys_ntfy_repo.get_lastest_id(session, uid, now)
        announce_id = await announce_ntfy_repo.get_lastest_id(session, now)

        remind_map[SysActionEnum.SYS] = sys_id
        remind_map[SysAnnounceActionEnum.ANNOUNCE] = announce_id

        await remind_ntfy_cursor_repo.edit(session, uid, remind_map)

        await UnReadMsgCntCache(uid).delete()


class SysNtfyService(BaseNtfyService):
    async def list(self, session, user: TokenUserInfo, params: QueryRemindNotifySchema):
        cur_uid = user.id
        paged = await sys_ntfy_repo.list(session, cur_uid, params)
        rows = paged.items

        target_map = await self.get_targets(session, [(row.ttype, row.tid) for row in rows])
        items = []
        for item in rows:
            ntfy = SysNotifyItem.model_validate(item, strict=False)
            ntfy.target = target_map[item.ttype].get(item.tid)
            items.append(ntfy)

        paged.items = items

        return paged


class AnnounceNtfyService(BaseNtfyService):
    async def list(self, session, user: TokenUserInfo, params: QueryRemindNotifySchema):
        cur_uid = user.id
        paged = await announce_ntfy_repo.list(session, cur_uid, params)
        return paged
