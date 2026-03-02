"""TradingView webhook schema adapter.

TradingView alert payloads typically look like:

    {"ticker": "SPY", "action": "buy", "price": 450.50, "volume": 1234567}

or with nested strategy:

    {"ticker": "SPY", "strategy": {"order": {"action": "sell", "price": 448.0}}}

Field mapping:
    ticker / symbol   → symbol
    action (buy/sell/long/short/exit/close) → direction (long/short/flat)
    price / close     → entry_zone
"""

from typing import Any

from sigmatic.server.adapters.base import BaseAdapter

# Maps TradingView action strings → canonical direction
_ACTION_MAP: dict[str, str] = {
    "buy": "long",
    "long": "long",
    "sell": "short",
    "short": "short",
    "exit": "flat",
    "close": "flat",
    "exit_long": "flat",
    "exit_short": "flat",
}


class TradingViewAdapter(BaseAdapter):
    """Adapter for TradingView alert webhook payloads."""

    def normalize(
        self, raw_payload: dict[str, Any], source_config: dict[str, Any]
    ) -> dict[str, Any]:
        # Symbol: prefer "ticker", fall back to "symbol"
        symbol = raw_payload.get("ticker") or raw_payload.get("symbol")
        if not symbol:
            raise ValueError("TradingView payload missing 'ticker' or 'symbol' field")

        # Direction: check top-level "action", then nested strategy path
        action_raw = (
            raw_payload.get("action")
            or raw_payload.get("strategy", {}).get("order", {}).get("action")
        )
        if not action_raw:
            raise ValueError("TradingView payload missing 'action' field")

        direction = _ACTION_MAP.get(str(action_raw).strip().lower())
        if direction is None:
            raise ValueError(
                f"Unknown TradingView action '{action_raw}'. "
                f"Expected one of: {sorted(_ACTION_MAP)}"
            )

        # Entry zone: prefer explicit "price", then "close"
        entry_zone: float | None = None
        for price_key in ("price", "close"):
            raw_price = raw_payload.get(price_key)
            if raw_price is not None:
                try:
                    entry_zone = float(raw_price)
                except (TypeError, ValueError):
                    pass
                break

        return {
            "symbol": str(symbol).strip(),
            "direction": direction,
            "entry_zone": entry_zone,
            "timeframe": raw_payload.get("interval") or raw_payload.get("timeframe"),
            "strategy_id": raw_payload.get("strategy_id"),
        }
