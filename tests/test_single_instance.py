from __future__ import annotations

import socket
import unittest

from snake_frame.single_instance import SingleInstanceGuard


def _find_free_tcp_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


class TestSingleInstanceGuard(unittest.TestCase):
    def test_acquire_blocks_second_instance_on_same_port(self) -> None:
        port = _find_free_tcp_port()
        first = SingleInstanceGuard(port=port)
        second = SingleInstanceGuard(port=port)
        try:
            self.assertTrue(first.acquire())
            self.assertFalse(second.acquire())
            first.release()
            self.assertTrue(second.acquire())
        finally:
            first.release()
            second.release()

    def test_release_is_idempotent(self) -> None:
        port = _find_free_tcp_port()
        guard = SingleInstanceGuard(port=port)
        self.assertTrue(guard.acquire())
        guard.release()
        guard.release()


if __name__ == "__main__":
    unittest.main()
