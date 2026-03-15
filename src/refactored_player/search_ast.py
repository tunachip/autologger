from __future__ import annotations

import re
from dataclasses import dataclass


SEARCH_FIELD_OPTIONS = [
    "$title",
    "$creator",
    "$genre",
    "$summary",
    "$length",
    "$ts",
    "$*",
]


@dataclass(slots=True, frozen=True)
class SearchTerm:
    value: str


@dataclass(slots=True, frozen=True)
class SearchAndClause:
    terms: tuple[SearchTerm, ...]


@dataclass(slots=True, frozen=True)
class SearchQueryAst:
    clauses: tuple[SearchAndClause, ...]


@dataclass(slots=True, frozen=True)
class SearchClause:
    field: str
    negated: bool
    expression: str


@dataclass(slots=True, frozen=True)
class AdvancedSearchQueryAst:
    clauses: tuple[SearchClause, ...]


def is_search_field_token(token: str) -> bool:
    raw = str(token or "").strip()
    if not raw or not raw.startswith("$"):
        return False
    base = raw[1:]
    if base.endswith("!"):
        base = base[:-1]
    if base == "*":
        return True
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", base))


def build_search_ast(query: str) -> SearchQueryAst:
    raw = str(query or "").strip().lower()
    if not raw:
        return SearchQueryAst(clauses=())
    clauses: list[SearchAndClause] = []
    for clause_text in raw.split("|"):
        terms = tuple(
            SearchTerm(value=term)
            for term in (piece.strip() for piece in clause_text.split("&"))
            if term
        )
        if terms:
            clauses.append(SearchAndClause(terms=terms))
    return SearchQueryAst(clauses=tuple(clauses))


def build_advanced_search_ast(query: str) -> AdvancedSearchQueryAst:
    raw = str(query or "").strip()
    if not raw:
        return AdvancedSearchQueryAst(clauses=())
    clauses: list[SearchClause] = []
    for piece in raw.split(";"):
        token = piece.strip()
        if not token:
            continue
        parts = token.split(None, 1)
        head = parts[0].strip()
        tail = parts[1].strip() if len(parts) > 1 else ""
        base = head[1:]
        if base.endswith("!"):
            base = base[:-1]
        negated = head.endswith("!")
        if is_search_field_token(head):
            clauses.append(
                SearchClause(
                    field="ANY" if base == "*" else base.upper(),
                    negated=negated,
                    expression=tail or "*",
                )
            )
            continue
        clauses.append(
            SearchClause(
                field="TS",
                negated=False,
                expression=token,
            )
        )
    return AdvancedSearchQueryAst(clauses=tuple(clauses))


def parse_search_query(query: str) -> list[list[str]]:
    return [
        [term.value for term in clause.terms]
        for clause in build_search_ast(query).clauses
    ]


def parse_advanced_search_query(query: str) -> list[SearchClause]:
    return list(build_advanced_search_ast(query).clauses)
