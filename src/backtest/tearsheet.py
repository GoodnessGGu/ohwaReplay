import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.backtest.engine import BacktestResult


class TearsheetGenerator:
    """
    Generates professional standalone interactive HTML performance tearsheet reports.
    """

    @staticmethod
    def generate_html(result: BacktestResult, title: str = "Strategy Backtest Performance Tearsheet") -> str:
        res_dict = result.to_dict()
        profit_color = "#26a69a" if result.total_net_profit >= 0 else "#ef5350"
        ret_color = "#26a69a" if result.return_pct >= 0 else "#ef5350"

        # Prepare JSON data for embedded charts
        eq_data_json = json.dumps(result.equity_curve)
        trades_json = json.dumps([t.__dict__ for t in result.trades])

        # Trade rows HTML
        trade_rows = []
        for t in result.trades:
            pnl_col = "#26a69a" if t.net_pnl >= 0 else "#ef5350"
            entry_dt = datetime.utcfromtimestamp(t.entry_time).strftime("%Y-%m-%d %H:%M") if t.entry_time else "--"
            exit_dt = datetime.utcfromtimestamp(t.exit_time).strftime("%Y-%m-%d %H:%M") if t.exit_time else "--"
            dir_str = t.direction.value if hasattr(t.direction, "value") else str(t.direction)

            trade_rows.append(f"""
            <tr>
              <td>#{t.id}</td>
              <td><b>{dir_str}</b></td>
              <td>{entry_dt}</td>
              <td>{t.entry_price:.2f}</td>
              <td>{exit_dt}</td>
              <td>{t.exit_price:.2f}</td>
              <td>{t.lot_size:.2f}</td>
              <td style="color:{pnl_col};font-weight:bold;">${t.net_pnl:+,.2f}</td>
              <td><span class="badge badge-{t.exit_reason.lower()}">{t.exit_reason}</span></td>
              <td style="color:#848e9c;font-size:11px;">{t.comment}</td>
            </tr>
            """)
        trades_html = "\n".join(trade_rows) if trade_rows else '<tr><td colspan="10" style="text-align:center;color:#848e9c;">No trades executed</td></tr>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} - {result.strategy_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #131722;
    --card-bg: #1e222d;
    --border: #2a2e39;
    --text: #d1d4dc;
    --text-muted: #848e9c;
    --green: #26a69a;
    --red: #ef5350;
    --blue: #2962ff;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background-color: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    padding: 24px;
    line-height: 1.5;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
    margin-bottom: 24px;
  }}
  h1 {{ font-size: 24px; font-weight: 700; color: #ffffff; }}
  .meta-tag {{
    background: #2a2e39;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
    color: var(--blue);
  }}
  .grid-cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }}
  .card-label {{ font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }}
  .card-value {{ font-size: 20px; font-weight: 700; }}

  .chart-section {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
  }}
  .chart-title {{ font-size: 14px; font-weight: 700; margin-bottom: 14px; color: #ffffff; }}
  .chart-container {{ position: relative; height: 320px; width: 100%; }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    text-align: left;
  }}
  th {{
    background: #2a2e39;
    color: var(--text-muted);
    padding: 10px 12px;
    font-weight: 600;
  }}
  td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}
  .badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 700;
    font-size: 10px;
  }}
  .badge-tp {{ background: rgba(38, 166, 154, 0.2); color: var(--green); }}
  .badge-sl {{ background: rgba(239, 83, 80, 0.2); color: var(--red); }}

  footer {{
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 30px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>{result.strategy_name}</h1>
      <p style="color:var(--text-muted);font-size:12px;margin-top:4px;">
        Symbol: <b>{result.symbol}</b> | Timeframe: <b>{result.timeframe}</b> | Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
      </p>
    </div>
    <div>
      <span class="meta-tag">TRADING REPLAY LAB</span>
      <span class="meta-tag">QUANT BACKTEST</span>
    </div>
  </header>

  <!-- KPI Overview -->
  <div class="grid-cards">
    <div class="card">
      <div class="card-label">Net Profit</div>
      <div class="card-value" style="color:{profit_color};">${result.total_net_profit:+,.2f}</div>
    </div>
    <div class="card">
      <div class="card-label">Return on Capital</div>
      <div class="card-value" style="color:{ret_color};">{result.return_pct:+,.2f}%</div>
    </div>
    <div class="card">
      <div class="card-label">Profit Factor</div>
      <div class="card-value">{result.profit_factor:.2f}</div>
    </div>
    <div class="card">
      <div class="card-label">Win Rate</div>
      <div class="card-value">{result.win_rate_pct:.1f}% ({result.winning_trades}W / {result.losing_trades}L)</div>
    </div>
    <div class="card">
      <div class="card-label">Max Drawdown</div>
      <div class="card-value" style="color:var(--red);">${result.max_drawdown_amount:,.2f} ({result.max_drawdown_pct:.2f}%)</div>
    </div>
    <div class="card">
      <div class="card-label">Sharpe Ratio</div>
      <div class="card-value">{result.sharpe_ratio:.2f}</div>
    </div>
    <div class="card">
      <div class="card-label">Sortino Ratio</div>
      <div class="card-value">{result.sortino_ratio:.2f}</div>
    </div>
    <div class="card">
      <div class="card-label">Trade Expectancy</div>
      <div class="card-value">${result.expectancy:+,.2f}</div>
    </div>
  </div>

  <!-- Interactive Equity Chart -->
  <div class="chart-section">
    <div class="chart-title">📈 Cumulative Equity Curve & Growth ($)</div>
    <div class="chart-container">
      <canvas id="equityChart"></canvas>
    </div>
  </div>

  <!-- Trade Log Table -->
  <div class="chart-section">
    <div class="chart-title">📋 Executed Trades Log ({result.total_trades} Trades)</div>
    <div style="overflow-x:auto;max-height:400px;">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Entry Date</th>
            <th>Entry Price</th>
            <th>Exit Date</th>
            <th>Exit Price</th>
            <th>Volume</th>
            <th>Net PnL</th>
            <th>Exit Reason</th>
            <th>Strategy Tag</th>
          </tr>
        </thead>
        <tbody>
          {trades_html}
        </tbody>
      </table>
    </div>
  </div>

  <footer>
    Automated Quantitative Performance Report &bull; Generated by Trading Replay Lab Engine
  </footer>
</div>

<script>
  const rawEquity = {eq_data_json};
  const labels = rawEquity.map(pt => {{
    const d = new Date(pt.time * 1000);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {{hour:'2-digit', minute:'2-digit'}});
  }});
  const eqValues = rawEquity.map(pt => pt.equity);
  const balValues = rawEquity.map(pt => pt.balance);

  const ctx = document.getElementById('equityChart').getContext('2d');
  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: labels,
      datasets: [
        {{
          label: 'Equity ($)',
          data: eqValues,
          borderColor: '#26a69a',
          backgroundColor: 'rgba(38, 166, 154, 0.12)',
          borderWidth: 2,
          fill: true,
          tension: 0.1,
          pointRadius: eqValues.length > 50 ? 0 : 3,
        }},
        {{
          label: 'Realized Balance ($)',
          data: balValues,
          borderColor: '#2962ff',
          borderWidth: 1.5,
          borderDash: [4, 4],
          fill: false,
          pointRadius: 0,
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ intersect: false, mode: 'index' }},
      plugins: {{
        legend: {{ labels: {{ color: '#d1d4dc', font: {{ size: 11 }} }} }}
      }},
      scales: {{
        x: {{
          grid: {{ color: '#2a2e39' }},
          ticks: {{ color: '#848e9c', maxTicksLimit: 10, font: {{ size: 10 }} }}
        }},
        y: {{
          grid: {{ color: '#2a2e39' }},
          ticks: {{
            color: '#848e9c',
            font: {{ size: 10 }},
            callback: (v) => '$' + v.toLocaleString()
          }}
        }}
      }}
    }}
  }});
</script>
</body>
</html>
"""

    @staticmethod
    def save_tearsheet(result: BacktestResult, output_path: str = "reports/backtest_tearsheet.html") -> str:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        html = TearsheetGenerator.generate_html(result)
        out_file.write_text(html, encoding="utf-8")
        return str(out_file.resolve())
