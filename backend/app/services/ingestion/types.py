"""Parser output types. Parsers know file layouts only; they never touch the DB."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class ValueRecord:
    name: str
    value: float | None
    unit: str | None
    record_kind: str
    source_row: int | None = None
    statistic: str | None = None
    qualifier: str | None = None
    name_original: str | None = None
    upstream_file: str | None = None


@dataclass
class ExperimentRecord:
    test_label: str
    record_kind: str
    source_row: int
    material: str | None = None
    fuel: str | None = None
    parent_label: str | None = None
    description: str | None = None
    date_text: str | None = None
    upstream_file: str | None = None
    # Attach measurements to an experiment created by another file (matched on
    # investigation + material + test_label) instead of creating one.
    attach_only: bool = False
    conditions: list[ValueRecord] = field(default_factory=list)
    combustion: list[ValueRecord] = field(default_factory=list)
    smoke: list[ValueRecord] = field(default_factory=list)


@dataclass
class Issue:
    severity: str  # info | warning | error
    code: str
    message: str
    source_row: int | None = None
    column: str | None = None


@dataclass
class ParseResult:
    rows_read: int
    experiments: list[ExperimentRecord] = field(default_factory=list)
    loose_combustion: list[ValueRecord] = field(default_factory=list)
    loose_smoke: list[ValueRecord] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


class Parser(Protocol):
    name: str
    version: str

    def parse(self, path: Path) -> ParseResult: ...
