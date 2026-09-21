from enum import Enum, auto


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class OrderType(str, Enum):
    MARKET_BUY = "MARKET_BUY"
    MARKET_SELL = "MARKET_SELL"
    BUY_LIMIT = "BUY_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_LIMIT = "SELL_LIMIT"
    SELL_STOP = "SELL_STOP"
    CLOSE_POSITION = "CLOSE_POSITION"


class CloseReason(str, Enum):
    MANUAL = "MANUAL"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    MARGIN_CALL = "MARGIN_CALL"


class IntrabarExecutionMode(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"  # Assume SL hits first if both SL and TP in range
    SL_FIRST = "SL_FIRST"
    TP_FIRST = "TP_FIRST"
    OPTIMISTIC = "OPTIMISTIC"
    LOWER_TIMEFRAME = "LOWER_TIMEFRAME"


class ReplayStateEnum(str, Enum):
    IDLE = "IDLE"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class DrawingType(str, Enum):
    CURSOR = "CURSOR"
    TRENDLINE = "TRENDLINE"
    RAY = "RAY"
    HORIZONTAL_LINE = "HORIZONTAL_LINE"
    VERTICAL_LINE = "VERTICAL_LINE"
    RECTANGLE = "RECTANGLE"
    FIBONACCI = "FIBONACCI"
    TEXT = "TEXT"
    ARROW = "ARROW"
    PATH = "PATH"
    VOLUME_PROFILE = "VOLUME_PROFILE"
    LONG_POSITION = "LONG_POSITION"
    SHORT_POSITION = "SHORT_POSITION"


class EventType(str, Enum):
    CANDLE_ADVANCED = "CANDLE_ADVANCED"
    REPLAY_STARTED = "REPLAY_STARTED"
    REPLAY_PAUSED = "REPLAY_PAUSED"
    REPLAY_RESET = "REPLAY_RESET"
    REPLAY_COMPLETED = "REPLAY_COMPLETED"
    ORDER_OPENED = "ORDER_OPENED"
    ORDER_CLOSED = "ORDER_CLOSED"
    PENDING_ORDER_CREATED = "PENDING_ORDER_CREATED"
    PENDING_ORDER_CANCELLED = "PENDING_ORDER_CANCELLED"
    PENDING_ORDER_TRIGGERED = "PENDING_ORDER_TRIGGERED"
    POSITION_UPDATED = "POSITION_UPDATED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    SL_HIT = "SL_HIT"
    TP_HIT = "TP_HIT"
    PRICE_ALERT = "PRICE_ALERT"
    DRAWING_CREATED = "DRAWING_CREATED"
    DRAWING_UPDATED = "DRAWING_UPDATED"
    DRAWING_DELETED = "DRAWING_DELETED"
    WORKSPACE_SAVED = "WORKSPACE_SAVED"
    WORKSPACE_LOADED = "WORKSPACE_LOADED"
    TIMEFRAME_CHANGED = "TIMEFRAME_CHANGED"
    DATA_LOADED = "DATA_LOADED"


# Supported standard timeframes
TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"]

TIMEFRAME_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}

ASSET_CATEGORIES = {
    "Forex Majors": [
        ("EURUSD", "Euro / US Dollar"),
        ("GBPUSD", "British Pound / US Dollar"),
        ("USDJPY", "US Dollar / Japanese Yen"),
        ("AUDUSD", "Australian Dollar / US Dollar"),
        ("USDCAD", "US Dollar / Canadian Dollar"),
        ("USDCHF", "US Dollar / Swiss Franc"),
        ("NZDUSD", "New Zealand Dollar / US Dollar"),
    ],
    "Forex Crosses": [
        ("EURGBP", "Euro / British Pound"),
        ("EURJPY", "Euro / Japanese Yen"),
        ("GBPJPY", "British Pound / Japanese Yen"),
        ("AUDJPY", "Australian Dollar / Japanese Yen"),
        ("EURAUD", "Euro / Australian Dollar"),
        ("CADJPY", "Canadian Dollar / Japanese Yen"),
        ("GBPAUD", "British Pound / Australian Dollar"),
    ],
    "Metals & Commodities": [
        ("XAUUSD", "Spot Gold / US Dollar"),
        ("XAGUSD", "Spot Silver / US Dollar"),
        ("USOIL", "WTI Crude Oil"),
        ("UKOIL", "Brent Crude Oil"),
    ],
    "Indices": [
        ("US30", "Dow Jones Industrial Average"),
        ("NAS100", "Nasdaq 100 Index"),
        ("SPX500", "S&P 500 Index"),
        ("GER40", "German DAX 40"),
    ],
    "Crypto (24/7)": [
        ("BTCUSD", "Bitcoin / US Dollar"),
        ("ETHUSD", "Ethereum / US Dollar"),
        ("SOLUSD", "Solana / US Dollar"),
        ("XRPUSD", "Ripple / US Dollar"),
        ("BNBUSD", "Binance Coin / US Dollar"),
    ],
}
