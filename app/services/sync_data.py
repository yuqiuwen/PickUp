import traceback
from app.core.loggers import app_logger
from app.database import redcache
from app.repo.anniversary import anniv_repo
from app.services.cache.counter import AnnivCounter
from app.utils.common import chunker


class SyncDataService:
    @staticmethod
    async def synchronize_anniv_count(session):
        """
        同步纪念日计数字段
        :return:
        """

        size = 5000
        keys = await AnnivCounter("*").scan(count=size)

        for batch in chunker(keys, chunk_size=size):
            try:
                data = await AnnivCounter.get_cache_data(
                    redcache, "hash", batch, cmd="HGETALL", sep_rule=(":", 1, 1)
                )
                if not data:
                    continue
                await anniv_repo.batch_edit(session, data)

                ret = await redcache.delete(*batch)
                app_logger.info(f"succeeded to synchronize bp count, deleted cache {ret} items")

            except Exception as e:
                await session.rollback()
                traceback.print_exc()
                app_logger.error(f"failed to synchronize bp count, errmsg：{str(e)}")

                for k in batch:  # 更新失败延长缓存key过期时间
                    await AnnivCounter(k).expire()

                continue
