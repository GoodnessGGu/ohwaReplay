from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class BaseIndicator(ABC):
    """Base class for all technical indicators."""

    name: str = "BaseIndicator"
    display_name: str = "Base Indicator"
    overlay: bool = True  # True if rendered on main chart, False if in separate panel (e.g. RSI, MACD)

    def __init__(self, **params: Any):
        self.params: Dict[str, Any] = params

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates indicator values from OHLCV dataframe.
        Returns a DataFrame containing the calculated series aligned with original index.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "overlay": self.overlay,
            "params": self.params,
        }
