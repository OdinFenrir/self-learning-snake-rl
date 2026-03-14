from __future__ import annotations

import logging
import socket

logger = logging.getLogger(__name__)


class SingleInstanceGuard:
    """Process-level guard to avoid running multiple app instances."""

    def __init__(self, host: str = "127.0.0.1", port: int = 49542) -> None:
        self._host = host
        self._port = int(port)
        self._socket: socket.socket | None = None

    def acquire(self) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind((self._host, self._port))
            sock.listen(1)
            self._socket = sock
            return True
        except OSError:
            logger.debug("SingleInstanceGuard acquire failed on %s:%s", self._host, self._port, exc_info=True)
            sock.close()
            return False

    def release(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                logger.warning("Failed to close single-instance guard socket", exc_info=True)
            self._socket = None
