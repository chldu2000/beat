"""Errors and warnings with source locations, phrased so an agent can act on them."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    level: str  # "error" | "warning"
    where: str
    message: str

    def __str__(self) -> str:
        if self.where:
            return f"[{self.level}] {self.where}: {self.message}"
        return f"[{self.level}] {self.message}"

    def to_dict(self) -> dict:
        return {"level": self.level, "where": self.where, "message": self.message}


class Diagnostics:
    def __init__(self) -> None:
        self.items: list[Diagnostic] = []

    def _add(self, level: str, where: str, message: str) -> None:
        d = Diagnostic(level, where, message)
        # Patterns are parsed once per use, so the same problem can be reported repeatedly.
        if d not in self.items:
            self.items.append(d)

    def error(self, where: str, message: str) -> None:
        self._add("error", where, message)

    def warn(self, where: str, message: str) -> None:
        self._add("warning", where, message)

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.items if d.level == "error"]

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.items if d.level == "warning"]

    @property
    def has_errors(self) -> bool:
        return any(d.level == "error" for d in self.items)


def loc(*parts: object) -> str:
    """Join location parts, skipping empty ones: loc("verse#1", "bs", "bar 3")."""
    return " > ".join(str(p) for p in parts if p not in (None, ""))
