from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import webbrowser

import numpy as np
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _resolve_vecnormalize_path(model_path: Path, requested: str | None) -> Path | None:
    if requested:
        path = Path(requested)
        return path if path.exists() else None
    if model_path.name.endswith("_steps.zip"):
        token = model_path.name.replace("step_", "").replace("_steps.zip", "")
        candidate = model_path.parent / f"step_vecnormalize_{token}_steps.pkl"
        if candidate.exists():
            return candidate
    candidate = model_path.parent / "vecnormalize.pkl"
    if candidate.exists():
        return candidate
    candidate = model_path.parent / "resume_vecnormalize.pkl"
    if candidate.exists():
        return candidate
    return None


def _load_reward_and_obs_config(model_path: Path):
    from snake_frame.settings import ObsConfig, RewardConfig

    metadata = model_path.parent / "metadata.json"
    if metadata.exists():
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        reward_cfg = RewardConfig(**dict(payload.get("reward_config", {})))
        obs_cfg = ObsConfig(**dict(payload.get("obs_config", {})))
        return reward_cfg, obs_cfg
    return RewardConfig(), ObsConfig()


def _maybe_load_vecnorm(vec_path: Path | None, reward_cfg, obs_cfg, board_cells: int) -> VecNormalize | None:
    from snake_frame.ppo_env import SnakePPOEnv

    if vec_path is None or not vec_path.exists():
        return None
    dummy = DummyVecEnv([lambda: Monitor(SnakePPOEnv(board_cells=board_cells, seed=0, reward_config=reward_cfg, obs_config=obs_cfg))])
    try:
        vec = VecNormalize.load(str(vec_path), dummy)
        vec.training = False
        vec.norm_reward = False
        return vec
    except Exception:
        dummy.close()
        return None


def _pca_3d(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    u, s, _vt = np.linalg.svd(centered, full_matrices=False)
    k = min(3, s.shape[0])
    proj = u[:, :k] * s[:k]
    if k < 3:
        pad = np.zeros((proj.shape[0], 3 - k), dtype=np.float32)
        proj = np.concatenate([proj, pad], axis=1)
    return proj.astype(np.float32)


def _sample_indices(count: int, limit: int) -> np.ndarray:
    if count <= limit:
        return np.arange(count, dtype=np.int64)
    return np.linspace(0, count - 1, num=limit, dtype=np.int64)


def build_view(
    *,
    model_path: Path,
    vec_path: Path | None,
    out_path: Path,
    episodes: int,
    max_steps: int,
    seed_base: int,
    max_points: int,
) -> Path:
    from snake_frame.ppo_env import SnakePPOEnv
    from snake_frame.settings import Settings

    settings = Settings()
    reward_cfg, obs_cfg = _load_reward_and_obs_config(model_path)
    model = MaskablePPO.load(str(model_path), device="cpu")
    policy = model.policy
    vec_norm = _maybe_load_vecnorm(vec_path, reward_cfg, obs_cfg, settings.board_cells)

    latent_rows: list[np.ndarray] = []
    action_rows: list[int] = []
    conf_rows: list[float] = []
    score_rows: list[int] = []
    episode_rows: list[int] = []
    step_rows: list[int] = []
    terminal_idx: list[int] = []
    terminal_reason: list[str] = []
    entropy_rows: list[float] = []
    safe_count_rows: list[int] = []
    danger_sum_rows: list[float] = []

    with torch.no_grad():
        for ep in range(max(1, int(episodes))):
            env_seed = int(seed_base + ep)
            env = SnakePPOEnv(
                board_cells=settings.board_cells,
                seed=env_seed,
                reward_config=reward_cfg,
                obs_config=obs_cfg,
            )
            try:
                obs, _ = env.reset(seed=env_seed)
                done = False
                for t in range(max(1, int(max_steps))):
                    obs_arr = np.asarray(obs, dtype=np.float32)
                    if vec_norm is not None:
                        obs_arr = np.asarray(vec_norm.normalize_obs(obs_arr), dtype=np.float32)
                    batch_obs = np.expand_dims(obs_arr, axis=0)
                    obs_tensor, _ = policy.obs_to_tensor(batch_obs)
                    latent_pi, _latent_vf = policy.mlp_extractor(obs_tensor)
                    logits = policy.action_net(latent_pi)
                    probs = torch.softmax(logits, dim=1).detach().cpu().numpy().reshape(-1)
                    act = int(np.argmax(probs))
                    confidence = float(np.max(probs))
                    entropy = float(-np.sum(probs * np.log(np.clip(probs, 1e-9, 1.0))))

                    latent_rows.append(latent_pi.detach().cpu().numpy().reshape(-1).astype(np.float32))
                    action_rows.append(act)
                    conf_rows.append(confidence)
                    entropy_rows.append(entropy)
                    score_rows.append(int(env.score))
                    episode_rows.append(int(ep))
                    step_rows.append(int(t))

                    masks = env.action_masks()
                    safe_count_rows.append(int(np.asarray(masks, dtype=bool).sum()))
                    danger_sum_rows.append(float(np.asarray(obs_arr, dtype=np.float32)[:3].sum()))
                    action, _ = model.predict(batch_obs, deterministic=True, action_masks=np.asarray(masks, dtype=bool).reshape(1, -1))
                    obs, _reward, terminated, truncated, info = env.step(int(np.asarray(action).reshape(-1)[0]))
                    if terminated or truncated:
                        done = True
                        terminal_idx.append(len(latent_rows) - 1)
                        terminal_reason.append(str(info.get("death_reason", "other")))
                        break
                if not done:
                    terminal_idx.append(len(latent_rows) - 1)
                    terminal_reason.append("timeout")
            finally:
                env.close()

    if vec_norm is not None:
        vec_norm.close()

    if not latent_rows:
        raise RuntimeError("No rollout data collected.")

    matrix = np.stack(latent_rows, axis=0)
    keep = _sample_indices(matrix.shape[0], max_points)
    points = _pca_3d(matrix[keep])

    idx_map = {int(orig): idx for idx, orig in enumerate(keep.tolist())}
    terminal_keep = [idx_map[i] for i in terminal_idx if i in idx_map]
    terminal_keep_reason = [terminal_reason[j] for j, i in enumerate(terminal_idx) if i in idx_map]

    hover = [
        (
            f"ep={episode_rows[i]} step={step_rows[i]} score={score_rows[i]} "
            f"action={action_rows[i]} conf={conf_rows[i]:.3f} entropy={entropy_rows[i]:.3f} "
            f"safe={safe_count_rows[i]} danger_sum={danger_sum_rows[i]:.2f}"
        )
        for i in keep.tolist()
    ]
    action_vals = [int(action_rows[i]) for i in keep.tolist()]
    conf_vals = [float(conf_rows[i]) for i in keep.tolist()]
    ent_vals = [float(entropy_rows[i]) for i in keep.tolist()]
    safe_vals = [int(safe_count_rows[i]) for i in keep.tolist()]
    danger_vals = [float(danger_sum_rows[i]) for i in keep.tolist()]

    terminal_x = [float(points[i, 0]) for i in terminal_keep]
    terminal_y = [float(points[i, 1]) for i in terminal_keep]
    terminal_z = [float(points[i, 2]) for i in terminal_keep]
    terminal_hover = [f"terminal: {r}" for r in terminal_keep_reason]

    conf_arr = np.asarray(conf_rows, dtype=np.float64)
    ent_arr = np.asarray(entropy_rows, dtype=np.float64)
    danger_arr = np.asarray(danger_sum_rows, dtype=np.float64)
    action_arr = np.asarray(action_rows, dtype=np.int64)
    safe_arr = np.asarray(safe_count_rows, dtype=np.int64)
    reason_counts: dict[str, int] = {}
    for reason in terminal_reason:
        key = str(reason)
        reason_counts[key] = int(reason_counts.get(key, 0) + 1)
    action_counts = {str(k): int((action_arr == k).sum()) for k in (0, 1, 2)}
    safe_counts = {str(k): int((safe_arr == k).sum()) for k in (0, 1, 2, 3)}
    conf_p10 = float(np.percentile(conf_arr, 10)) if conf_arr.size else 0.0
    conf_mean = float(conf_arr.mean()) if conf_arr.size else 0.0
    ent_mean = float(ent_arr.mean()) if ent_arr.size else 0.0
    low_conf_rate = float((conf_arr < 0.45).mean()) if conf_arr.size else 0.0
    corr_danger_conf = float(np.corrcoef(danger_arr, conf_arr)[0, 1]) if conf_arr.size > 1 else 0.0

    payload = {
        "x": points[:, 0].astype(float).tolist(),
        "y": points[:, 1].astype(float).tolist(),
        "z": points[:, 2].astype(float).tolist(),
        "hover": hover,
        "action": action_vals,
        "conf": conf_vals,
        "entropy": ent_vals,
        "safe": safe_vals,
        "danger": danger_vals,
        "terminal_x": terminal_x,
        "terminal_y": terminal_y,
        "terminal_z": terminal_z,
        "terminal_hover": terminal_hover,
        "title": f"Policy Embedding 3D - {model_path.name}",
        "summary": {
            "points": int(len(conf_rows)),
            "episodes": int(max(1, episodes)),
            "conf_mean": conf_mean,
            "conf_p10": conf_p10,
            "entropy_mean": ent_mean,
            "low_conf_rate": low_conf_rate,
            "corr_danger_conf": corr_danger_conf,
            "action_counts": action_counts,
            "safe_counts": safe_counts,
            "terminal_reason_counts": reason_counts,
        },
    }

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Policy Embedding 3D</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    html, body {{ width: 100%; height: 100%; margin: 0; background: #0d1117; color: #e6edf3; font-family: Segoe UI, Arial, sans-serif; }}
    #wrap {{ display: grid; grid-template-columns: minmax(280px, 320px) 1fr; width: 100%; height: 100%; }}
    #side {{ border-right: 1px solid #1f2a37; padding: 12px; overflow: auto; background: #0b1220; }}
    #plot {{ width: 100%; height: 100%; }}
    .k {{ color: #8fb3d9; }}
    .v {{ color: #f3f8ff; }}
    .blk {{ margin-bottom: 10px; }}
    h3 {{ margin: 0 0 8px 0; font-size: 15px; }}
  </style>
</head>
<body>
  <div id="wrap">
    <div id="side">
      <h3>Policy Diagnostics</h3>
      <div class="blk"><span class="k">Points:</span> <span class="v" id="points"></span></div>
      <div class="blk"><span class="k">Episodes:</span> <span class="v" id="episodes"></span></div>
      <div class="blk"><span class="k">Mean confidence:</span> <span class="v" id="conf_mean"></span></div>
      <div class="blk"><span class="k">P10 confidence:</span> <span class="v" id="conf_p10"></span></div>
      <div class="blk"><span class="k">Mean entropy:</span> <span class="v" id="entropy_mean"></span></div>
      <div class="blk"><span class="k">Low-conf rate (&lt;0.45):</span> <span class="v" id="low_conf_rate"></span></div>
      <div class="blk"><span class="k">Corr(danger, conf):</span> <span class="v" id="corr_danger_conf"></span></div>
      <div class="blk"><span class="k">Action counts:</span> <span class="v" id="action_counts"></span></div>
      <div class="blk"><span class="k">Safe-action counts:</span> <span class="v" id="safe_counts"></span></div>
      <div class="blk"><span class="k">Terminal reasons:</span> <span class="v" id="terminal_reasons"></span></div>
    </div>
    <div id="plot"></div>
  </div>
  <script>
    const d = {json.dumps(payload)};
    const traceConf = {{
      type: 'scatter3d',
      mode: 'markers',
      x: d.x, y: d.y, z: d.z,
      text: d.hover,
      hovertemplate: '%{{text}}<extra></extra>',
      marker: {{
        size: 3,
        color: d.conf,
        colorscale: 'Turbo',
        opacity: 0.82,
        colorbar: {{ title: 'confidence' }}
      }},
      name: 'confidence'
    }};
    const traceEntropy = {{
      type: 'scatter3d',
      mode: 'markers',
      x: d.x, y: d.y, z: d.z,
      text: d.hover,
      hovertemplate: '%{{text}}<extra></extra>',
      marker: {{
        size: 3,
        color: d.entropy,
        colorscale: 'Viridis',
        opacity: 0.82,
        colorbar: {{ title: 'entropy' }}
      }},
      visible: false,
      name: 'entropy'
    }};
    const traceAction = {{
      type: 'scatter3d',
      mode: 'markers',
      x: d.x, y: d.y, z: d.z,
      text: d.hover,
      hovertemplate: '%{{text}}<extra></extra>',
      marker: {{
        size: 3,
        color: d.action,
        colorscale: [[0.0, '#3b82f6'], [0.5, '#22c55e'], [1.0, '#f59e0b']],
        opacity: 0.82,
        colorbar: {{ title: 'action' }}
      }},
      visible: false,
      name: 'action'
    }};
    const terminal = {{
      type: 'scatter3d',
      mode: 'markers',
      x: d.terminal_x, y: d.terminal_y, z: d.terminal_z,
      text: d.terminal_hover,
      hovertemplate: '%{{text}}<extra></extra>',
      marker: {{ size: 8, color: '#ff4d4f', symbol: 'diamond', line: {{color: '#111827', width: 1}} }},
      name: 'terminal'
    }};
    const layout = {{
      title: {{ text: d.title, font: {{ color: '#e6edf3', size: 16 }} }},
      paper_bgcolor: '#0d1117',
      plot_bgcolor: '#0d1117',
      scene: {{
        xaxis: {{ title: 'PC1', color: '#9fb3c8', gridcolor: '#24364b' }},
        yaxis: {{ title: 'PC2', color: '#9fb3c8', gridcolor: '#24364b' }},
        zaxis: {{ title: 'PC3', color: '#9fb3c8', gridcolor: '#24364b' }}
      }},
      legend: {{ font: {{ color: '#e6edf3' }} }},
      updatemenus: [{{
        type: 'buttons',
        direction: 'left',
        x: 0.02, y: 1.02,
        bgcolor: '#0f172a',
        bordercolor: '#334155',
        buttons: [
          {{label: 'Color: Confidence', method: 'update', args: [{{visible: [true, false, false, true]}}]}},
          {{label: 'Color: Entropy', method: 'update', args: [{{visible: [false, true, false, true]}}]}},
          {{label: 'Color: Action', method: 'update', args: [{{visible: [false, false, true, true]}}]}}
        ]
      }}]
    }};
    Plotly.newPlot('plot', [traceConf, traceEntropy, traceAction, terminal], layout, {{responsive: true}});

    const s = d.summary;
    const fmt = (n) => Number(n).toFixed(3);
    document.getElementById('points').textContent = s.points;
    document.getElementById('episodes').textContent = s.episodes;
    document.getElementById('conf_mean').textContent = fmt(s.conf_mean);
    document.getElementById('conf_p10').textContent = fmt(s.conf_p10);
    document.getElementById('entropy_mean').textContent = fmt(s.entropy_mean);
    document.getElementById('low_conf_rate').textContent = (100.0 * Number(s.low_conf_rate)).toFixed(1) + '%';
    document.getElementById('corr_danger_conf').textContent = fmt(s.corr_danger_conf);
    document.getElementById('action_counts').textContent = JSON.stringify(s.action_counts);
    document.getElementById('safe_counts').textContent = JSON.stringify(s.safe_counts);
    document.getElementById('terminal_reasons').textContent = JSON.stringify(s.terminal_reason_counts);
  </script>
</body>
</html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an interactive 3D policy-embedding viewer.")
    parser.add_argument("--model", type=str, default="state/ppo/v2/best_score_model.zip")
    parser.add_argument("--vecnormalize", type=str, default="")
    parser.add_argument("--out", type=str, default="artifacts/visuals/policy_embedding_3d.html")
    parser.add_argument("--episodes", type=int, default=24)
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--seed-base", type=int, default=70000)
    parser.add_argument("--max-points", type=int, default=6000)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")
    vec_path = _resolve_vecnormalize_path(model_path, args.vecnormalize or None)

    out = build_view(
        model_path=model_path,
        vec_path=vec_path,
        out_path=Path(args.out),
        episodes=int(args.episodes),
        max_steps=int(args.max_steps),
        seed_base=int(args.seed_base),
        max_points=int(args.max_points),
    )
    print(f"Wrote: {out}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
