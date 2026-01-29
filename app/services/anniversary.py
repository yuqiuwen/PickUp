import asyncio
from typing import Any, List, Literal
from app.constant import AnniversaryType, GroupRole, InviteTargetType
from app.core.http_handler import CursorPageRespModel
from app.ext.jwt import TokenUserInfo
from app.repo.anniversary import anniv_repo, anniv_member_repo, remind_repo, tag_repo
from app.schemas.anniversary import (
    AnnivFeedItem,
    AnnivStat,
    CreateAnnivSchema,
    QueryAnnivSchema,
    RemindRuleSchema,
)
from app.schemas.common import MediaSchema, TagsSchema
from app.services.invite import InviteService
from app.utils.dater import DT


class AnnivService:
    def __init__(self, type: AnniversaryType):
        self.anniv_type = type

    async def create_anniv(self, session, cur_user: TokenUserInfo, data: CreateAnnivSchema):
        expires_seconds = 7 * 86400  # invite expire time，7 days
        if not data.owner_id:
            data.owner_id = cur_user.id

        anniv_data = {
            "name": data.name,
            "description": data.description,
            "event_year": data.event_year,
            "event_date": data.event_date,
            "event_time": data.event_time,
            "cover": data.cover,
            "calendar_type": data.calendar_type,
            "type": data.type,
            "share_mode": data.share_mode,
            "owner_id": data.owner_id,
            "is_reminder": data.is_reminder,
            "repeat_type": data.repeat_type,
            "lunar_year": data.lunar_year,
            "lunar_month": data.lunar_month,
            "lunar_day": data.lunar_day,
            "lunar_is_leap": data.lunar_is_leap,
            "next_trigger_at": data.next_trigger_at,
            "location": data.location,
            "create_by": cur_user.id,
            "update_by": cur_user.id,
        }
        # create invite record
        anniv = await anniv_repo.add(session, anniv_data, commit=False)
        anniv_id = anniv.id

        # create anniversary member for owner
        await anniv_member_repo.batch_add(
            session,
            [
                {
                    "anniv_id": anniv_id,
                    "ttype": 2,
                    "tid": str(data.owner_id),
                    "role": GroupRole.OWNER,
                }
            ],
            commit=False,
        )

        # create tags
        if data.tags:
            await anniv_repo.add_tag(session, anniv_id, cur_user.id, data.tags, commit=False)

        # create media
        if data.media:
            await anniv_repo.add_media(session, anniv_id, data.media, commit=False)

        # create remind
        if data.is_reminder:
            await self.create_remind(
                session, anniv_id, [data.owner_id], data.remind_rule, commit=False
            )

        # create invite records if share，include site and email invite
        if data.share_mode == 1:
            await InviteService(InviteTargetType.ANNIVERSARY).create_invite(
                session, anniv_id, cur_user.id, data.share, expires_seconds, commit=False
            )

            await InviteService(InviteTargetType.ANNIVERSARY).publish_invite_job(anniv_id)

        await session.commit()

        return data

    async def create_remind(
        self, session, anniv_id: str, user_ids: list[int], data: RemindRuleSchema, commit=True
    ):
        rule = await remind_repo.add(session, anniv_id, user_ids, data, commit)
        return rule

    async def update_remind(
        self, session, anniv_id: str, user_ids: list[int], data: RemindRuleSchema, commit=True
    ):
        rule = await remind_repo.edit(session, anniv_id, user_ids, data, commit)
        return rule

    @staticmethod
    async def get_base_stat(session, cur_user: TokenUserInfo):
        year_total = await anniv_repo.get_year_total(session, cur_user.id, DT.now_year())
        next_annivs = await anniv_repo.get_next(
            session,
            cur_user.id,
        )
        return AnnivStat(year_total=year_total, next_anniv=next_annivs)

    @staticmethod
    async def get_anniv_feed(
        session,
        cur_user: TokenUserInfo,
        params: QueryAnnivSchema,
    ) -> CursorPageRespModel[List[AnnivFeedItem]]:
        paged = await anniv_repo.list_feed(session, cur_user.id, params)

        anniv_ids = [i.id for i in paged.items]
        tags_mapping = await anniv_repo.list_tag(session, anniv_ids)
        medias_mapping = await anniv_repo.list_media(session, anniv_ids)

        items: list[AnnivFeedItem] = []
        for anniv in paged.items:
            anniv = AnnivFeedItem.model_validate(anniv)
            tags = tags_mapping[anniv.id]
            medias = medias_mapping[anniv.id]
            anniv.tags = TagsSchema.to_dantic_model_list(tags, strict=False)
            anniv.medias = MediaSchema.to_dantic_model_list(medias, strict=False)
            items.append(anniv)

        paged.items = items

        return paged

    @staticmethod
    async def get_anniv(session, cur_user: TokenUserInfo, anniv_id: str):
        item = await anniv_repo.retrieve_my_anniv(session, cur_user.id, anniv_id)
        return item
