"""Keyword-based sentiment analysis for financial news titles."""

from datetime import datetime, timezone
from datetime import datetime as dt
from typing import Dict, List, Tuple

# Weighted keyword dictionaries for financial sentiment.
# Weights indicate signal strength: higher absolute value = stronger signal.

POSITIVE_KEYWORDS: Dict[str, float] = {
    # English
    "surge": 0.8,
    "surges": 0.8,
    "soar": 0.8,
    "soars": 0.8,
    "rally": 0.7,
    "rallies": 0.7,
    "jump": 0.6,
    "jumps": 0.6,
    "gain": 0.5,
    "gains": 0.5,
    "rise": 0.5,
    "rises": 0.5,
    "climb": 0.5,
    "climbs": 0.5,
    "beat": 0.6,
    "beats": 0.6,
    "upgrade": 0.7,
    "upgraded": 0.7,
    "outperform": 0.7,
    "bullish": 0.9,
    "record high": 0.8,
    "all-time high": 0.8,
    "profit": 0.5,
    "growth": 0.5,
    "revenue growth": 0.6,
    "strong earnings": 0.7,
    "beat expectations": 0.7,
    "exceeds": 0.6,
    "dividend": 0.4,
    "buyback": 0.5,
    "buy rating": 0.7,
    "overweight": 0.6,
    "recovery": 0.5,
    "breakout": 0.6,
    "upside": 0.5,
    "boost": 0.5,
    "boosts": 0.5,
    # Chinese
    "營收成長": 0.6,
    "營收增長": 0.6,
    "獲利": 0.5,
    "利多": 0.8,
    "漲停": 0.9,
    "大漲": 0.7,
    "突破": 0.5,
    "上調": 0.7,
    "調升": 0.7,
    "看好": 0.6,
    "看多": 0.6,
    "買進": 0.7,
    "加碼": 0.5,
    "創新高": 0.8,
    "歷史新高": 0.8,
    "轉盈": 0.6,
    "成長動能": 0.5,
    "需求強勁": 0.6,
    "訂單滿載": 0.7,
    "法人買超": 0.5,
    "外資買超": 0.6,
}

NEGATIVE_KEYWORDS: Dict[str, float] = {
    # English
    "crash": 0.9,
    "crashes": 0.9,
    "plunge": 0.8,
    "plunges": 0.8,
    "tumble": 0.7,
    "tumbles": 0.7,
    "drop": 0.5,
    "drops": 0.5,
    "fall": 0.5,
    "falls": 0.5,
    "decline": 0.5,
    "declines": 0.5,
    "sink": 0.6,
    "sinks": 0.6,
    "loss": 0.6,
    "losses": 0.6,
    "miss": 0.5,
    "misses": 0.5,
    "downgrade": 0.7,
    "downgraded": 0.7,
    "underperform": 0.7,
    "bearish": 0.9,
    "sell-off": 0.7,
    "selloff": 0.7,
    "recession": 0.7,
    "default": 0.8,
    "bankruptcy": 0.9,
    "warning": 0.4,
    "warns": 0.4,
    "weak earnings": 0.7,
    "miss expectations": 0.7,
    "below expectations": 0.6,
    "layoff": 0.5,
    "layoffs": 0.5,
    "cut": 0.3,
    "cuts": 0.3,
    "sell rating": 0.7,
    "underweight": 0.6,
    "downside": 0.5,
    "risk": 0.3,
    # Chinese
    "虧損": 0.6,
    "利空": 0.8,
    "跌停": 0.9,
    "大跌": 0.7,
    "暴跌": 0.8,
    "下調": 0.7,
    "調降": 0.7,
    "看空": 0.6,
    "看淡": 0.5,
    "賣出": 0.7,
    "減碼": 0.5,
    "衰退": 0.7,
    "警示": 0.5,
    "違約": 0.8,
    "下市": 0.9,
    "法人賣超": 0.5,
    "外資賣超": 0.6,
    "營收衰退": 0.6,
    "獲利下滑": 0.6,
    "需求疲軟": 0.6,
}


def analyze_title(title: str) -> Tuple[float, str]:
    """Analyze sentiment of a news title using keyword matching.

    Returns:
        Tuple of (score, label) where score is in [-1.0, 1.0]
        and label is one of "bullish", "neutral", "bearish".
    """
    title_lower = title.lower()
    score = 0.0

    for keyword, weight in POSITIVE_KEYWORDS.items():
        if keyword in title_lower or keyword in title:
            score += weight

    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if keyword in title_lower or keyword in title:
            score -= weight

    # Clamp to [-1.0, 1.0]
    score = max(-1.0, min(1.0, score))

    if score > 0.15:
        label = "bullish"
    elif score < -0.15:
        label = "bearish"
    else:
        label = "neutral"

    return score, label


def analyze_news_batch(ticker: str, news_items: List[dict]) -> List[dict]:
    """Analyze a batch of raw yfinance news items.

    Args:
        ticker: The stock ticker symbol.
        news_items: Raw dicts from yfinance Ticker.news.

    Returns:
        List of dicts ready for DB insertion.
    """
    results = []
    now = datetime.now(timezone.utc)

    def _extract_raw_fields(item: dict) -> tuple[str, str, str | None, datetime]:
        """
        Extract (title, url, publisher, published_at) from yfinance news items.

        yfinance has returned multiple shapes over time:
        - Legacy: {"title", "link", "publisher", "providerPublishTime"}
        - Newer: {"content": {"title", "pubDate", "provider": {"displayName"}, "canonicalUrl"/"clickThroughUrl"}}
        """
        content = item.get("content") or {}

        title = item.get("title") or content.get("title") or ""

        url = item.get("link") or ""
        if not url:
            for k in ("canonicalUrl", "clickThroughUrl"):
                u = (content.get(k) or {}).get("url")
                if u:
                    url = u
                    break

        publisher = item.get("publisher") or (content.get("provider") or {}).get("displayName")

        publish_ts = item.get("providerPublishTime")
        if publish_ts is not None:
            published_at = datetime.fromtimestamp(publish_ts, tz=timezone.utc)
        else:
            pub_date = content.get("pubDate") or content.get("displayTime")
            if isinstance(pub_date, str) and pub_date:
                try:
                    published_at = dt.fromisoformat(pub_date.replace("Z", "+00:00")).astimezone(timezone.utc)
                except ValueError:
                    published_at = now
            else:
                published_at = now

        return title, url, publisher, published_at

    for item in news_items:
        title, url, publisher, published_at = _extract_raw_fields(item)
        if not title or not url:
            continue

        sentiment_score, sentiment_label = analyze_title(title)

        results.append(
            {
                "ticker": ticker,
                "title": title,
                "url": url,
                "publisher": publisher,
                "published_at": published_at,
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": sentiment_label,
                "fetched_at": now,
            }
        )

    return results
