"""Deterministic exporters for review/consumption formats (never a source of truth)."""

from .data_dictionary_excel import build_source_dictionary_workbook

__all__ = ["build_source_dictionary_workbook"]
