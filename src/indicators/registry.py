from typing import Dict, List, Type
from src.indicators.base_indicator import BaseIndicator
from src.indicators.all_indicators import (
    EMAIndicator,
    SMAIndicator,
    RSIIndicator,
    MACDIndicator,
    ATRIndicator,
    BollingerBandsIndicator,
    SmartTrailIndicator,
    FVGIndicator,
    MarketStructureIndicator,
)


class IndicatorRegistry:
    """Central registry of available technical indicators."""

    _indicators: Dict[str, Type[BaseIndicator]] = {
        "EMA": EMAIndicator,
        "SMA": SMAIndicator,
        "RSI": RSIIndicator,
        "MACD": MACDIndicator,
        "ATR": ATRIndicator,
        "BollingerBands": BollingerBandsIndicator,
        "SmartTrail": SmartTrailIndicator,
        "FVG": FVGIndicator,
        "MarketStructure": MarketStructureIndicator,
    }

    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseIndicator]]:
        return cls._indicators

    @classmethod
    def get(cls, name: str) -> Type[BaseIndicator]:
        return cls._indicators.get(name)

    @classmethod
    def register(cls, name: str, indicator_cls: Type[BaseIndicator]) -> None:
        cls._indicators[name] = indicator_cls

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseIndicator:
        ind_cls = cls._indicators.get(name)
        if not ind_cls:
            raise ValueError(f"Unknown indicator: {name}")
        return ind_cls(**kwargs)
