"""Filesystem and Path utilities."""

import getpass
import hashlib
from datetime import datetime
from pathlib import Path


def user() -> str:
    """Get the current user"""
    return getpass.getuser()


def path_collapse_user(path: Path, home: Path | None = None):
    """Do the opposite of path.expanduser(), for portability.

    Replaces the home directory prefix with '~', so paths like
    /home/user/projects/ become ~/projects/.
    """
    if home is None:
        home = Path.home()
    try:
        relative = path.relative_to(home)
        return Path("~") / relative
    except ValueError:
        # Path is not under the home directory, return as-is
        return path


def tmp_path(ext: str):
    """Temporary file with extension."""
    ext = ext.removeprefix(".")

    now = datetime.now().isoformat()
    return Path(f"/tmp/{now}.{ext}")


def stem(p: Path | str):
    """lazy way to get the stem of a path (str)"""
    return Path(p).stem


def sha256_file(path: Path, chunksize: int = 1 << 20) -> str:
    """Checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while buf := f.read(chunksize):
            h.update(buf)
    return h.hexdigest()


def sha256_path(path: Path) -> str:
    """Deterministic checksum of a directory: hash of sorted per-file checksums."""

    if path.is_file():
        return sha256_file(path)

    file_hashes = sorted(
        f"{sha256_file(f)}  {f.relative_to(path)}"
        for f in sorted(path.rglob("*"))
        if f.is_file()
    )
    return hashlib.sha256("\n".join(file_hashes).encode()).hexdigest()
