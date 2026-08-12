import asyncio
import inspect
import logging
import time
from functools import wraps

from pypresence import AioPresence
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


def asyncSlot(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.ensure_future(func(*args, **kwargs))

    return wrapper


class DiscordRPCThread(QThread):
    rpc_connected = pyqtSignal(object)

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.discord_rpc: AioPresence | None = None
        self.start_time = time.time()
        self.latest_rpc = {}

    @property
    def rpc_check(self):
        return bool(
            self.discord_rpc
            and self.mw.settings.value("discord_rpc/enable", True, type=bool)
        )

    @asyncSlot
    async def connect(self):
        try:
            self.discord_rpc = AioPresence("1358471829165047819")
            self.rpc_connected.emit(await self.discord_rpc.connect())
            logger.debug(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC connected!"
            )
        except Exception as e:  # noqa: BLE001
            self.mw.settings.setValue("discord_rpc/enable", False)
            logger.error(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}"
            )

    @asyncSlot
    async def update(self, *args, **kwargs):
        if self.rpc_check:
            try:
                self.latest_rpc = {"args": args, "kwargs": kwargs}
                await self.discord_rpc.update(
                    *self.latest_rpc["args"],
                    **self.latest_rpc["kwargs"],
                    start=self.start_time,
                )
                logger.debug(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated!"
                )
            except RuntimeError:
                logger.warning(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated, but RuntimeError!"
                )
            except Exception as e:  # noqa: BLE001
                self.mw.settings.setValue("discord_rpc/enable", False)
                logger.error(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}"
                )
        else:
            logger.warning(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC not initialized"
            )

    @asyncSlot
    async def update_wlrpc(self):
        if self.rpc_check:
            try:
                await self.discord_rpc.update(
                    *self.latest_rpc["args"],
                    **self.latest_rpc["kwargs"],
                    start=self.start_time,
                )
                logger.debug(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated!"
                )
            except RuntimeError:
                logger.warning(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC updated, but RuntimeError!"
                )
            except Exception as e:  # noqa: BLE001
                self.mw.settings.setValue("discord_rpc/enable", False)
                logger.error(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}"
                )
        else:
            logger.warning(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC not initialized"
            )

    @asyncSlot
    async def clear(self):
        if self.rpc_check:
            try:
                await self.discord_rpc.clear()
                logger.debug(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC cleared!"
                )
            except Exception as e:  # noqa: BLE001
                self.mw.settings.setValue("discord_rpc/enable", False)
                logger.error(
                    f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}"
                )
        else:
            logger.warning(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC not initialized"
            )

    @asyncSlot
    async def close(self):
        try:
            await self.discord_rpc.close()
            logging.debug(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): DiscordRPC closed!"
            )
        except Exception as e:
            self.mw.settings.setValue("discord_rpc/enable", False)
            logging.error(
                f"QThreads.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): {e}"
            )
