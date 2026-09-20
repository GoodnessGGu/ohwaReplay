# Trading Replay Lab 📈🔬

**Trading Replay Lab** is a high-precision desktop trading analysis and manual backtesting workstation built with Python, PyQt6, and TradingView Lightweight Charts.

It enables traders, analysts, and algorithmic strategy designers to replay historical market data candle-by-candle with strict hidden-future enforcement, execute simulated trades with realistic broker mechanics (slippage, spread, commission, and margin), draw technical analysis annotations, track live PnL, journal trades, and compute institutional-grade performance analytics.

---

## 🌟 Key Features

* **Strict Hidden Future Enforcement**: During replay at candle *N*, future price action is completely hidden and inaccessible to prevent hindsight bias.
* **Deterministic Multi-Speed Replay**: Play, pause, step forward, step backward, jump to candle/date, and randomized starting points with configurable speeds (0.1x to 10.0x).
* **Broker-Grade Virtual Execution Engine**:
  * Simulated Market Buy and Sell orders with configurable spreads and slippage.
  * Real-time Stop Loss (SL) and Take Profit (TP) order processing on candle High/Low.
  * Configurable Intrabar Ambiguity execution modes (`CONSERVATIVE`, `SL_FIRST`, `TP_FIRST`, `OPTIMISTIC`).
  * Real-time margin validation, leverage calculations, and commission tracking.
* **Interactive Charting & Overlay System**:
  * Candlestick and volume visualization via Lightweight Charts.
  * Real-time visual SL and TP price lines, active position markers, and exit markers.
* **Analysis & Drawing Tools**:
  * Cursor, Trendline, Ray, Horizontal Line, Vertical Line, Rectangle, Arrow, Text.
  * **Fibonacci Retracement** with configurable ratio levels.
  * **Long/Short Position Setup Tools**: Visualizes entry, SL, TP, risk, reward, and R:R ratios on chart without opening automated trades.
  * Command-based Undo / Redo system (`Ctrl+Z` / `Ctrl+Y`).
* **Institutional Analytics & Statistics**:
  * Total Net Profit, Gross Profit/Loss, Win Rate, Profit Factor.
  * Max Drawdown ($ and %), Average Win/Loss, Expectancy, Win/Loss Streaks, Long vs. Short breakdown.
  * Export completed trade history to CSV.
* **Integrated Trade Journal**:
  * Document trading strategies, setups, psychology notes, and tags for every completed trade.
* **Offline Ready & Synthetic Generator**:
  * Load any standard CSV dataset or generate realistic synthetic market data for `XAUUSD`, `EURUSD`, `GBPUSD`, `USDJPY`, and `BTCUSD`.
* **Workspace Persistence**:
  * Save and reload complete workstation sessions (drawings, account balances, replay states, alerts) to versioned JSON.

---

## 🏗 Architecture

The codebase enforces strict separation of concerns across decoupled layers:

```
                  ┌──────────────────────┐
                  │      Data Layer      │
                  │  (Loader, Resampler) │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │    Replay Engine     │
                  │  (Hidden Future API) │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │   Event Bus Layer    │
                  └──────────┬───────────┘
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Chart Layer   │ │ Account Engine  │ │ Analytics Layer │
│ (PyQt6/WebView) │ │ (Orders, SL/TP) │ │ (Stats, Curves) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🚀 Quick Start

### 1. Requirements
* Python 3.11+
* Windows / macOS / Linux

### 2. Setup Virtual Environment & Install Dependencies

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch Application

```bash
python main.py
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **Space** | Play / Pause Replay |
| **Right Arrow** | Step Forward (Next Candle) |
| **Left Arrow** | Step Backward (Previous Candle) |
| **B** | Execute Market Buy |
| **S** | Execute Market Sell |
| **C** | Close Active Positions |
| **T** | Trendline Tool |
| **R** | Rectangle Tool |
| **F** | Fibonacci Retracement Tool |
| **L** | Long Position Setup Tool |
| **Shift + L** | Short Position Setup Tool |
| **Esc** | Cursor / Cancel Tool |
| **Ctrl + Z** | Undo Drawing |
| **Ctrl + Y** / **Ctrl + Shift + Z** | Redo Drawing |
| **Ctrl + S** | Save Workspace |

---

## 🧪 Testing

Execute the comprehensive automated test suite covering all data validation, resamplers, replay stepping, broker execution, SL/TP triggers, risk calculators, drawings, and analytics:

```bash
pytest
```

---

## ⚙️ Configuration (`config.yaml`)

Custom defaults such as starting balance, default symbol, leverage, commission rates, and chart color themes can be configured in `config.yaml`.
