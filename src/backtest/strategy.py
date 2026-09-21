from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd

from src.utils.constants import Direction


class BaseStrategy(ABC):
    """
    Abstract base class for rule-based automated trading strategies.
    """
    name: str = "BaseStrategy"
    description: str = "Base Strategy"

    def __init__(self, **params: Any):
        self.params = params

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyzes the historical OHLCV DataFrame and returns a signals DataFrame
        with columns:
        - 'signal': 1 (BUY), -1 (SELL), 0 (HOLD)
        - 'stop_loss': float price
        - 'take_profit': float price
        - 'comment': str reason
        """
        pass
