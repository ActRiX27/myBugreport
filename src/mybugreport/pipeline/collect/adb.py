"""ADB-based collection utilities with layered fallbacks and logging.

All functions are designed to be testable by injecting a custom runner.
"""

import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from ...models import CollectArtifact, DeviceInfo
from ...utils import write_json
from . import collect_existing_artifact, fingerprint_file, write_artifacts_index

CommandRunner = Callable[[List[str], Optional[float]], subprocess.CompletedProcess]


def default_runner(cmd: List[str], timeout: Optional[float] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def log_line(handle, message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    handle.write(f"[{ts}] {message}\n")
    handle.flush()


def ensure_dir(path: Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def get_device_info(serial: str, runner: CommandRunner, log_handle) -> DeviceInfo:
    props = {
        "model": _adb_getprop(serial, "ro.product.model", runner, log_handle),
        "android_version": _adb_getprop(serial, "ro.build.version.release", runner, log_handle),
        "build_fingerprint": _adb_getprop(serial, "ro.build.fingerprint", runner, log_handle),
    }
    return DeviceInfo(serial=serial, **props)


def _adb_getprop(serial: str, key: str, runner: CommandRunner, log_handle) -> Optional[str]:
    cmd = ["adb", "-s", serial, "shell", "getprop", key]
    proc = runner(cmd, timeout=15)
    log_line(log_handle, f"run {' '.join(shlex.quote(c) for c in cmd)} -> {proc.returncode}")
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def run_and_save(
    cmd: List[str],
    output_path: Path,
    runner: CommandRunner,
    log_handle,
    timeout: Optional[float] = None,
) -> None:
    proc = runner(cmd, timeout=timeout)
    log_line(log_handle, f"run {' '.join(shlex.quote(c) for c in cmd)} -> {proc.returncode}")
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(proc.stdout or "")


def collect_adb(
    serial: str,
    out_dir: Path,
    duration: Optional[int] = None,
    since: Optional[str] = None,
    buffers: Optional[Iterable[str]] = None,
    include_dmesg: bool = False,
    include_bugreport: bool = False,
    runner: CommandRunner = default_runner,
) -> Path:
    """
    Collect logs from adb. Raises RuntimeError on failures.
    Returns path to artifacts.json.
    """
    out_dir = Path(out_dir)
    logs_dir = out_dir / "logs"
    ensure_dir(logs_dir)
    artifacts: List[CollectArtifact] = []
    log_handle = (out_dir / "collect.log").open("a", encoding="utf-8")

    try:
        device = get_device_info(serial, runner, log_handle)

        logcat_cmd = ["adb", "-s", serial, "logcat", "-v", "threadtime", "-d"]
        if buffers:
            for buf in buffers:
                logcat_cmd.extend(["-b", buf])
        if since:
            logcat_cmd.extend(["-T", since])
        logcat_path = logs_dir / "logcat.txt"
        run_and_save(logcat_cmd, logcat_path, runner, log_handle, timeout=duration)
        artifacts.append(
            CollectArtifact(
                path=str(logcat_path),
                captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                device=device,
                artifact_type="logcat",
                sha256=fingerprint_file(logcat_path),
                size_bytes=logcat_path.stat().st_size,
                command=" ".join(logcat_cmd),
                metadata={"buffers": list(buffers) if buffers else None, "since": since},
            )
        )

        if include_dmesg:
            dmesg_cmd = ["adb", "-s", serial, "shell", "dmesg"]
            dmesg_path = logs_dir / "dmesg.txt"
            run_and_save(dmesg_cmd, dmesg_path, runner, log_handle, timeout=duration)
            artifacts.append(
                CollectArtifact(
                    path=str(dmesg_path),
                    captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    device=device,
                    artifact_type="dmesg",
                    sha256=fingerprint_file(dmesg_path),
                    size_bytes=dmesg_path.stat().st_size,
                    command=" ".join(dmesg_cmd),
                )
            )

        if include_bugreport:
            bugreport_cmd = ["adb", "-s", serial, "bugreport"]
            bugreport_path = logs_dir / "bugreport.txt"
            run_and_save(bugreport_cmd, bugreport_path, runner, log_handle, timeout=duration or 300)
            artifacts.append(
                CollectArtifact(
                    path=str(bugreport_path),
                    captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    device=device,
                    artifact_type="bugreport",
                    sha256=fingerprint_file(bugreport_path),
                    size_bytes=bugreport_path.stat().st_size,
                    command=" ".join(bugreport_cmd),
                )
            )

        device_info_path = logs_dir / "device_info.json"
        write_json(device, device_info_path)

        artifacts_dir = out_dir / "collect"
        ensure_dir(artifacts_dir)
        artifacts_index = artifacts_dir / "artifacts.json"
        write_artifacts_index(artifacts, artifacts_index)
        log_line(log_handle, f"Artifacts indexed at {artifacts_index}")
        return artifacts_index
    except FileNotFoundError as exc:
        log_line(log_handle, f"ERROR: command not found: {exc}")
        raise RuntimeError("adb not found") from exc
    except subprocess.TimeoutExpired as exc:
        log_line(log_handle, f"ERROR: command timeout: {exc}")
        raise RuntimeError("adb command timeout") from exc
    except Exception as exc:
        log_line(log_handle, f"ERROR: {exc}")
        raise
    finally:
        log_handle.close()


__all__ = ["collect_adb", "default_runner"]
