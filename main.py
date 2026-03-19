from snake_frame.app import run
from snake_frame.single_instance import SingleInstanceGuard
from snake_frame.welcome import show_welcome_window


if __name__ == "__main__":
    guard = SingleInstanceGuard()
    if not guard.acquire():
        raise SystemExit("Snake Frame is already running.")
    try:
        while True:
            route = show_welcome_window()
            if route is None:
                raise SystemExit(0)
            return_to_menu = bool(run(startup_route=route))
            if not return_to_menu:
                break
    finally:
        guard.release()
