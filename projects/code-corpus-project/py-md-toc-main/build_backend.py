"""Minimal local PEP 517 backend for py-md-toc.

This backend keeps the project buildable without downloading a third-party
build backend, which is helpful in restricted or offline environments.
"""

from __future__ import annotations

import base64
import hashlib
import io
import tarfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_ROOT = ROOT / "src" / "py_md_toc"


def _project() -> dict[str, object]:
    """Load the project metadata straight from pyproject.toml."""

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]


def _normalized_name(name: str) -> str:
    """Normalize the distribution name for wheel and dist-info paths."""

    return name.replace("-", "_").replace(".", "_")


def _sdist_name(name: str, version: str) -> str:
    return f"{name}-{version}.tar.gz"


def _wheel_name(name: str, version: str) -> str:
    return f"{_normalized_name(name)}-{version}-py3-none-any.whl"


def _dist_info_name(name: str, version: str) -> str:
    return f"{_normalized_name(name)}-{version}.dist-info"


def _metadata_text() -> str:
    """Generate the wheel metadata file from the project configuration."""

    project = _project()
    lines = [
        "Metadata-Version: 2.4",
        f"Name: {project['name']}",
        f"Version: {project['version']}",
        f"Summary: {project['description']}",
        f"Requires-Python: {project['requires-python']}",
    ]
    for dependency in project.get("dependencies", []):
        lines.append(f"Requires-Dist: {dependency}")
    return "\n".join(lines) + "\n"


def _wheel_metadata() -> str:
    return (
        "\n".join(
            [
                "Wheel-Version: 1.0",
                "Generator: py-md-toc.build_backend",
                "Root-Is-Purelib: true",
                "Tag: py3-none-any",
            ]
        )
        + "\n"
    )


def _entry_points_text() -> str:
    """Render console-script entry points for the wheel metadata."""

    project = _project()
    scripts = project.get("scripts", {})
    if not scripts:
        return ""
    lines = ["[console_scripts]"]
    for name, target in scripts.items():
        lines.append(f"{name} = {target}")
    return "\n".join(lines) + "\n"


def _top_level_text() -> str:
    return "py_md_toc\n"


def _record_line(path: str, data: bytes) -> str:
    """Format one RECORD entry with the file hash and byte length."""

    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"{path},sha256={encoded},{len(data)}"


def _wheel_files() -> list[tuple[str, bytes]]:
    """Collect source files that should be included in the wheel."""

    files: list[tuple[str, bytes]] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT / "src").as_posix()
        files.append((rel, path.read_bytes()))
    return files


def _write_zip_member(zf: zipfile.ZipFile, path: str, data: bytes) -> None:
    """Write a deterministic zip member so builds stay reproducible."""

    info = zipfile.ZipInfo(path)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data)


def get_requires_for_build_sdist(config_settings: dict[str, object] | None = None) -> list[str]:
    return []


def get_requires_for_build_wheel(config_settings: dict[str, object] | None = None) -> list[str]:
    return []


def get_requires_for_build_editable(
    config_settings: dict[str, object] | None = None,
) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    return _write_dist_info(metadata_directory)


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    return _write_dist_info(metadata_directory)


def _write_dist_info(metadata_directory: str) -> str:
    """Create the dist-info directory used by editable and regular builds."""

    project = _project()
    dist_info = Path(metadata_directory) / _dist_info_name(
        str(project["name"]),
        str(project["version"]),
    )
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(_metadata_text(), encoding="utf-8")
    (dist_info / "WHEEL").write_text(_wheel_metadata(), encoding="utf-8")
    (dist_info / "top_level.txt").write_text(_top_level_text(), encoding="utf-8")
    entry_points = _entry_points_text()
    if entry_points:
        (dist_info / "entry_points.txt").write_text(entry_points, encoding="utf-8")
    return dist_info.name


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return _write_wheel(wheel_directory, editable=False)


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return _write_wheel(wheel_directory, editable=True)


def _wheel_members(editable: bool) -> list[tuple[str, bytes]]:
    """Assemble wheel contents for either editable or regular installs."""

    project = _project()
    dist_info = _dist_info_name(str(project["name"]), str(project["version"]))
    files: list[tuple[str, bytes]] = []

    if editable:
        # Editable installs expose the source tree directly through a .pth file.
        files.append(
            (
                f"{_normalized_name(str(project['name']))}.pth",
                f"{(ROOT / 'src').as_posix()}\n".encode(),
            )
        )
    else:
        files.extend(_wheel_files())

    files.append((f"{dist_info}/METADATA", _metadata_text().encode("utf-8")))
    files.append((f"{dist_info}/WHEEL", _wheel_metadata().encode("utf-8")))
    files.append((f"{dist_info}/top_level.txt", _top_level_text().encode("utf-8")))
    entry_points = _entry_points_text()
    if entry_points:
        files.append((f"{dist_info}/entry_points.txt", entry_points.encode("utf-8")))
    return files


def _write_wheel(wheel_directory: str, editable: bool) -> str:
    """Create a wheel archive in the target directory."""

    project = _project()
    wheel_path = Path(wheel_directory) / _wheel_name(str(project["name"]), str(project["version"]))
    dist_info = _dist_info_name(str(project["name"]), str(project["version"]))

    files = _wheel_members(editable)
    record_entries = [_record_line(path, data) for path, data in files]
    record_entries.append(f"{dist_info}/RECORD,,")

    with zipfile.ZipFile(wheel_path, mode="w") as zf:
        for path, data in files:
            _write_zip_member(zf, path, data)
        _write_zip_member(
            zf,
            f"{dist_info}/RECORD",
            ("\n".join(record_entries) + "\n").encode("utf-8"),
        )

    return wheel_path.name


def build_sdist(
    sdist_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    """Create a source distribution with the files needed to rebuild the project."""

    project = _project()
    archive_name = _sdist_name(str(project["name"]), str(project["version"]))
    archive_path = Path(sdist_directory) / archive_name
    root_name = f"{project['name']}-{project['version']}"

    sources = [
        "README.md",
        "SETUP_GUIDE.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "REPO_METADATA.yml",
        "requirements.txt",
        "pyproject.toml",
        "build_backend.py",
        ".editorconfig",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".env.example",
    ]

    with tarfile.open(archive_path, mode="w:gz", format=tarfile.PAX_FORMAT) as tar:
        root_info = tarfile.TarInfo(root_name)
        root_info.type = tarfile.DIRTYPE
        root_info.mode = 0o755
        root_info.mtime = 0
        tar.addfile(root_info)

        for entry in sources:
            path = ROOT / entry
            data = path.read_bytes()
            info = tarfile.TarInfo(f"{root_name}/{entry}")
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            tar.addfile(info, fileobj=io.BytesIO(data))

        for folder in ("config", "src", "tests"):
            # Include the core source and test tree so sdists stay self-contained.
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_dir() or "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(ROOT).as_posix()
                data = path.read_bytes()
                info = tarfile.TarInfo(f"{root_name}/{rel}")
                info.size = len(data)
                info.mode = 0o644
                info.mtime = 0
                tar.addfile(info, fileobj=io.BytesIO(data))

    return archive_name
