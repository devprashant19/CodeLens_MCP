from dataclasses import dataclass


@dataclass
class ChunkResult:
    file_path: str
    start_line: int
    end_line: int
    code_text: str
    symbol_name: str
    symbol_type: str
    parent_symbol: str | None

@dataclass
class SearchResult(ChunkResult):
    distance: float
    relevance_score: float

@dataclass
class StructureEntry:
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    parent_symbol: str | None
