from dataclasses import dataclass


@dataclass
class SymbolLocation:
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str
    parent_symbol: str | None

@dataclass
class ChunkResult(SymbolLocation):
    code_text: str

@dataclass
class SearchResult(ChunkResult):
    distance: float
    relevance_score: float

@dataclass
class StructureEntry(SymbolLocation):
    pass
