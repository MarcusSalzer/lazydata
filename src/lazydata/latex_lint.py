"""Simple utility for linting a latex manuscript."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class DocumentStats:
    """Things found in the manuscript."""


@dataclass
class LatexLinter:
    """Settings."""

    crossref_mode: Literal["ref", "cref", "Cref"] = "Cref"

    found: DocumentStats | None = None

    def _check_bibtex(self, f: Path):
        """Extract keys from bibtex"""

    def lint(self, project_dir: Path) -> None:
        assert project_dir.is_dir()
