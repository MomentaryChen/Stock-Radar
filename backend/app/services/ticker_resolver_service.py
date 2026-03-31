"""Resolve ticker identifiers from ticker code or localized names."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.market_data_service import MarketDataService
from backend.core import data as core_data


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _normalize_ticker_code(raw: str) -> str:
    value = raw.strip().upper()
    if not value:
        return ""
    if value.endswith(".TW") or value.endswith(".TWO"):
        return value
    if value.isdigit():
        return f"{value}.TW"
    return value


def _looks_like_ticker(value: str) -> bool:
    if not value:
        return False
    if value.endswith(".TW") or value.endswith(".TWO"):
        return True
    if value.isdigit():
        return True
    if "." in value:
        return True
    return value.isalnum() and len(value) <= 6


async def resolve_identifier_to_ticker(session: AsyncSession, raw: str) -> str:
    """Resolve input to ticker code, supporting Chinese/English names."""
    candidate = raw.strip()
    if not candidate:
        return ""

    # Fast path for regular ticker inputs.
    normalized = _normalize_ticker_code(candidate)
    if not _has_cjk(candidate) and _looks_like_ticker(normalized):
        return normalized

    market_data_service = MarketDataService(session)

    # Resolve by cached ticker profile names first.
    mapped = await market_data_service.find_ticker_by_name(candidate)
    if mapped:
        return _normalize_ticker_code(mapped)

    # Fallback: resolve Chinese company name via TWSE mapping.
    if _has_cjk(candidate):
        twse_map = await asyncio.to_thread(core_data.fetch_twse_name_map)
        reverse_map = {name.strip(): code.strip() for code, name in twse_map.items() if name and code}
        twse_code = reverse_map.get(candidate)
        if twse_code:
            return _normalize_ticker_code(twse_code)

    return normalized
