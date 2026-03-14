from __future__ import annotations

import json
import logging
import platform
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
import zipfile

logger = logging.getLogger(__name__)


DIAGNOSTICS_CLEANUP_FAILED = "diagnostics_cleanup_failed"


class DiagnosticsBundleResult:
    def __init__(
        self,
        *,
        bundle_path: Path,
        cleanup_warnings: tuple[str, ...] = (),
        error_codes: tuple[str, ...] = (),
    ) -> None:
        self.bundle_path = bundle_path
        self.cleanup_warnings = tuple(str(v) for v in cleanup_warnings)
        self.error_codes = tuple(str(v) for v in error_codes)


def _version_of(module_name: str) -> str:
    try:
        module = __import__(module_name)
    except Exception:
        return "unavailable"
    return str(getattr(module, "__version__", "unknown"))


def _serialize_obj(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_obj(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize_obj(v) for k, v in value.items()}
    return str(value)


def create_diagnostics_bundle(
    *,
    output_dir: Path,
    settings,
    state_paths: list[Path],
    extra: dict | None = None,
) -> DiagnosticsBundleResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_path = output_dir / "snakeframe_diagnostics_latest.zip"
    cleanup_warnings: list[str] = []
    error_codes: list[str] = []
    for stale in output_dir.glob("snakeframe_diagnostics_*.zip"):
        if stale.name == bundle_path.name:
            continue
        try:
            stale.unlink(missing_ok=True)
        except OSError as exc:
            warning = f"stale_bundle_cleanup_failed:{stale.name}: {exc}"
            cleanup_warnings.append(warning)
            error_codes.append(DIAGNOSTICS_CLEANUP_FAILED)
            logger.warning("Diagnostics cleanup warning: %s", warning, exc_info=True)
    extra_payload = _serialize_obj(extra or {})
    meta = {
        "generated_at_utc": stamp,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cleanupWarnings": list(cleanup_warnings),
        "errorCodes": list(error_codes),
        "runtimeHealth": _serialize_obj(extra_payload.get("runtimeHealth", {})) if isinstance(extra_payload, dict) else {},
        "lastError": _serialize_obj(extra_payload.get("lastError", {})) if isinstance(extra_payload, dict) else {},
        "versions": {
            "pygame": _version_of("pygame"),
            "numpy": _version_of("numpy"),
            "gymnasium": _version_of("gymnasium"),
            "stable_baselines3": _version_of("stable_baselines3"),
            "torch": _version_of("torch"),
        },
        "settings": _serialize_obj(settings),
        "extra": extra_payload,
    }
    with zipfile.ZipFile(bundle_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, indent=2))
        for state_path in state_paths:
            if not state_path.exists():
                continue
            zf.write(state_path, arcname=f"state/{state_path.name}")
    return DiagnosticsBundleResult(
        bundle_path=bundle_path,
        cleanup_warnings=tuple(cleanup_warnings),
        error_codes=tuple(error_codes),
    )
