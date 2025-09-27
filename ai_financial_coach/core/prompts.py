from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptLoader:
    """Utility to load and cache prompt templates from disk."""

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self.base_path = Path(base_path) if base_path else DEFAULT_PROMPTS_DIR
        self._cache: Dict[str, str] = {}

    def _resolve_file(self, name: str) -> Path:
        path = self.base_path / name
        if path.suffix:
            return path
        return self.base_path / f"{name}.txt"

    def load(self, name: str, *, use_cache: bool = True) -> str:
        key = Path(name).stem
        if use_cache and key in self._cache:
            return self._cache[key]

        file_path = self._resolve_file(name)
        text = file_path.read_text(encoding="utf-8")
        self._cache[key] = text
        return text

    def load_all(self) -> Dict[str, str]:
        prompts: Dict[str, str] = {}
        for file_path in sorted(self.base_path.glob("*.txt")):
            prompts[file_path.stem] = self.load(file_path.name)
        return prompts

    def refresh(self, names: Optional[Iterable[str]] = None) -> None:
        if names is None:
            self._cache.clear()
        else:
            for name in names:
                self._cache.pop(Path(name).stem, None)


_default_loader = PromptLoader()


def load_prompt(name: str, *, use_cache: bool = True) -> str:
    return _default_loader.load(name, use_cache=use_cache)


def load_all_prompts() -> Dict[str, str]:
    return _default_loader.load_all()
