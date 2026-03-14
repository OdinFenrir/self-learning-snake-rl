from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from sb3_contrib import MaskablePPO


class _PolicyTraceWrapper(torch.nn.Module):
    def __init__(self, policy: torch.nn.Module) -> None:
        super().__init__()
        self.policy = policy

    def forward(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        latent_pi, latent_vf = self.policy.mlp_extractor(obs)
        logits = self.policy.action_net(latent_pi)
        value = self.policy.value_net(latent_vf)
        return logits, value


def main() -> None:
    parser = argparse.ArgumentParser(description="Export SB3 MaskablePPO policy to TorchScript for Netron.")
    parser.add_argument("--model", required=True, help="Path to SB3 .zip model")
    parser.add_argument("--out", required=True, help="Output .pt path")
    args = parser.parse_args()

    model_path = Path(args.model)
    out_path = Path(args.out)
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")

    model = MaskablePPO.load(str(model_path), device="cpu")
    policy = model.policy
    policy.eval()

    obs_shape = tuple(int(v) for v in getattr(model.observation_space, "shape", ()) or ())
    if not obs_shape:
        raise SystemExit("Unsupported observation space shape for export.")
    sample = torch.as_tensor(np.zeros((1, *obs_shape), dtype=np.float32))

    wrapper = _PolicyTraceWrapper(policy)
    traced = torch.jit.trace(wrapper, sample)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    traced.save(str(out_path))
    print(f"Exported TorchScript policy: {out_path}")


if __name__ == "__main__":
    main()
