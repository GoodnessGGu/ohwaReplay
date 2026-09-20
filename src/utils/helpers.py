import yaml
from pathlib import Path
from typing import Any, Dict


def load_yaml_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Loads configuration from a YAML file safely."""
    p = Path(config_path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}
    except Exception as e:
        print(f"Error loading config {config_path}: {e}")
        return {}


def format_currency(value: float, symbol: str = "$", decimals: int = 2) -> str:
    """Formats numeric values nicely as currency."""
    prefix = "+" if value > 0 else ""
    return f"{prefix}{symbol}{value:,.{decimals}f}" if value != 0 else f"{symbol}0.00"


def format_price(price: float, digits: int = 2) -> str:
    """Formats price to specified precision."""
    return f"{price:.{digits}f}"
