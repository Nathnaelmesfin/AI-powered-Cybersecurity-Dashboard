import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def ensure_nats_server_binary() -> str | None:
    existing = shutil.which("nats-server")
    if existing:
        return existing

    cache_dir = Path(__file__).parent / "fixtures" / ".bin"
    cache_dir.mkdir(parents=True, exist_ok=True)
    binary = cache_dir / "nats-server"
    if binary.exists():
        os.environ["PATH"] = f"{cache_dir}:{os.environ.get('PATH', '')}"
        return str(binary)

    version = "2.10.16"
    tgz = cache_dir / "nats-server.tgz"
    url = f"https://github.com/nats-io/nats-server/releases/download/v{version}/nats-server-v{version}-linux-amd64.tar.gz"
    try:
        subprocess.run(["curl", "-fsSL", "-o", str(tgz), url], check=True)
        subprocess.run(["tar", "-xzf", str(tgz), "-C", str(cache_dir)], check=True)
        extracted = cache_dir / f"nats-server-v{version}-linux-amd64" / "nats-server"
        extracted.replace(binary)
        binary.chmod(0o755)
        os.environ["PATH"] = f"{cache_dir}:{os.environ.get('PATH', '')}"
        return str(binary)
    except Exception:
        return None
