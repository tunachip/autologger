from __future__ import annotations

from .search_ast import (
    SEARCH_FIELD_OPTIONS,
    SearchClause,
    build_search_ast,
    is_search_field_token,
    parse_advanced_search_query as _parse_advanced_search_query,
)


def format_hms(seconds: float) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    remainder = total % 60
    return f"{hours:02d}:{minutes:02d}:{remainder:02d}"


def parse_search_query(query: str) -> list[list[str]]:
    return [
        [term.value for term in clause.terms]
        for clause in
        build_search_ast(query).clauses
    ]


def search_terms(query: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for clause in parse_search_query(query):
        for term in clause:
            if term in seen:
                continue
            seen.add(term)
            ordered.append(term)
    return ordered


def matches_search_query(text: str, query: str) -> bool:
    haystack = str(text or "").lower()
    clauses = parse_search_query(query)
    if not clauses:
        return True
    return any(all(term in haystack for term in clause) for clause in clauses)


def parse_advanced_search_query(query: str) -> list[SearchClause]:
    return _parse_advanced_search_query(query)
