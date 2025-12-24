import socketio

from app.middlewares.jwt_auth import JwtAuthMiddleware
from app.config import settings
from app.core.loggers import app_logger
from app.database.redis_client import redis_socket


# 创建 Socket.IO 服务器实例
sio = socketio.AsyncServer(
    client_manager=socketio.AsyncRedisManager(settings.REDIS_SOCKET_URL),
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
    cors_credentials=True,
    channel=f"{settings.APP_NAME}:{settings.ENV}",
    namespaces=['/ws'],
)


@sio.event(namespace='/ws')
async def connect(sid, environ, auth) -> bool:
    """Socket 连接事件"""
    if not auth:
        app_logger.error('WebSocket 连接失败：无授权')
        return False

    session_uuid = auth.get('session_uuid')
    token = auth.get('token')
    if not token or not session_uuid:
        app_logger.error('WebSocket 连接失败：授权失败，请检查')
        return False

    # 免授权直连
    await redis_socket.hset(settings.SID_MAP_KEY, sid, session_uuid)
    if token == settings.WS_NO_AUTH_MARKER:
        await redis_socket.sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
        return True

    try:
        await JwtAuthMiddleware.jwt_authentication(token)
    except Exception as e:
        app_logger.info(f'WebSocket 连接失败：{e!s}')
        return False
    
    await redis_socket.sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
    return True


@sio.event(namespace='/ws')
async def disconnect(sid) -> None:
    """Socket 断开连接事件"""
    session_uuid = await redis_socket.hget(settings.SID_MAP_KEY, sid)
    if session_uuid:
        await redis_socket.srem(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
    await redis_socket.hdel(settings.SID_MAP_KEY, sid)
