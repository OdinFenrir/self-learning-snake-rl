from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class UiStateErrorCode(str, Enum):
    NONE = "none"
    FILESYSTEM = "filesystem"
    IO_INVALID_JSON = "io_invalid_json"
    IO_SCHEMA_UNSUPPORTED = "io_schema_unsupported"
    IO_PARTIAL_WRITE_RECOVERED = "io_partial_write_recovered"
    # Backward-compatible aliases kept for existing callers/tests.
    INVALID = "io_invalid_json"
    UNSUPPORTED_SCHEMA = "io_schema_unsupported"
    PARTIAL_WRITE = "io_partial_write_recovered"


@dataclass(frozen=True)
class UiStateLoadResult:
    payload: dict | None
    invalid: bool = False
    error_code: UiStateErrorCode = UiStateErrorCode.NONE
    detail: str = ""
    cleanup_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class UiStateSaveResult:
    ok: bool
    error_code: UiStateErrorCode = UiStateErrorCode.NONE
    detail: str = ""
    cleanup_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class UiStateDeleteResult:
    ok: bool
    removed: bool
    error_code: UiStateErrorCode = UiStateErrorCode.NONE
    detail: str = ""
    cleanup_warnings: tuple[str, ...] = ()


def save_ui_state(path: Path, payload: dict) -> None:
    result = save_ui_state_result(path, payload)
    if not result.ok:
        raise OSError(result.detail or "failed to save ui state")


def save_ui_state_result(path: Path, payload: dict) -> UiStateSaveResult:
    cleanup_warnings: list[str] = []
    main_replace_succeeded = False
    rollback_created = False
    rollback_restore_succeeded = False

    def _result(
        *,
        ok: bool,
        error_code: UiStateErrorCode = UiStateErrorCode.NONE,
        detail: str = "",
    ) -> UiStateSaveResult:
        return UiStateSaveResult(
            ok=bool(ok),
            error_code=error_code,
            detail=str(detail or ""),
            cleanup_warnings=tuple(cleanup_warnings),
        )

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return _result(ok=False, error_code=UiStateErrorCode.FILESYSTEM, detail=str(exc))
    serialized = json.dumps(payload, indent=2)
    temp_name: str | None = None
    rollback_path = path.with_suffix(path.suffix + ".rollback.tmp")
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(serialized)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_name = temp_file.name
        if path.exists():
            try:
                os.replace(path, rollback_path)
                rollback_created = True
            except OSError as exc:
                return _result(
                    ok=False,
                    error_code=UiStateErrorCode.FILESYSTEM,
                    detail=str(exc),
                )
        try:
            os.replace(temp_name, path)
            main_replace_succeeded = True
        except OSError as exc:
            # Recovery path: restore previous good payload if we moved it.
            if rollback_path.exists():
                try:
                    os.replace(rollback_path, path)
                    rollback_restore_succeeded = True
                except OSError as restore_exc:
                    logger.exception("Failed to restore rollback UI state from %s", rollback_path)
                    cleanup_warnings.append(f"rollback_restore_failed: {restore_exc}")
                    cleanup_warnings.append("rollback_preserved_for_recovery")
            return _result(
                ok=False,
                error_code=UiStateErrorCode.PARTIAL_WRITE,
                detail=str(exc),
            )
        temp_name = None
        if rollback_path.exists():
            try:
                rollback_path.unlink(missing_ok=True)
            except OSError as exc:
                cleanup_warnings.append(f"rollback_cleanup_failed: {exc}")
        return _result(ok=True)
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Failed to remove temporary UI state file: %s", temp_name, exc_info=True)
                cleanup_warnings.append(f"temp_cleanup_failed: {exc}")
        if rollback_path.exists():
            should_cleanup_rollback = bool((main_replace_succeeded and rollback_created) or rollback_restore_succeeded)
            if should_cleanup_rollback:
                try:
                    rollback_path.unlink(missing_ok=True)
                except OSError as exc:
                    logger.warning(
                        "Failed to remove temporary rollback UI state file: %s",
                        rollback_path,
                        exc_info=True,
                    )
                    cleanup_warnings.append(f"rollback_cleanup_failed: {exc}")


def delete_ui_state(path: Path) -> bool:
    result = delete_ui_state_result(path)
    if result.error_code == UiStateErrorCode.FILESYSTEM:
        raise OSError(result.detail or "failed to delete ui state")
    return bool(result.removed)


def delete_ui_state_result(path: Path) -> UiStateDeleteResult:
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            return UiStateDeleteResult(
                ok=False,
                removed=False,
                error_code=UiStateErrorCode.FILESYSTEM,
                detail=str(exc),
            )
        return UiStateDeleteResult(ok=True, removed=True)
    return UiStateDeleteResult(ok=False, removed=False)


def _recover_interrupted_ui_state(path: Path) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    rollback_path = path.with_suffix(path.suffix + ".rollback.tmp")
    tmp_files = [p for p in path.parent.glob(f"{path.name}.*.tmp") if p != rollback_path]
    recovered = False
    if (not path.exists()) and rollback_path.exists():
        try:
            os.replace(str(rollback_path), str(path))
            recovered = True
        except OSError as exc:
            warnings.append(f"rollback_restore_failed: {exc}")
    for tmp_path in tmp_files:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError as exc:
            warnings.append(f"temp_cleanup_failed:{tmp_path.name}: {exc}")
    return recovered, warnings


def load_ui_state_result(path: Path) -> UiStateLoadResult:
    recovered, cleanup_warnings = _recover_interrupted_ui_state(path)
    if not path.exists():
        return UiStateLoadResult(
            payload=None,
            invalid=False,
            error_code=UiStateErrorCode.PARTIAL_WRITE if recovered else UiStateErrorCode.NONE,
            cleanup_warnings=tuple(cleanup_warnings),
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return UiStateLoadResult(
            payload=None,
            invalid=True,
            error_code=UiStateErrorCode.FILESYSTEM,
            detail=str(exc),
            cleanup_warnings=tuple(cleanup_warnings),
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        rollback_path = path.with_suffix(path.suffix + ".rollback.tmp")
        if rollback_path.exists():
            try:
                os.replace(str(rollback_path), str(path))
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return UiStateLoadResult(
                        payload=payload,
                        invalid=False,
                        error_code=UiStateErrorCode.PARTIAL_WRITE,
                        detail="Recovered from rollback after invalid JSON",
                        cleanup_warnings=tuple(cleanup_warnings),
                    )
            except Exception as exc:
                cleanup_warnings.append(f"rollback_restore_failed: {exc}")
        return UiStateLoadResult(
            payload=None,
            invalid=True,
            error_code=UiStateErrorCode.INVALID,
            cleanup_warnings=tuple(cleanup_warnings),
        )
    if not isinstance(payload, dict):
        return UiStateLoadResult(
            payload=None,
            invalid=True,
            error_code=UiStateErrorCode.INVALID,
            cleanup_warnings=tuple(cleanup_warnings),
        )
    rollback_path = path.with_suffix(path.suffix + ".rollback.tmp")
    if rollback_path.exists():
        try:
            rollback_path.unlink(missing_ok=True)
        except OSError as exc:
            cleanup_warnings.append(f"rollback_cleanup_failed: {exc}")
    return UiStateLoadResult(
        payload=payload,
        invalid=False,
        error_code=UiStateErrorCode.PARTIAL_WRITE if recovered else UiStateErrorCode.NONE,
        cleanup_warnings=tuple(cleanup_warnings),
    )


def load_ui_state(path: Path) -> dict | None:
    return load_ui_state_result(path).payload


def migrate_ui_payload(payload: dict | None, *, minimum_version: int = 2, current_version: int = 2) -> UiStateLoadResult:
    src = payload or {}
    if not isinstance(src, dict):
        return UiStateLoadResult(payload=None, invalid=True, error_code=UiStateErrorCode.INVALID)
    migrated = dict(src)
    version = migrated.get("uiStateVersion")
    try:
        version_i = int(version)
    except (TypeError, ValueError):
        version_i = 1
    if version_i > int(current_version):
        return UiStateLoadResult(
            payload=None,
            invalid=True,
            error_code=UiStateErrorCode.UNSUPPORTED_SCHEMA,
            detail=f"uiStateVersion {version_i} is newer than supported {current_version}",
        )
    if version_i < 2 and "themeName" not in migrated:
        migrated["themeName"] = "retro_forest_noir"
    migrated["uiStateVersion"] = max(int(minimum_version), int(version_i))
    return UiStateLoadResult(payload=migrated, invalid=False, error_code=UiStateErrorCode.NONE)
