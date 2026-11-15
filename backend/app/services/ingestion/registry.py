from app.services.ingestion.parsers.psi115 import Psi115SummaryParser
from app.services.ingestion.parsers.psi117 import Psi117ExtinctionParser
from app.services.ingestion.parsers.same_r import (
    SameRDetectionByMaterialParser, SameRDetectionByTestParser, SameRTableParser,
)
from app.services.ingestion.types import Parser

PARSERS: dict[str, Parser] = {
    p.name: p
    for p in (SameRTableParser(), SameRDetectionByTestParser(), SameRDetectionByMaterialParser(),
              Psi115SummaryParser(), Psi117ExtinctionParser())
}


def get_parser(name: str) -> Parser:
    try:
        return PARSERS[name]
    except KeyError:
        raise ValueError(f"Unknown parser {name!r}. Known: {sorted(PARSERS)}") from None
