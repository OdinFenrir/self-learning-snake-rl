from snake_frame.app import run
from snake_frame.single_instance import SingleInstanceGuard


if __name__ == "__main__":
    guard = SingleInstanceGuard()
    if not guard.acquire():
        raise SystemExit("Snake Frame is already running.")
    try:
        run()
    finally:
        guard.release()
