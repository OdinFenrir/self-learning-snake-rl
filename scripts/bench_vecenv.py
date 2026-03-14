from __future__ import annotations

from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from snake_frame.ppo_agent import PpoSnakeAgent  # noqa: E402
from snake_frame.settings import ObsConfig, PpoConfig, RewardConfig, Settings  # noqa: E402


def main() -> None:
    obs = ObsConfig(use_extended_features=True, use_path_features=True, use_tail_path_features=True)
    reward = RewardConfig()
    settings = Settings()
    for use_subproc in (False, True):
        cfg = PpoConfig(
            env_count=8,
            use_subproc_env=use_subproc,
            n_steps=1024,
            batch_size=256,
            n_epochs=8,
            eval_freq_steps=0,
            checkpoint_freq_steps=0,
        )
        agent = PpoSnakeAgent(
            settings=settings,
            artifact_dir=ROOT / "artifacts" / "tmp_perf" / ("subproc_on" if use_subproc else "subproc_off"),
            config=cfg,
            reward_config=reward,
            obs_config=obs,
            autoload=False,
        )
        start = time.perf_counter()
        steps = agent.train(total_timesteps=8192, stop_flag=lambda: False)
        elapsed = time.perf_counter() - start
        print(
            {
                "use_subproc": bool(use_subproc),
                "steps": int(steps),
                "elapsed": float(elapsed),
                "sps": float(steps / elapsed),
            }
        )


if __name__ == "__main__":
    main()
