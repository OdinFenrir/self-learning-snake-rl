from __future__ import annotations

import unittest

try:
    from stable_baselines3.common.env_checker import check_env
except Exception as exc:  # pragma: no cover - env-dependent import gate
    raise RuntimeError(
        "ML dependency setup is required for env-compliance tests. "
        "Install with `pip install -r requirements.txt`."
    ) from exc

from snake_frame.ppo_env import SnakePPOEnv


class TestEnvCompliance(unittest.TestCase):
    def test_check_env_passes(self) -> None:
        env = SnakePPOEnv(board_cells=10, seed=1337)
        try:
            check_env(env, warn=True, skip_render_check=True)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
