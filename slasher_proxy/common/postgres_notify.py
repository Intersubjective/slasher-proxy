from typing import Any, Callable, Coroutine

import asyncpg_listen

from slasher_proxy.common.log import LOGGER


async def create_notification_listener(
    postgres_url: str, channel_name: str, callback: Callable[[str | None], Any]
) -> Coroutine[Any, Any, None]:
    listener = asyncpg_listen.NotificationListener(
        asyncpg_listen.connect_func(dsn=postgres_url)
    )

    async def handle_notifications(
        notification: asyncpg_listen.NotificationOrTimeout,
    ) -> None:
        if isinstance(notification, asyncpg_listen.Timeout):
            LOGGER.warning("Timeout waiting for notification from Postgres")
            return
        LOGGER.debug("Received notification from Postgres: %s", notification.payload)
        callback(notification.payload)

    return listener.run(
        {channel_name: handle_notifications},
        policy=asyncpg_listen.ListenPolicy.ALL,
        notification_timeout=3600,
    )
