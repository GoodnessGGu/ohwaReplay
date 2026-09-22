from pathlib import Path


def get_chart_html(theme: str = "dark") -> str:
    """
    Returns self-contained offline-ready interactive HTML containing
    Lightweight Charts, high-framerate drawing engine with specialized floating properties toolbar
    for Long/Short position setups vs standard shapes, borderless green/red risk-reward zones,
    dynamic trade progression fill (denser ONLY on the relevant TP or SL region),
    hover-only compact typography, single-click instant drop, 8-handle rectangles, and fail-safe coordinate scaling.
    """
    bg_color = "#131722" if theme == "dark" else "#ffffff"
    text_color = "#d1d4dc" if theme == "dark" else "#191919"
    grid_color = "#1e222d" if theme == "dark" else "#f0f3fa"

    local_js_path = Path("assets/js/lightweight-charts.standalone.production.js")
    if local_js_path.exists():
        with open(local_js_path, "r", encoding="utf-8") as f:
            js_bundle = f"<script>\n{f.read()}\n</script>"
    else:
        js_bundle = '<script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Trading Replay Chart</title>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
{js_bundle}
<style>
  html, body {{
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background-color: {bg_color};
    user-select: none;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  }}
  #chart-container {{
    width: 100%;
    height: 100%;
    position: relative;
  }}
  #drawing-canvas {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
    pointer-events: none;
  }}
  #active-tool-banner {{
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(30, 34, 45, 0.95);
    color: #2962ff;
    border: 1px solid #2962ff;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    display: none;
    z-index: 30;
    box-shadow: 0 4px 12px rgba(0,0,0,0.6);
    pointer-events: none;
  }}
  #watermark {{
    position: absolute;
    bottom: 30px;
    left: 20px;
    font-size: 26px;
    font-weight: 800;
    color: rgba(255, 255, 255, 0.04);
    pointer-events: none;
    z-index: 5;
    letter-spacing: 2px;
  }}

  /* Floating Drawing Property Toolbar */
  #drawing-prop-toolbar {{
    position: absolute;
    display: none;
    align-items: center;
    gap: 6px;
    background: #1e222d;
    border: 1px solid #363c4e;
    box-shadow: 0 6px 20px rgba(0,0,0,0.85);
    border-radius: 6px;
    padding: 4px 8px;
    z-index: 50;
    color: #d1d4dc;
    font-size: 11px;
  }}
  #drawing-prop-toolbar button, #drawing-prop-toolbar select, #drawing-prop-toolbar input {{
    background: #2a2e39;
    border: 1px solid #434651;
    color: #d1d4dc;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 11px;
    cursor: pointer;
    outline: none;
    height: 24px;
    box-sizing: border-box;
  }}
  #drawing-prop-toolbar button:hover, #drawing-prop-toolbar select:hover {{
    background: #363c4e;
    border-color: #2962ff;
  }}
  #drawing-prop-toolbar .separator {{
    width: 1px;
    height: 18px;
    background: #434651;
    margin: 0 2px;
  }}
  .prop-tool-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 6px !important;
  }}
  .prop-label {{
    font-size: 10px;
    color: #848e9c;
    font-weight: 600;
  }}
  #prop-drag-handle {{
    cursor: grab;
    color: #848e9c;
    padding: 2px 4px;
    user-select: none;
    font-size: 13px;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  #prop-drag-handle:hover {{
    color: #2962ff;
  }}
</style>
</head>
<body>
<div id="chart-container">
  <div id="watermark">TRADING REPLAY LAB</div>
  <div id="active-tool-banner">TOOL: CURSOR</div>

  <!-- Floating Drawing Property Toolbar -->
  <div id="drawing-prop-toolbar">
    <div id="prop-drag-handle" title="Drag to move toolbar">⠿</div>
    <!-- Standard Drawing Controls (Rectangles, Lines, etc.) -->
    <div id="prop-standard-controls" style="display:flex;align-items:center;gap:6px;">
      <span class="prop-label">Line:</span>
      <input type="color" id="prop-outline-color" title="Outline Color" style="width:24px;height:22px;padding:0;cursor:pointer;border:1px solid #434651;border-radius:3px;background:none;" />
      
      <select id="prop-line-width" title="Line Thickness">
        <option value="0.5">0.5px</option>
        <option value="1">1px</option>
        <option value="1.5">1.5px</option>
        <option value="2">2px</option>
        <option value="3">3px</option>
        <option value="4">4px</option>
      </select>

      <select id="prop-line-style" title="Line Style">
        <option value="solid">― Solid</option>
        <option value="dashed">-- Dashed</option>
        <option value="dotted">··· Dotted</option>
      </select>

      <div class="separator"></div>

      <span class="prop-label">Fill:</span>
      <input type="color" id="prop-fill-color" title="Fill Color" style="width:24px;height:22px;padding:0;cursor:pointer;border:1px solid #434651;border-radius:3px;background:none;" />
      
      <select id="prop-fill-opacity" title="Fill Opacity">
        <option value="0">0%</option>
        <option value="0.10">10%</option>
        <option value="0.20">20%</option>
        <option value="0.35">35%</option>
        <option value="0.50">50%</option>
        <option value="0.80">80%</option>
      </select>

      <div class="separator"></div>

      <input type="text" id="prop-text-input" placeholder="Text Label..." title="Drawing Text" style="width: 80px;" />

      <div class="separator"></div>
    </div>

    <!-- Position Setup Specific Controls (Long / Short) -->
    <div id="prop-position-controls" style="display:none;align-items:center;gap:6px;">
      <span id="prop-pos-type-badge" style="font-weight:700;padding:2px 7px;border-radius:4px;font-size:10px;">LONG</span>
      <span id="prop-pos-rr-badge" style="background:#2a2e39;border:1px solid #434651;border-radius:4px;padding:2px 7px;font-size:10px;color:#ffffff;font-weight:600;">R:R 2.00</span>
      <span id="prop-pos-risk-badge" style="color:#ef5350;font-size:10px;font-weight:600;">Risk: -10.00</span>
      <span id="prop-pos-reward-badge" style="color:#26a69a;font-size:10px;font-weight:600;">Target: +20.00</span>
      <button id="prop-btn-exec-trade" title="Execute Market Order with this SL/TP" style="background:#26a69a;color:#ffffff;font-weight:700;font-size:11px;padding:3px 8px;border:none;border-radius:3px;cursor:pointer;display:flex;align-items:center;gap:4px;">⚡ Buy Market</button>
      <button id="prop-btn-exec-limit" title="Place Pending Limit/Stop Order" style="background:#2962ff;color:#ffffff;font-weight:700;font-size:11px;padding:3px 8px;border:none;border-radius:3px;cursor:pointer;display:flex;align-items:center;gap:4px;">⏳ Set Limit</button>
      <button id="prop-btn-move-be" title="Move Stop Loss to Break Even" style="background:#ff9800;color:#131722;font-weight:700;font-size:11px;padding:3px 8px;border:none;border-radius:3px;cursor:pointer;display:flex;align-items:center;gap:4px;">⚡ Move to BE</button>
      <button id="prop-btn-apply-panel" title="Copy SL and TP to Right-Side Execution Panel" style="background:#2a2e39;color:#d1d4dc;font-weight:600;font-size:11px;padding:3px 7px;border:1px solid #434651;border-radius:3px;cursor:pointer;">📋 Copy to Panel</button>
      <div class="separator"></div>
    </div>

    <!-- Shared Actions -->
    <button id="prop-btn-lock" title="Lock / Unlock" class="prop-tool-btn">🔒</button>
    <button id="prop-btn-settings" title="Full Properties Dialog" class="prop-tool-btn">⚙</button>
    <button id="prop-btn-delete" title="Delete Drawing" style="color: #ef5350;" class="prop-tool-btn">🗑</button>
  </div>

  <canvas id="drawing-canvas"></canvas>
</div>

<script>
  let chart, candleSeries, volumeSeries;
  let currentSymbol = "XAUUSD";
  let activeTool = "CURSOR";
  let drawings = [];
  let tempDrawingPoints = [];
  let liveMousePoint = null;
  let isCreatingDrawing = false;
  let startCreationPoint = null;
  let tradeOverlays = {{ lines: [], markers: [] }};
  let currentCandles = [];

  let selectedDrawingId = null;
  let hoveredDrawingId = null;
  let draggingHandle = null;
  let isShiftPressed = false;
  let toolbarDragOffset = {{ x: 0, y: 0 }};
  let isDraggingToolbar = false;
  let lastSelectedDrawingId = null;

  const container = document.getElementById('chart-container');
  const canvas = document.getElementById('drawing-canvas');
  const ctx = canvas.getContext('2d');
  const toolBanner = document.getElementById('active-tool-banner');
  const propToolbar = document.getElementById('drawing-prop-toolbar');

  // Setup QWebChannel if available
  if (typeof QWebChannel !== 'undefined') {{
    new QWebChannel(qt.webChannelTransport, function (channel) {{
      window.qtBridge = channel.objects.qtBridge;
    }});
  }}

  let rafScheduled = false;
  function scheduleRender() {{
    if (!rafScheduled) {{
      rafScheduled = true;
      requestAnimationFrame(() => {{
        renderDrawings();
        updatePropToolbarPosition();
        rafScheduled = false;
      }});
    }}
  }}

  function resizeCanvas() {{
    canvas.width = container.clientWidth * window.devicePixelRatio;
    canvas.height = container.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    scheduleRender();
  }}

  function initChart() {{
    chart = LightweightCharts.createChart(container, {{
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {{
        background: {{ type: 'solid', color: '{bg_color}' }},
        textColor: '{text_color}',
      }},
      grid: {{
        vertLines: {{ color: '{grid_color}' }},
        horzLines: {{ color: '{grid_color}' }},
      }},
      crosshair: {{
        mode: LightweightCharts.CrosshairMode.Normal,
      }},
      rightPriceScale: {{
        borderColor: '{grid_color}',
        scaleMargins: {{
          top: 0.1,
          bottom: 0.2,
        }},
      }},
      timeScale: {{
        borderColor: '{grid_color}',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 9,
      }},
    }});

    candleSeries = chart.addCandlestickSeries({{
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceLineVisible: true,
      lastValueVisible: true,
      priceLineColor: '#2962ff',
    }});


    volumeSeries = chart.addHistogramSeries({{
      color: '#26a69a',
      priceFormat: {{ type: 'volume' }},
      priceScaleId: '',
      scaleMargins: {{
        top: 0.8,
        bottom: 0,
      }},
      visible: false,
    }});

    window.addEventListener('resize', () => {{
      chart.applyOptions({{ width: container.clientWidth, height: container.clientHeight }});
      resizeCanvas();
    }});

    // Continuous redraw listeners
    chart.timeScale().subscribeVisibleTimeRangeChange(() => scheduleRender());
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {{
      if (range) {{
        lastSavedLogicalRange = range;
        if (window.qtBridge && window.qtBridge.onVisibleRangeChanged) {{
          window.qtBridge.onVisibleRangeChanged(JSON.stringify(range));
        }}
      }}
      scheduleRender();
    }});
    container.addEventListener('mousemove', () => scheduleRender(), {{ passive: true }});
    container.addEventListener('wheel', () => scheduleRender(), {{ passive: true }});

    setupInteractionEvents();
    setupPropertyToolbarEvents();
    resizeCanvas();
  }}

  let lastSavedLogicalRange = null;

  // Bridge functions
  function setSymbol(symbol) {{
    if (!symbol) return;
    currentSymbol = symbol;
    const sym = symbol.toUpperCase();
    let precision = 2;
    let minMove = 0.01;

    if (sym.includes('JPY')) {{
      precision = 3;
      minMove = 0.001;
    }} else if (sym.includes('EUR') || sym.includes('GBP') || sym.includes('AUD') || sym.includes('NZD') || (sym.includes('USD') && !sym.includes('XAU') && !sym.includes('BTC'))) {{
      precision = 5;
      minMove = 0.00001;
    }} else if (sym.includes('XAU') || sym.includes('GOLD')) {{
      precision = 2;
      minMove = 0.01;
    }} else if (sym.includes('BTC')) {{
      precision = 2;
      minMove = 0.1;
    }}

    if (candleSeries) {{
      candleSeries.applyOptions({{
        priceFormat: {{
          type: 'price',
          precision: precision,
          minMove: minMove,
        }}
      }});
    }}

    const wm = document.getElementById('watermark');
    if (wm) {{
      wm.innerText = symbol + ' • TRADING REPLAY LAB';
    }}
    scheduleRender();
  }}

  function setChartData(candleData, volumeData, savedRange) {{
    currentCandles = candleData ? candleData.slice() : [];
    candleSeries.setData(candleData || []);
    if (volumeData && volumeData.length > 0) {{
      volumeSeries.setData(volumeData);
    }}

    const n = currentCandles.length;
    if (n > 0) {{
      if (savedRange && savedRange.from !== undefined && savedRange.to !== undefined) {{
        try {{
          chart.timeScale().setVisibleLogicalRange(savedRange);
        }} catch (e) {{
          const span = 110;
          chart.timeScale().setVisibleLogicalRange({{ from: Math.max(0, n - span), to: n + 10 }});
        }}
      }} else if (lastSavedLogicalRange && lastSavedLogicalRange.from !== undefined && lastSavedLogicalRange.to !== undefined) {{
        const span = Math.max(25, Math.min(600, Math.round(lastSavedLogicalRange.to - lastSavedLogicalRange.from)));
        chart.timeScale().setVisibleLogicalRange({{ from: Math.max(0, n - span), to: n + Math.round(span * 0.08) }});
      }} else {{
        const span = 110;
        chart.timeScale().setVisibleLogicalRange({{ from: Math.max(0, n - span), to: n + 10 }});
      }}
    }}
    scheduleRender();
  }}


  function updateCandle(candle, volume) {{
    if (!candle) return;
    try {{
      if (currentCandles.length > 0) {{
        const lastCandle = currentCandles[currentCandles.length - 1];
        if (candle.time < lastCandle.time) {{
          // Re-filter/trim candles to strictly before current time and append
          currentCandles = currentCandles.filter(c => c.time < candle.time);
          currentCandles.push(candle);
          candleSeries.setData(currentCandles);
          if (volume) {{
            volumeSeries.setData(currentCandles.map(c => ({{
              time: c.time,
              value: (c.time === candle.time && volume.value !== undefined) ? volume.value : 0,
              color: c.close >= c.open ? 'rgba(38, 166, 154, 0.4)' : 'rgba(239, 83, 80, 0.4)'
            }})));
          }}
          scheduleRender();
          return;
        }} else if (candle.time === lastCandle.time) {{
          currentCandles[currentCandles.length - 1] = candle;
        }} else {{
          currentCandles.push(candle);
        }}
      }} else {{
        currentCandles.push(candle);
      }}

      candleSeries.update(candle);
      if (volume) {{
        try {{
          volumeSeries.update(volume);
        }} catch (vErr) {{}}
      }}
    }} catch (err) {{
      try {{
        candleSeries.setData(currentCandles);
      }} catch (e2) {{}}
    }}
    scheduleRender();
  }}


  function setMarkers(markers) {{
    candleSeries.setMarkers(markers || []);
  }}

  function setDrawings(drawingsList) {{
    drawings = drawingsList || [];
    scheduleRender();
  }}

  function setTradeOverlays(overlays) {{
    tradeOverlays = overlays || {{ lines: [], markers: [] }};
    scheduleRender();
  }}

  function setVolumeVisible(visible) {{
    volumeSeries.applyOptions({{ visible: Boolean(visible) }});
    scheduleRender();
  }}

  function setTheme(themeName, bgColor, textColor, gridColor, cardBg, borderColor) {{
    if (chart) {{
      chart.applyOptions({{
        layout: {{
          background: {{ type: 'solid', color: bgColor }},
          textColor: textColor,
        }},
        grid: {{
          vertLines: {{ color: gridColor }},
          horzLines: {{ color: gridColor }},
        }},
        rightPriceScale: {{ borderColor: gridColor }},
        timeScale: {{ borderColor: gridColor }},
      }});
      document.body.style.backgroundColor = bgColor;
      document.documentElement.style.backgroundColor = bgColor;
      const wm = document.getElementById('watermark');
      if (wm) {{
        const isLight = (textColor === '#191919' || textColor === '#131722' || textColor === '#1e222d');
        wm.style.color = isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.04)';
      }}
      const propTb = document.getElementById('drawing-prop-toolbar');
      if (propTb && cardBg) {{
        propTb.style.background = cardBg;
        propTb.style.borderColor = borderColor || gridColor;
        propTb.style.color = textColor;
      }}
      scheduleRender();
    }}
  }}

  let indicatorSeriesMap = {{}};

  function setIndicatorData(indId, seriesList) {{
    if (!indicatorSeriesMap[indId]) {{
      indicatorSeriesMap[indId] = [];
    }}
    while (indicatorSeriesMap[indId].length > seriesList.length) {{
      const oldS = indicatorSeriesMap[indId].pop();
      chart.removeSeries(oldS);
    }}
    seriesList.forEach((sConf, idx) => {{
      let sObj = indicatorSeriesMap[indId][idx];
      const opts = {{
        color: sConf.color || '#2196f3',
        lineWidth: sConf.lineWidth || 2,
        lineStyle: sConf.lineStyle === 'dashed' ? 2 : (sConf.lineStyle === 'dotted' ? 1 : 0),
        visible: sConf.visible !== undefined ? Boolean(sConf.visible) : true,
        priceScaleId: sConf.priceScaleId || 'right',
      }};
      if (!sObj) {{
        if (sConf.type === 'histogram') {{
          sObj = chart.addHistogramSeries(opts);
        }} else {{
          sObj = chart.addLineSeries(opts);
        }}
        indicatorSeriesMap[indId].push(sObj);
      }} else {{
        sObj.applyOptions(opts);
      }}
      sObj.setData(sConf.data || []);
    }});
    scheduleRender();
  }}

  function removeIndicator(indId) {{
    if (indicatorSeriesMap[indId]) {{
      indicatorSeriesMap[indId].forEach(sObj => chart.removeSeries(sObj));
      delete indicatorSeriesMap[indId];
      scheduleRender();
    }}
  }}

  function setIndicatorVisible(indId, visible) {{
    if (indicatorSeriesMap[indId]) {{
      indicatorSeriesMap[indId].forEach(sObj => sObj.applyOptions({{ visible: Boolean(visible) }}));
      scheduleRender();
    }}
  }}

  function setActiveTool(toolName) {{
    activeTool = toolName;
    tempDrawingPoints = [];
    liveMousePoint = null;
    isCreatingDrawing = false;
    startCreationPoint = null;

    if (activeTool && activeTool !== 'CURSOR') {{
      toolBanner.innerText = 'TOOL: ' + activeTool;
      toolBanner.style.display = 'block';
      canvas.style.pointerEvents = 'auto';
      canvas.style.cursor = 'crosshair';
      chart.applyOptions({{ handleScroll: false, handleScale: false }});
    }} else {{
      toolBanner.style.display = 'none';
      canvas.style.pointerEvents = 'none';
      canvas.style.cursor = 'default';
      chart.applyOptions({{ handleScroll: true, handleScale: true }});
    }}
    scheduleRender();
  }}

  // Safe Coordinate Mapping Helpers (Rock-solid multi-timeframe anchoring)
  function safeTimeToCoordinate(time) {{
    if (time === null || time === undefined || isNaN(time)) return null;
    const coord = chart.timeScale().timeToCoordinate(time);
    if (coord !== null && !isNaN(coord)) return coord;

    // Fractional bar index interpolation against loaded candle series
    if (currentCandles && currentCandles.length > 0) {{
      const n = currentCandles.length;
      if (n === 1) {{
        return chart.timeScale().logicalToCoordinate(0);
      }}

      // If before first candle in loaded dataset
      if (time <= currentCandles[0].time) {{
        const dt = currentCandles[1].time - currentCandles[0].time;
        const logical = (dt > 0) ? (time - currentCandles[0].time) / dt : 0;
        const c = chart.timeScale().logicalToCoordinate(logical);
        if (c !== null && !isNaN(c)) return c;
      }}

      // If after last candle in loaded dataset
      if (time >= currentCandles[n - 1].time) {{
        const dt = currentCandles[n - 1].time - currentCandles[n - 2].time;
        const logical = (dt > 0) ? (n - 1) + (time - currentCandles[n - 1].time) / dt : (n - 1);
        const c = chart.timeScale().logicalToCoordinate(logical);
        if (c !== null && !isNaN(c)) return c;
      }}

      // Binary search between two bounding candles
      let low = 0, high = n - 1;
      while (low <= high) {{
        const mid = (low + high) >> 1;
        if (currentCandles[mid].time <= time) {{
          low = mid + 1;
        }} else {{
          high = mid - 1;
        }}
      }}
      const idx = Math.max(0, Math.min(n - 2, high));
      const t1 = currentCandles[idx].time;
      const t2 = currentCandles[idx + 1].time;
      const frac = (t2 > t1) ? (time - t1) / (t2 - t1) : 0;
      const logical = idx + frac;
      const c = chart.timeScale().logicalToCoordinate(logical);
      if (c !== null && !isNaN(c)) return c;
    }}

    return null;
  }}

  function safePriceToCoordinate(price) {{
    if (price === null || price === undefined || isNaN(price)) return null;
    const coord = candleSeries.priceToCoordinate(price);
    if (coord !== null && !isNaN(coord)) return coord;
    return null;
  }}

  function safeCoordinateToTime(x) {{
    const t = chart.timeScale().coordinateToTime(x);
    if (t !== null && !isNaN(t)) return t;

    if (currentCandles && currentCandles.length > 0) {{
      const n = currentCandles.length;
      const logical = chart.timeScale().coordinateToLogical(x);
      if (logical !== null && !isNaN(logical)) {{
        if (n === 1) return currentCandles[0].time;
        if (logical <= 0) {{
          const dt = currentCandles[1].time - currentCandles[0].time;
          return Math.round(currentCandles[0].time + logical * dt);
        }}
        if (logical >= n - 1) {{
          const dt = currentCandles[n - 1].time - currentCandles[n - 2].time;
          return Math.round(currentCandles[n - 1].time + (logical - (n - 1)) * dt);
        }}
        const i = Math.floor(logical);
        const frac = logical - i;
        const dt = currentCandles[i + 1].time - currentCandles[i].time;
        return Math.round(currentCandles[i].time + frac * dt);
      }}
    }}
    return Math.floor(Date.now() / 1000);
  }}

  function safeCoordinateToPrice(y) {{
    const p = candleSeries.coordinateToPrice(y);
    if (p !== null && !isNaN(p)) return p;
    return null;
  }}

  function colorToHex(colorStr) {{
    if (!colorStr) return '#2962ff';
    if (colorStr.startsWith('#')) return colorStr.slice(0, 7);
    const match = colorStr.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
    if (match) {{
      const r = parseInt(match[1]).toString(16).padStart(2, '0');
      const g = parseInt(match[2]).toString(16).padStart(2, '0');
      const b = parseInt(match[3]).toString(16).padStart(2, '0');
      return '#' + r + g + b;
    }}
    return '#2962ff';
  }}

  function hexAndAlphaToRgba(hexStr, alpha) {{
    if (!hexStr || !hexStr.startsWith('#')) hexStr = '#2962ff';
    const r = parseInt(hexStr.slice(1, 3), 16) || 41;
    const g = parseInt(hexStr.slice(3, 5), 16) || 98;
    const b = parseInt(hexStr.slice(5, 7), 16) || 255;
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }}

  function getSnappedPoint(anchorTime, anchorPrice, curX, curY) {{
    const x1 = safeTimeToCoordinate(anchorTime);
    const y1 = safePriceToCoordinate(anchorPrice);
    if (x1 === null || y1 === null) {{
      return {{
        x: curX,
        y: curY,
        price: safeCoordinateToPrice(curY),
        time: safeCoordinateToTime(curX)
      }};
    }}

    const dx = curX - x1;
    const dy = curY - y1;
    if (Math.hypot(dx, dy) === 0) {{
      return {{
        x: curX,
        y: curY,
        price: anchorPrice,
        time: anchorTime
      }};
    }}

    const angle = Math.atan2(dy, dx);
    const snapStep = Math.PI / 4; // 45 degree intervals (0°, 45°, 90°, 135°, 180°, etc.)
    const snappedAngle = Math.round(angle / snapStep) * snapStep;
    const dist = Math.hypot(dx, dy);

    let sX = x1 + dist * Math.cos(snappedAngle);
    let sY = y1 + dist * Math.sin(snappedAngle);
    let sPrice, sTime;

    // Exact horizontal snap (0, PI, -PI) -> locks price identically to start anchor price
    if (Math.abs(Math.sin(snappedAngle)) < 1e-4) {{
      sY = y1;
      sPrice = anchorPrice;
    }} else {{
      sPrice = safeCoordinateToPrice(sY);
    }}

    // Exact vertical snap (PI/2, -PI/2) -> locks time identically to start anchor time
    if (Math.abs(Math.cos(snappedAngle)) < 1e-4) {{
      sX = x1;
      sTime = anchorTime;
    }} else {{
      sTime = safeCoordinateToTime(sX);
    }}

    return {{ x: sX, y: sY, price: sPrice, time: sTime }};
  }}

  // Render Canvas Drawings & Overlays
  function renderDrawings() {{
    ctx.clearRect(0, 0, container.clientWidth, container.clientHeight);

    // Session Background Highlighting & Killzones
    if (currentCandles && currentCandles.length > 0) {{
      const nCandles = currentCandles.length;
      let curSession = null;
      let sStart = null;
      let sEnd = null;
      let curCol = null;
      let curLabel = null;

      const scanStart = Math.max(0, nCandles - 600);
      for (let i = scanStart; i < nCandles; i++) {{
        const c = currentCandles[i];
        const d = new Date(c.time * 1000);
        const h = d.getUTCHours();
        let sess = null;
        let col = null;
        let label = null;

        if (h >= 0 && h < 8) {{
          sess = 'ASIA';
          col = 'rgba(156, 39, 176, 0.04)';
          label = 'Asia';
        }} else if (h >= 7 && h < 10) {{
          sess = 'LONDON';
          col = 'rgba(33, 150, 243, 0.06)';
          label = 'London';
        }} else if (h >= 12 && h < 15) {{
          sess = 'NY';
          col = 'rgba(255, 152, 0, 0.06)';
          label = 'NY Open';
        }} else if (h >= 15 && h < 17) {{
          sess = 'LDN_CLOSE';
          col = 'rgba(0, 150, 136, 0.05)';
          label = 'Ldn Close';
        }}

        if (sess !== curSession) {{
          if (curSession && sStart !== null && sEnd !== null) {{
            const x1 = safeTimeToCoordinate(sStart);
            const x2 = safeTimeToCoordinate(sEnd);
            if (x1 !== null && x2 !== null && x2 >= x1 - 5) {{
              const w = Math.max(x2 - x1, 12);
              ctx.save();
              ctx.fillStyle = curCol;
              ctx.fillRect(x1, 0, w, container.clientHeight);
              ctx.fillStyle = 'rgba(255, 255, 255, 0.18)';
              ctx.font = 'bold 9px sans-serif';
              ctx.fillText(curLabel, x1 + 4, 14);
              ctx.restore();
            }}
          }}
          curSession = sess;
          curCol = col;
          curLabel = label;
          sStart = c.time;
          sEnd = c.time;
        }} else {{
          sEnd = c.time;
        }}
      }}
      if (curSession && sStart !== null && sEnd !== null) {{
        const x1 = safeTimeToCoordinate(sStart);
        const x2 = safeTimeToCoordinate(sEnd);
        if (x1 !== null && x2 !== null && x2 >= x1 - 5) {{
          const w = Math.max(x2 - x1, 12);
          ctx.save();
          ctx.fillStyle = curCol;
          ctx.fillRect(x1, 0, w, container.clientHeight);
          ctx.fillStyle = 'rgba(255, 255, 255, 0.18)';
          ctx.font = 'bold 9px sans-serif';
          ctx.fillText(curLabel, x1 + 4, 14);
          ctx.restore();
        }}
      }}

      // Key Reference Levels (Daily Open, PDH, PDL)
      if (nCandles > 10) {{
        const lastCandle = currentCandles[nCandles - 1];
        const lastDate = new Date(lastCandle.time * 1000);
        const lastDay = lastDate.getUTCDate();
        const lastMonth = lastDate.getUTCMonth();
        const lastYear = lastDate.getUTCFullYear();

        let todayOpen = null;
        let prevDayHigh = -Infinity;
        let prevDayLow = Infinity;
        let prevDayCandles = 0;
        let prevDayNum = null;

        for (let i = nCandles - 1; i >= 0; i--) {{
          const c = currentCandles[i];
          const cd = new Date(c.time * 1000);
          const cDay = cd.getUTCDate();
          const isToday = (cDay === lastDay && cd.getUTCMonth() === lastMonth && cd.getUTCFullYear() === lastYear);

          if (isToday) {{
            todayOpen = c.open;
          }} else {{
            if (prevDayNum === null) {{
              prevDayNum = cDay;
            }}
            if (cDay === prevDayNum) {{
              prevDayHigh = Math.max(prevDayHigh, c.high);
              prevDayLow = Math.min(prevDayLow, c.low);
              prevDayCandles++;
            }} else if (prevDayCandles > 0) {{
              break;
            }}
          }}
        }}

        const levelsToDraw = [];
        if (todayOpen !== null) {{
          levelsToDraw.push({{ price: todayOpen, label: 'DO', color: '#00bcd4' }});
        }}
        if (prevDayCandles > 0 && prevDayHigh > -Infinity) {{
          levelsToDraw.push({{ price: prevDayHigh, label: 'PDH', color: '#ff9800' }});
          levelsToDraw.push({{ price: prevDayLow, label: 'PDL', color: '#ff9800' }});
        }}

        levelsToDraw.forEach(lvl => {{
          const y = safePriceToCoordinate(lvl.price);
          if (y !== null && y >= 0 && y <= container.clientHeight) {{
            ctx.save();
            ctx.beginPath();
            ctx.strokeStyle = lvl.color;
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 4]);
            ctx.moveTo(0, y);
            ctx.lineTo(container.clientWidth - 80, y);
            ctx.stroke();

            // Right tag
            ctx.fillStyle = lvl.color;
            ctx.font = 'bold 9px sans-serif';
            ctx.fillText(lvl.label + ' ' + lvl.price.toFixed(2), container.clientWidth - 75, y + 3);
            ctx.restore();
          }}
        }});
      }}
    }}

    // 0. Persistent Crosshair Guidelines when Drawing Tool is Active
    if (activeTool !== 'CURSOR' && liveMousePoint) {{
      ctx.save();
      ctx.strokeStyle = 'rgba(150, 154, 168, 0.50)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);

      const chX = (liveMousePoint.rawX !== undefined) ? liveMousePoint.rawX : liveMousePoint.x;
      const chY = (liveMousePoint.rawY !== undefined) ? liveMousePoint.rawY : liveMousePoint.y;

      // Vertical crosshair guideline (full chart height)
      ctx.beginPath();
      ctx.moveTo(chX, 0);
      ctx.lineTo(chX, container.clientHeight);
      ctx.stroke();

      // Horizontal crosshair guideline (full chart width)
      ctx.beginPath();
      ctx.moveTo(0, chY);
      ctx.lineTo(container.clientWidth, chY);
      ctx.stroke();

      // Price Tag Badge on right price axis
      const curP = safeCoordinateToPrice(chY);
      if (curP !== null && !isNaN(curP)) {{
        const priceStr = Number(curP).toFixed(2);
        const tagW = 64;
        const tagH = 18;
        const tagX = container.clientWidth - tagW - 2;
        const tagY = chY - tagH / 2;

        ctx.fillStyle = '#2a2e39';
        ctx.fillRect(tagX, tagY, tagW, tagH);
        ctx.strokeStyle = '#434651';
        ctx.setLineDash([]);
        ctx.strokeRect(tagX, tagY, tagW, tagH);

        ctx.fillStyle = '#d1d4dc';
        ctx.font = 'bold 10px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(priceStr, tagX + tagW / 2, chY);
      }}

      ctx.restore();
    }}

    // 1. Active SL / TP Trade Lines
    if (tradeOverlays.lines) {{
      tradeOverlays.lines.forEach(line => {{
        const y = safePriceToCoordinate(line.price);
        if (y !== null && y >= -50 && y <= container.clientHeight + 50) {{
          ctx.save();
          ctx.beginPath();
          ctx.strokeStyle = line.color || '#2962ff';
          ctx.lineWidth = line.width || 1.5;
          if (line.style === 'dashed') ctx.setLineDash([4, 4]);
          ctx.moveTo(0, y);
          ctx.lineTo(container.clientWidth, y);
          ctx.stroke();

          // Badge
          ctx.fillStyle = line.color || '#2962ff';
          ctx.fillRect(container.clientWidth - 110, y - 10, 105, 20);
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 10px sans-serif';
          ctx.fillText((line.label || '') + ' ' + Number(line.price).toFixed(2), container.clientWidth - 105, y + 4);

          // Drag Handle
          ctx.beginPath();
          ctx.arc(container.clientWidth - 115, y, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.fill();
          ctx.stroke();
          ctx.restore();
        }}
      }});
    }}

    // 2. Existing User Drawings
    drawings.forEach(d => {{
      if (!d.visible) return;
      ctx.save();
      const style = d.style || {{}};
      const isSelected = (d.id === selectedDrawingId);
      const isHoveredOrSelected = (d.id === hoveredDrawingId || isSelected);

      ctx.strokeStyle = isSelected ? '#ffeb3b' : (style.color || '#2962ff');
      ctx.fillStyle = style.fill_color || 'rgba(41, 98, 255, 0.25)';
      ctx.lineWidth = (style.line_width !== undefined ? Number(style.line_width) : 1.0) + (isSelected ? 0.5 : 0);
      
      if (style.line_style === 'dashed') ctx.setLineDash([6, 6]);
      else if (style.line_style === 'dotted') ctx.setLineDash([2, 3]);
      else ctx.setLineDash([]);

      if (d.type === 'TRENDLINE' || d.type === 'RAY' || d.type === 'ARROW') {{
        if (d.points && d.points.length >= 2) {{
          const x1 = safeTimeToCoordinate(d.points[0].time);
          const y1 = safePriceToCoordinate(d.points[0].price);
          const x2 = safeTimeToCoordinate(d.points[1].time);
          const y2 = safePriceToCoordinate(d.points[1].price);

          if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            if (d.type === 'RAY') {{
              const dx = x2 - x1;
              const dy = y2 - y1;
              ctx.lineTo(x1 + dx * 25, y1 + dy * 25);
            }} else {{
              ctx.lineTo(x2, y2);
            }}
            ctx.stroke();

            if (d.type === 'ARROW') {{
              const angle = Math.atan2(y2 - y1, x2 - x1);
              ctx.beginPath();
              ctx.moveTo(x2, y2);
              ctx.lineTo(x2 - 12 * Math.cos(angle - Math.PI / 6), y2 - 12 * Math.sin(angle - Math.PI / 6));
              ctx.lineTo(x2 - 12 * Math.cos(angle + Math.PI / 6), y2 - 12 * Math.sin(angle + Math.PI / 6));
              ctx.closePath();
              ctx.fillStyle = ctx.strokeStyle;
              ctx.fill();
            }}

            if (d.text) {{
              ctx.fillStyle = style.text_color || '#ffffff';
              ctx.font = 'bold 11px sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'bottom';
              ctx.fillText(d.text, (x1 + x2) / 2, (y1 + y2) / 2 - 6);
            }}

            if (isSelected) {{
              renderHandle(x1, y1);
              renderHandle(x2, y2);
            }}
          }}
        }}
      }}
      else if (d.type === 'HORIZONTAL_LINE') {{
        if (d.points && d.points.length >= 1) {{
          const y = safePriceToCoordinate(d.points[0].price);
          if (y !== null) {{
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(container.clientWidth, y);
            ctx.stroke();
            ctx.fillStyle = ctx.strokeStyle;
            ctx.font = 'bold 11px sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            const txt = (d.text ? d.text + ' : ' : '') + Number(d.points[0].price).toFixed(2);
            ctx.fillText(txt, 15, y - 5);
            if (isSelected) renderHandle(container.clientWidth / 2, y);
          }}
        }}
      }}
      else if (d.type === 'VERTICAL_LINE') {{
        if (d.points && d.points.length >= 1) {{
          const x = safeTimeToCoordinate(d.points[0].time);
          if (x !== null) {{
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, container.clientHeight);
            ctx.stroke();
            if (d.text) {{
              ctx.fillStyle = style.text_color || '#ffffff';
              ctx.font = 'bold 11px sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillText(d.text, x, 25);
            }}
            if (isSelected) renderHandle(x, container.clientHeight / 2);
          }}
        }}
      }}
      else if (d.type === 'RECTANGLE') {{
        if (d.points && d.points.length >= 2) {{
          const x1 = safeTimeToCoordinate(d.points[0].time);
          const y1 = safePriceToCoordinate(d.points[0].price);
          const x2 = safeTimeToCoordinate(d.points[1].time);
          const y2 = safePriceToCoordinate(d.points[1].price);

          if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            const minY = Math.min(y1, y2);
            const maxY = Math.max(y1, y2);
            const midX = (minX + maxX) / 2;
            const midY = (minY + maxY) / 2;
            const rw = maxX - minX;
            const rh = maxY - minY;

            ctx.fillRect(minX, minY, rw, rh);
            ctx.strokeRect(minX, minY, rw, rh);

            // Centered Rectangle Text
            if (d.text) {{
              ctx.fillStyle = style.text_color || '#ffffff';
              ctx.font = 'bold ' + (style.font_size || 12) + 'px sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText(d.text, midX, midY);
            }}

            if (isSelected) {{
              // 8 Handles
              renderHandle(minX, minY); // NW
              renderHandle(midX, minY); // N
              renderHandle(maxX, minY); // NE
              renderHandle(maxX, midY); // E
              renderHandle(maxX, maxY); // SE
              renderHandle(midX, maxY); // S
              renderHandle(minX, maxY); // SW
              renderHandle(minX, midY); // W
            }}
          }}
        }}
      }}
      else if (d.type === 'FIBONACCI') {{
        if (d.points && d.points.length >= 2) {{
          const x1 = safeTimeToCoordinate(d.points[0].time);
          const y1 = safePriceToCoordinate(d.points[0].price);
          const x2 = safeTimeToCoordinate(d.points[1].time);
          const y2 = safePriceToCoordinate(d.points[1].price);

          if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
            const p1 = d.points[0].price;
            const p2 = d.points[1].price;
            const diff = p2 - p1;
            const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2) + 240;

            levels.forEach(lvl => {{
              const lvlPrice = p1 + diff * lvl;
              const ly = safePriceToCoordinate(lvlPrice);
              if (ly !== null) {{
                ctx.beginPath();
                ctx.moveTo(minX, ly);
                ctx.lineTo(maxX, ly);
                ctx.stroke();
                ctx.fillStyle = '#ffffff';
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'bottom';
                ctx.fillText(lvl + ' (' + lvlPrice.toFixed(2) + ')', minX + 5, ly - 3);
              }}
            }});
            if (isSelected) {{
              renderHandle(x1, y1);
              renderHandle(x2, y2);
            }}
          }}
        }}
      }}
      else if (d.type === 'PATH') {{
        if (d.points && d.points.length >= 2) {{
          ctx.beginPath();
          let isFirst = true;
          d.points.forEach(p => {{
            const px = safeTimeToCoordinate(p.time);
            const py = safePriceToCoordinate(p.price);
            if (px !== null && py !== null) {{
              if (isFirst) {{
                ctx.moveTo(px, py);
                isFirst = false;
              }} else {{
                ctx.lineTo(px, py);
              }}
            }}
          }});
          ctx.stroke();

          if (d.text && d.points.length > 0) {{
            const lastPt = d.points[d.points.length - 1];
            const lx = safeTimeToCoordinate(lastPt.time);
            const ly = safePriceToCoordinate(lastPt.price);
            if (lx !== null && ly !== null) {{
              ctx.fillStyle = style.text_color || '#ffffff';
              ctx.font = 'bold 11px sans-serif';
              ctx.textAlign = 'left';
              ctx.textBaseline = 'middle';
              ctx.fillText(' ' + d.text, lx + 6, ly);
            }}
          }}

          if (isSelected) {{
            d.points.forEach(p => {{
              const px = safeTimeToCoordinate(p.time);
              const py = safePriceToCoordinate(p.price);
              if (px !== null && py !== null) renderHandle(px, py);
            }});
          }}
        }}
      }}
      else if (d.type === 'VOLUME_PROFILE') {{
        if (d.points && d.points.length >= 2) {{
          const t1 = d.points[0].time;
          const t2 = d.points[1].time;
          const tStart = Math.min(t1, t2);
          const tEnd = Math.max(t1, t2);

          let x1 = safeTimeToCoordinate(tStart);
          let x2 = safeTimeToCoordinate(tEnd);
          if (x1 === null && x2 !== null) x1 = x2 - 140;
          if (x2 === null && x1 !== null) x2 = x1 + 140;
          if (x1 === null && x2 === null) {{
            x1 = 100;
            x2 = 250;
          }}

          const minX = Math.min(x1, x2);
          const maxX = Math.max(x1, x2);
          const spanWidth = Math.max(30, maxX - minX);

          const rangeCandles = (currentCandles || []).filter(c => c.time >= tStart && c.time <= tEnd);
          if (rangeCandles.length > 0) {{
            let minP = Infinity, maxP = -Infinity;
            rangeCandles.forEach(c => {{
              if (c.low < minP) minP = c.low;
              if (c.high > maxP) maxP = c.high;
            }});

            if (maxP <= minP) maxP = minP + 1.0;
            const numBins = (d.metadata && d.metadata.num_bins) ? d.metadata.num_bins : 30;
            const binSize = (maxP - minP) / numBins;
            const binUp = new Array(numBins).fill(0);
            const binDown = new Array(numBins).fill(0);

            rangeCandles.forEach(c => {{
              const cVol = (c.volume !== undefined && c.volume > 0) ? c.volume : 100;
              const isUp = c.close >= c.open;
              const lIdx = Math.max(0, Math.min(numBins - 1, Math.floor((c.low - minP) / binSize)));
              const hIdx = Math.max(0, Math.min(numBins - 1, Math.floor((c.high - minP) / binSize)));
              const span = Math.max(1, hIdx - lIdx + 1);
              const vPerBin = cVol / span;
              for (let b = lIdx; b <= hIdx; b++) {{
                if (isUp) binUp[b] += vPerBin;
                else binDown[b] += vPerBin;
              }}
            }});

            const binTotals = binUp.map((u, i) => u + binDown[i]);
            let maxBinVol = 0, pocIdx = 0, totalVol = 0;
            binTotals.forEach((tv, i) => {{
              totalVol += tv;
              if (tv > maxBinVol) {{
                maxBinVol = tv;
                pocIdx = i;
              }}
            }});

            const targetVaVol = totalVol * 0.70;
            let currVaVol = binTotals[pocIdx] || 0;
            const vaSet = new Set([pocIdx]);
            let upI = pocIdx + 1, downI = pocIdx - 1;
            while (currVaVol < targetVaVol && (upI < numBins || downI >= 0)) {{
              const uV = (upI < numBins) ? binTotals[upI] : 0;
              const dV = (downI >= 0) ? binTotals[downI] : 0;
              if (uV >= dV && upI < numBins) {{
                currVaVol += uV;
                vaSet.add(upI);
                upI++;
              }} else if (downI >= 0) {{
                currVaVol += dV;
                vaSet.add(downI);
                downI--;
              }} else if (upI < numBins) {{
                currVaVol += uV;
                vaSet.add(upI);
                upI++;
              }} else break;
            }}

            const vaIndices = Array.from(vaSet);
            const valIdx = Math.min(...vaIndices);
            const vahIdx = Math.max(...vaIndices);
            const valPrice = minP + valIdx * binSize;
            const vahPrice = minP + (vahIdx + 1) * binSize;
            const pocPrice = minP + (pocIdx + 0.5) * binSize;

            const topY = safePriceToCoordinate(maxP);
            const botY = safePriceToCoordinate(minP);
            if (topY !== null && botY !== null) {{
              ctx.fillStyle = isSelected ? 'rgba(41, 98, 255, 0.08)' : 'rgba(255, 255, 255, 0.02)';
              ctx.fillRect(minX, Math.min(topY, botY), spanWidth, Math.abs(botY - topY));
              ctx.strokeStyle = isSelected ? '#ffeb3b' : 'rgba(100, 100, 100, 0.3)';
              ctx.lineWidth = 1;
              ctx.strokeRect(minX, Math.min(topY, botY), spanWidth, Math.abs(botY - topY));
            }}

            for (let i = 0; i < numBins; i++) {{
              const bLowPrice = minP + i * binSize;
              const bHighPrice = bLowPrice + binSize;
              const yLow = safePriceToCoordinate(bLowPrice);
              const yHigh = safePriceToCoordinate(bHighPrice);
              if (yLow === null || yHigh === null) continue;

              const barY = Math.min(yLow, yHigh);
              const barH = Math.max(1, Math.abs(yLow - yHigh) - 0.5);
              const inVa = vaSet.has(i);

              const upRatio = maxBinVol > 0 ? (binUp[i] / maxBinVol) : 0;
              const downRatio = maxBinVol > 0 ? (binDown[i] / maxBinVol) : 0;

              const maxBarWidth = spanWidth * 0.85;
              const upWidth = upRatio * maxBarWidth;
              const downWidth = downRatio * maxBarWidth;

              // Buy Volume (Teal)
              ctx.fillStyle = inVa ? 'rgba(38, 166, 154, 0.70)' : 'rgba(38, 166, 154, 0.30)';
              ctx.fillRect(minX, barY, upWidth, barH);

              // Sell Volume (Red)
              ctx.fillStyle = inVa ? 'rgba(239, 83, 80, 0.70)' : 'rgba(239, 83, 80, 0.30)';
              ctx.fillRect(minX + upWidth, barY, downWidth, barH);
            }}

            // POC Line
            const pocY = safePriceToCoordinate(pocPrice);
            if (pocY !== null) {{
              ctx.beginPath();
              ctx.strokeStyle = '#f23645';
              ctx.lineWidth = 2;
              ctx.setLineDash([]);
              ctx.moveTo(minX, pocY);
              ctx.lineTo(maxX, pocY);
              ctx.stroke();

              ctx.fillStyle = '#f23645';
              ctx.font = 'bold 10px sans-serif';
              ctx.textAlign = 'right';
              ctx.fillText('POC: ' + pocPrice.toFixed(2), maxX - 4, pocY - 3);
            }}

            // VAH Line
            const vahY = safePriceToCoordinate(vahPrice);
            if (vahY !== null) {{
              ctx.beginPath();
              ctx.strokeStyle = '#2962ff';
              ctx.lineWidth = 1.5;
              ctx.setLineDash([4, 4]);
              ctx.moveTo(minX, vahY);
              ctx.lineTo(maxX, vahY);
              ctx.stroke();

              ctx.fillStyle = '#2962ff';
              ctx.font = 'bold 9px sans-serif';
              ctx.textAlign = 'right';
              ctx.fillText('VAH: ' + vahPrice.toFixed(2), maxX - 4, vahY - 3);
            }}

            // VAL Line
            const valY = safePriceToCoordinate(valPrice);
            if (valY !== null) {{
              ctx.beginPath();
              ctx.strokeStyle = '#2962ff';
              ctx.lineWidth = 1.5;
              ctx.setLineDash([4, 4]);
              ctx.moveTo(minX, valY);
              ctx.lineTo(maxX, valY);
              ctx.stroke();

              ctx.fillStyle = '#2962ff';
              ctx.font = 'bold 9px sans-serif';
              ctx.textAlign = 'right';
              ctx.fillText('VAL: ' + valPrice.toFixed(2), maxX - 4, valY + 10);
            }}

            if (isSelected) {{
              const midY = (topY !== null && botY !== null) ? (topY + botY) / 2 : 100;
              renderHandle(minX, midY);
              renderHandle(maxX, midY);
              if (topY !== null) renderHandle((minX + maxX) / 2, topY);
              if (botY !== null) renderHandle((minX + maxX) / 2, botY);
            }}
          }}
        }}
      }}
      else if (d.type === 'TEXT') {{
        if (d.points && d.points.length >= 1) {{
          const x = safeTimeToCoordinate(d.points[0].time);
          const y = safePriceToCoordinate(d.points[0].price);
          if (x !== null && y !== null) {{
            ctx.fillStyle = style.text_color || '#ffffff';
            ctx.font = 'bold ' + (style.font_size || 14) + 'px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(d.text || 'Text', x, y);
            if (isSelected) renderHandle(x, y);
          }}
        }}
      }}
      else if (d.type === 'LONG_POSITION' || d.type === 'SHORT_POSITION') {{
        if (d.points && d.points.length >= 3) {{
          const isLong = (d.type === 'LONG_POSITION');
          const tStart = d.points[0].time;
          const tEnd = (d.points.length >= 4 && d.points[3].time) ? d.points[3].time : (tStart + 14400);

          let x1 = safeTimeToCoordinate(tStart);
          let x2 = safeTimeToCoordinate(tEnd);

          if (x1 === null && x2 !== null) x1 = x2 - 160;
          if (x2 === null && x1 !== null) x2 = x1 + 160;
          if (x1 === null && x2 === null) {{
            x1 = 100;
            x2 = 260;
          }}

          const minX = Math.min(x1, x2);
          const maxX = Math.max(x1, x2);
          const midX = (minX + maxX) / 2;
          const boxWidth = Math.max(20, maxX - minX);

          const entryPrice = d.points[0].price;
          const slPrice = d.points[1].price;
          const tpPrice = d.points[2].price;

          let yEntry = safePriceToCoordinate(entryPrice);
          let ySL = safePriceToCoordinate(slPrice);
          let yTP = safePriceToCoordinate(tpPrice);

          // Clamped bounds so boxes never vanish
          if (yEntry === null) yEntry = container.clientHeight / 2;
          if (ySL === null) ySL = isLong ? container.clientHeight + 100 : -100;
          if (yTP === null) yTP = isLong ? -100 : container.clientHeight + 100;

          // Compute trade progression & candle fill simulation
          let tpHit = false, slHit = false, hitTime = null;
          let activeFillTime = tStart;
          let latestCandleClose = entryPrice;

          if (currentCandles && currentCandles.length > 0) {{
            for (let cIdx = 0; cIdx < currentCandles.length; cIdx++) {{
              const c = currentCandles[cIdx];
              if (c.time < tStart) continue;
              if (c.time > tEnd) break;

              activeFillTime = c.time;
              latestCandleClose = c.close;

              if (isLong) {{
                if (c.high >= tpPrice) {{
                  tpHit = true;
                  hitTime = c.time;
                  break;
                }}
                if (c.low <= slPrice) {{
                  slHit = true;
                  hitTime = c.time;
                  break;
                }}
              }} else {{
                if (c.low <= tpPrice) {{
                  tpHit = true;
                  hitTime = c.time;
                  break;
                }}
                if (c.high >= slPrice) {{
                  slHit = true;
                  hitTime = c.time;
                  break;
                }}
              }}
            }}
          }}

          const finalFillTime = hitTime || activeFillTime;
          let fillEndX = safeTimeToCoordinate(finalFillTime);
          if (fillEndX === null) fillEndX = minX;
          fillEndX = Math.max(minX, Math.min(maxX, fillEndX));
          const fillWidth = Math.max(0, fillEndX - minX);

          const tpTop = Math.min(yEntry, yTP);
          const tpHeight = Math.max(2, Math.abs(yEntry - yTP));
          const slTop = Math.min(yEntry, ySL);
          const slHeight = Math.max(2, Math.abs(yEntry - ySL));

          // 1. Base Semi-Transparent Zones (NO OUTLINES)
          ctx.fillStyle = 'rgba(38, 166, 154, 0.16)';
          ctx.fillRect(minX, tpTop, boxWidth, tpHeight);

          ctx.fillStyle = 'rgba(239, 83, 80, 0.16)';
          ctx.fillRect(minX, slTop, boxWidth, slHeight);

          // 2. Denser Filled Progression Section (ONLY the relevant TP or SL region gets denser)
          if (fillWidth > 0) {{
            if (tpHit) {{
              // TP Hit -> ONLY green TP zone gets denser
              ctx.fillStyle = 'rgba(38, 166, 154, 0.50)';
              ctx.fillRect(minX, tpTop, fillWidth, tpHeight);
            }} else if (slHit) {{
              // SL Hit -> ONLY red SL zone gets denser
              ctx.fillStyle = 'rgba(239, 83, 80, 0.50)';
              ctx.fillRect(minX, slTop, fillWidth, slHeight);
            }} else {{
              // Active trade in progress -> Highlight ONLY the currently floating side (Profit = Green, Loss = Red)
              const inProfit = isLong ? (latestCandleClose >= entryPrice) : (latestCandleClose <= entryPrice);
              if (inProfit) {{
                ctx.fillStyle = 'rgba(38, 166, 154, 0.38)';
                ctx.fillRect(minX, tpTop, fillWidth, tpHeight);
              }} else {{
                ctx.fillStyle = 'rgba(239, 83, 80, 0.38)';
                ctx.fillRect(minX, slTop, fillWidth, slHeight);
              }}
            }}

            ctx.beginPath();
            ctx.strokeStyle = tpHit ? '#26a69a' : (slHit ? '#ef5350' : 'rgba(255, 255, 255, 0.35)');
            ctx.lineWidth = 1;
            ctx.setLineDash(tpHit || slHit ? [] : [3, 3]);
            ctx.moveTo(fillEndX, Math.min(tpTop, slTop));
            ctx.lineTo(fillEndX, Math.max(tpTop + tpHeight, slTop + slHeight));
            ctx.stroke();
            ctx.setLineDash([]);
          }}

          // 3. Typography (Render ONLY when cursor is hovering or drawing is selected)
          if (isHoveredOrSelected) {{
            const risk = Math.abs(entryPrice - slPrice);
            const reward = Math.abs(tpPrice - entryPrice);
            const rr = risk > 0 ? (reward / risk).toFixed(2) : '1.00';
            const riskPct = entryPrice > 0 ? ((risk / entryPrice) * 100).toFixed(2) : '0.00';
            const rewardPct = entryPrice > 0 ? ((reward / entryPrice) * 100).toFixed(2) : '0.00';

            ctx.textAlign = 'left';

            // Target Label (Top green area)
            ctx.font = '600 9.5px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
            const tpText = 'Target: ' + tpPrice.toFixed(2) + ' (+' + reward.toFixed(2) + ' | +' + rewardPct + '%)';
            ctx.textBaseline = 'top';
            ctx.fillText(tpText, minX + 6, tpTop + 5);

            // Stop Loss Label (Bottom red area)
            const slText = 'Stop: ' + slPrice.toFixed(2) + ' (-' + risk.toFixed(2) + ' | -' + riskPct + '%)';
            ctx.textBaseline = 'bottom';
            ctx.fillText(slText, minX + 6, slTop + slHeight - 5);

            // Entry & R:R Label (Right at entry line)
            ctx.font = 'bold 9.5px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillStyle = '#ffffff';
            ctx.textBaseline = 'bottom';
            ctx.fillText('Open ' + entryPrice.toFixed(2) + ' | R:R ' + rr, minX + 6, yEntry - 3);

            // Trade Outcome Badges if exited
            if (tpHit && fillEndX >= minX) {{
              ctx.fillStyle = '#26a69a';
              ctx.fillRect(fillEndX - 50, tpTop + 4, 48, 15);
              ctx.fillStyle = '#ffffff';
              ctx.font = 'bold 8.5px sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText('✓ TP HIT', fillEndX - 26, tpTop + 12);
            }} else if (slHit && fillEndX >= minX) {{
              ctx.fillStyle = '#ef5350';
              ctx.fillRect(fillEndX - 50, slTop + slHeight - 19, 48, 15);
              ctx.fillStyle = '#ffffff';
              ctx.font = 'bold 8.5px sans-serif';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText('✗ SL HIT', fillEndX - 26, slTop + slHeight - 11);
            }}
          }}

          if (isSelected) {{
            // 5 Interactive Position Handles
            renderHandle(midX, yEntry); // Entry Level Handle
            renderHandle(midX, yTP);    // TP Price Handle
            renderHandle(midX, ySL);    // SL Price Handle
            renderHandle(minX, yEntry); // Left Time Handle
            renderHandle(maxX, yEntry); // Right Time / Width Handle
          }}
        }}
      }}
      ctx.restore();
    }});

    // 3. Real-Time Interactive Live Drawing Preview (Rubberband for multi-point lines)
    if (activeTool !== 'CURSOR' && activeTool !== 'LONG_POSITION' && activeTool !== 'SHORT_POSITION' && tempDrawingPoints.length > 0 && liveMousePoint) {{
      ctx.save();
      ctx.strokeStyle = '#2962ff';
      ctx.fillStyle = 'rgba(41, 98, 255, 0.25)';
      ctx.lineWidth = 1.0;
      ctx.setLineDash([4, 4]);

      const x1 = safeTimeToCoordinate(tempDrawingPoints[0].time);
      const y1 = safePriceToCoordinate(tempDrawingPoints[0].price);
      const x2 = liveMousePoint.x;
      const y2 = liveMousePoint.y;

      if (x1 !== null && y1 !== null) {{
        if (activeTool === 'TRENDLINE' || activeTool === 'RAY' || activeTool === 'ARROW' || activeTool === 'MEASURE') {{
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
          renderHandle(x1, y1);
          renderHandle(x2, y2);
        }}
        else if (activeTool === 'PATH') {{
          ctx.beginPath();
          let f = true;
          tempDrawingPoints.forEach(p => {{
            const px = safeTimeToCoordinate(p.time);
            const py = safePriceToCoordinate(p.price);
            if (px !== null && py !== null) {{
              if (f) {{ ctx.moveTo(px, py); f = false; }}
              else {{ ctx.lineTo(px, py); }}
            }}
          }});
          ctx.lineTo(x2, y2);
          ctx.stroke();
          tempDrawingPoints.forEach(p => {{
            const px = safeTimeToCoordinate(p.time);
            const py = safePriceToCoordinate(p.price);
            if (px !== null && py !== null) renderHandle(px, py);
          }});
          renderHandle(x2, y2);
        }}
        else if (activeTool === 'VOLUME_PROFILE') {{
          const rx = Math.min(x1, x2);
          const ry = Math.min(y1, y2);
          const rw = Math.abs(x2 - x1);
          const rh = Math.abs(y2 - y1);
          ctx.fillRect(rx, ry, rw, rh);
          ctx.strokeRect(rx, ry, rw, rh);
          ctx.fillStyle = '#2962ff';
          ctx.font = 'bold 11px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('Volume Profile Range', rx + rw / 2, ry + rh / 2);
          renderHandle(rx, ry);
          renderHandle(rx + rw, ry + rh);
        }}
        else if (activeTool === 'RECTANGLE') {{
          const rx = Math.min(x1, x2);
          const ry = Math.min(y1, y2);
          const rw = Math.abs(x2 - x1);
          const rh = Math.abs(y2 - y1);
          ctx.fillRect(rx, ry, rw, rh);
          ctx.strokeRect(rx, ry, rw, rh);
          renderHandle(rx, ry);
          renderHandle(rx + rw, ry + rh);
        }}
        else if (activeTool === 'FIBONACCI') {{
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
          const minX = Math.min(x1, x2);
          const maxX = Math.max(x1, x2) + 160;
          [0, 0.382, 0.5, 0.618, 1.0].forEach(lvl => {{
            const ly = y1 + (y2 - y1) * lvl;
            ctx.beginPath();
            ctx.moveTo(minX, ly);
            ctx.lineTo(maxX, ly);
            ctx.stroke();
          }});
        }}
      }}
      ctx.restore();
    }}
  }}

  function renderHandle(x, y) {{
    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.strokeStyle = '#2962ff';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();
  }}

  // Floating Property Toolbar Position & Sync
  function updatePropToolbarPosition() {{
    if (!selectedDrawingId || isCreatingDrawing || draggingHandle) {{
      propToolbar.style.display = 'none';
      return;
    }}

    if (lastSelectedDrawingId !== selectedDrawingId) {{
      toolbarDragOffset = {{ x: 0, y: 0 }};
      lastSelectedDrawingId = selectedDrawingId;
    }}

    const targetD = drawings.find(d => d.id === selectedDrawingId);
    if (!targetD || !targetD.points || targetD.points.length === 0) {{
      propToolbar.style.display = 'none';
      return;
    }}

    // Find bounding box in pixel coordinates across all points
    let minX = 99999, maxX = -99999, minY = 99999, maxY = -99999;
    targetD.points.forEach(p => {{
      const px = safeTimeToCoordinate(p.time);
      const py = safePriceToCoordinate(p.price);
      if (px !== null && py !== null) {{
        if (px < minX) minX = px;
        if (px > maxX) maxX = px;
        if (py < minY) minY = py;
        if (py > maxY) maxY = py;
      }}
    }});

    if (minY === 99999) {{
      propToolbar.style.display = 'none';
      return;
    }}

    const isPos = (targetD.type === 'LONG_POSITION' || targetD.type === 'SHORT_POSITION');
    const tbWidth = propToolbar.offsetWidth || (isPos ? 540 : 440);
    const tbHeight = propToolbar.offsetHeight || 34;

    const centerX = (minX + maxX) / 2;
    const GAP = 30; // Generous clearance so toolbar never covers handles or drawing

    let posX = centerX - (tbWidth / 2);
    let posY = minY - tbHeight - GAP;

    // If too close to the top of the chart, flip comfortably below the drawing
    if (posY < 12) {{
      if (maxY + GAP + tbHeight <= container.clientHeight - 10) {{
        posY = maxY + GAP;
      }} else {{
        posY = 12;
      }}
    }}

    // Apply manual drag offset if user repositioned it
    posX += toolbarDragOffset.x;
    posY += toolbarDragOffset.y;

    // Clamp inside visible chart container
    posX = Math.max(10, Math.min(container.clientWidth - tbWidth - 10, posX));
    posY = Math.max(10, Math.min(container.clientHeight - tbHeight - 10, posY));

    propToolbar.style.left = posX + 'px';
    propToolbar.style.top = posY + 'px';
    propToolbar.style.display = 'flex';

    if (isPos) {{
      document.getElementById('prop-standard-controls').style.display = 'none';
      document.getElementById('prop-position-controls').style.display = 'flex';

      const isLong = (targetD.type === 'LONG_POSITION');
      const typeBadge = document.getElementById('prop-pos-type-badge');
      typeBadge.innerText = isLong ? 'LONG' : 'SHORT';
      typeBadge.style.backgroundColor = isLong ? 'rgba(38, 166, 154, 0.25)' : 'rgba(239, 83, 80, 0.25)';
      typeBadge.style.color = isLong ? '#26a69a' : '#ef5350';
      typeBadge.style.border = '1px solid ' + (isLong ? '#26a69a' : '#ef5350');

      const entryP = targetD.points[0].price;
      const slP = targetD.points[1].price;
      const tpP = targetD.points[2].price;
      const risk = Math.abs(entryP - slP);
      const reward = Math.abs(tpP - entryP);
      const rr = risk > 0 ? (reward / risk).toFixed(2) : '1.00';

      document.getElementById('prop-pos-rr-badge').innerText = 'R:R ' + rr;
      document.getElementById('prop-pos-risk-badge').innerText = 'Risk: -' + risk.toFixed(2);
      document.getElementById('prop-pos-reward-badge').innerText = 'Target: +' + reward.toFixed(2);

      let latestPrice = entryP;
      if (currentCandles && currentCandles.length > 0) {{
        latestPrice = currentCandles[currentCandles.length - 1].close;
      }}

      let orderType = isLong ? 'BUY' : 'SELL';
      let btnText = isLong ? '⚡ Buy Market' : '⚡ Sell Market';

      const pDiff = entryP - latestPrice;
      if (Math.abs(pDiff) > 0.05) {{
        if (isLong) {{
          if (entryP < latestPrice) {{
            orderType = 'BUY_LIMIT';
            btnText = '⚡ Place Buy Limit @ ' + entryP.toFixed(2);
          }} else {{
            orderType = 'BUY_STOP';
            btnText = '⚡ Place Buy Stop @ ' + entryP.toFixed(2);
          }}
        }} else {{
          if (entryP > latestPrice) {{
            orderType = 'SELL_LIMIT';
            btnText = '⚡ Place Sell Limit @ ' + entryP.toFixed(2);
          }} else {{
            orderType = 'SELL_STOP';
            btnText = '⚡ Place Sell Stop @ ' + entryP.toFixed(2);
          }}
        }}
      }}

      const execBtn = document.getElementById('prop-btn-exec-trade');
      if (execBtn) {{
        execBtn.innerText = btnText;
        execBtn.setAttribute('data-order-type', orderType);
        execBtn.style.backgroundColor = isLong ? '#26a69a' : '#ef5350';
      }}
    }} else {{
      document.getElementById('prop-standard-controls').style.display = 'flex';
      document.getElementById('prop-position-controls').style.display = 'none';

      // Synchronize input controls
      const style = targetD.style || {{}};
      document.getElementById('prop-outline-color').value = colorToHex(style.color || '#2962ff');
      document.getElementById('prop-line-width').value = String(style.line_width !== undefined ? style.line_width : '1.5');
      document.getElementById('prop-line-style').value = style.line_style || 'solid';
      
      document.getElementById('prop-fill-color').value = colorToHex(style.fill_color || '#2962ff');
      document.getElementById('prop-fill-opacity').value = String(style.opacity !== undefined ? style.opacity : '0.20');
      
      document.getElementById('prop-text-input').value = targetD.text || '';
    }}

    document.getElementById('prop-btn-lock').innerText = targetD.locked ? '🔒' : '🔓';
  }}

  function setupPropertyToolbarEvents() {{
    ['mousedown', 'mouseup', 'click', 'pointerdown', 'pointerup', 'touchstart', 'touchend'].forEach(evtName => {{
      propToolbar.addEventListener(evtName, (e) => {{
        e.stopPropagation();
      }});
    }});

    const dragHandle = document.getElementById('prop-drag-handle');
    if (dragHandle) {{
      let dragStartMouse = {{ x: 0, y: 0 }};
      let dragStartOffset = {{ x: 0, y: 0 }};

      dragHandle.addEventListener('mousedown', (e) => {{
        e.stopPropagation();
        e.preventDefault();
        isDraggingToolbar = true;
        dragStartMouse = {{ x: e.clientX, y: e.clientY }};
        dragStartOffset = {{ x: toolbarDragOffset.x, y: toolbarDragOffset.y }};
        dragHandle.style.cursor = 'grabbing';

        const onMouseMove = (moveEvt) => {{
          if (!isDraggingToolbar) return;
          const dx = moveEvt.clientX - dragStartMouse.x;
          const dy = moveEvt.clientY - dragStartMouse.y;
          toolbarDragOffset = {{
            x: dragStartOffset.x + dx,
            y: dragStartOffset.y + dy
          }};
          updatePropToolbarPosition();
        }};

        const onMouseUp = () => {{
          isDraggingToolbar = false;
          if (dragHandle) dragHandle.style.cursor = 'grab';
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);
        }};

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      }});
    }}

    const outlineColorInput = document.getElementById('prop-outline-color');
    const lineWidthSelect = document.getElementById('prop-line-width');
    const lineStyleSelect = document.getElementById('prop-line-style');
    const fillColorInput = document.getElementById('prop-fill-color');
    const fillOpacitySelect = document.getElementById('prop-fill-opacity');
    const textInput = document.getElementById('prop-text-input');
    const lockBtn = document.getElementById('prop-btn-lock');
    const settingsBtn = document.getElementById('prop-btn-settings');
    const deleteBtn = document.getElementById('prop-btn-delete');

    function notifyUpdated(d) {{
      scheduleRender();
      if (window.qtBridge && window.qtBridge.onDrawingUpdated) {{
        window.qtBridge.onDrawingUpdated(JSON.stringify(d));
      }}
    }}

    // 1. Outline Color ONLY modifies outline
    outlineColorInput.addEventListener('input', () => {{
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (!d) return;
      if (!d.style) d.style = {{}};
      d.style.color = outlineColorInput.value;
      notifyUpdated(d);
    }});

    // 2. Line Width ONLY modifies line width
    lineWidthSelect.addEventListener('change', () => {{
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (!d) return;
      if (!d.style) d.style = {{}};
      d.style.line_width = parseFloat(lineWidthSelect.value);
      notifyUpdated(d);
    }});

    // 3. Line Style ONLY modifies line style
    lineStyleSelect.addEventListener('change', () => {{
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (!d) return;
      if (!d.style) d.style = {{}};
      d.style.line_style = lineStyleSelect.value;
      notifyUpdated(d);
    }});

    // 4. Fill Color ONLY modifies fill color RGB
    fillColorInput.addEventListener('input', () => {{
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (!d) return;
      if (!d.style) d.style = {{}};
      const alpha = d.style.opacity !== undefined ? d.style.opacity : 0.25;
      d.style.fill_color = hexAndAlphaToRgba(fillColorInput.value, alpha);
      notifyUpdated(d);
    }});

    // 5. Fill Opacity ONLY modifies opacity alpha
    fillOpacitySelect.addEventListener('change', () => {{
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (!d) return;
      if (!d.style) d.style = {{}};
      const alpha = parseFloat(fillOpacitySelect.value);
      d.style.opacity = alpha;
      const hex = colorToHex(d.style.fill_color || fillColorInput.value);
      d.style.fill_color = hexAndAlphaToRgba(hex, alpha);
      notifyUpdated(d);
    }});

    // 6. Text Label
    textInput.addEventListener('input', () => {{
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (!d) return;
      d.text = textInput.value;
      notifyUpdated(d);
    }});

    lockBtn.addEventListener('click', (e) => {{
      e.stopPropagation();
      const d = drawings.find(x => x.id === selectedDrawingId);
      if (d) {{
        d.locked = !d.locked;
        lockBtn.innerText = d.locked ? '🔒' : '🔓';
        notifyUpdated(d);
      }}
    }});

    settingsBtn.addEventListener('click', (e) => {{
      e.stopPropagation();
      if (selectedDrawingId && window.qtBridge && window.qtBridge.openProperties) {{
        window.qtBridge.openProperties(selectedDrawingId);
      }}
    }});

    deleteBtn.addEventListener('click', (e) => {{
      e.stopPropagation();
      if (selectedDrawingId) {{
        const idToDelete = selectedDrawingId;
        drawings = drawings.filter(x => x.id !== idToDelete);
        selectedDrawingId = null;
        propToolbar.style.display = 'none';
        scheduleRender();
        if (window.qtBridge && window.qtBridge.onDrawingDeleted) {{
          window.qtBridge.onDrawingDeleted(idToDelete);
        }}
      }}
    }});

    const execBtn = document.getElementById('prop-btn-exec-trade');
    if (execBtn) {{
      execBtn.addEventListener('click', (e) => {{
        e.stopPropagation();
        if (!selectedDrawingId) return;
        const targetD = drawings.find(x => x.id === selectedDrawingId);
        if (!targetD || (targetD.type !== 'LONG_POSITION' && targetD.type !== 'SHORT_POSITION')) return;
        if (targetD.points.length < 3) return;

        const isLong = (targetD.type === 'LONG_POSITION');
        const entryP = targetD.points[0].price;
        const slP = targetD.points[1].price;
        const tpP = targetD.points[2].price;
        const orderType = execBtn.getAttribute('data-order-type') || (isLong ? 'BUY' : 'SELL');

        if (window.qtBridge && window.qtBridge.onExecuteTradeFromDrawing) {{
          window.qtBridge.onExecuteTradeFromDrawing(JSON.stringify({{
            direction: isLong ? 'BUY' : 'SELL',
            order_type: orderType,
            entry: entryP,
            sl: slP,
            tp: tpP,
            drawing_id: targetD.id,
          }}));
        }}
      }});
    }}

    const applyBtn = document.getElementById('prop-btn-apply-panel');
    if (applyBtn) {{
      applyBtn.addEventListener('click', (e) => {{
        e.stopPropagation();
        if (!selectedDrawingId) return;
        const targetD = drawings.find(x => x.id === selectedDrawingId);
        if (!targetD || (targetD.type !== 'LONG_POSITION' && targetD.type !== 'SHORT_POSITION')) return;
        if (targetD.points.length < 3) return;

        const isLong = (targetD.type === 'LONG_POSITION');
        const entryP = targetD.points[0].price;
        const slP = targetD.points[1].price;
        const tpP = targetD.points[2].price;
        const orderType = execBtn.getAttribute('data-order-type') || (isLong ? 'BUY' : 'SELL');

        if (window.qtBridge && window.qtBridge.onApplyToOrderPanel) {{
          window.qtBridge.onApplyToOrderPanel(JSON.stringify({{
            direction: isLong ? 'BUY' : 'SELL',
            order_type: orderType,
            entry: entryP,
            sl: slP,
            tp: tpP,
            drawing_id: targetD.id,
          }}));
        }}
      }});
    }}

    const limitBtn = document.getElementById('prop-btn-exec-limit');
    if (limitBtn) {{
      limitBtn.addEventListener('click', (e) => {{
        e.stopPropagation();
        if (!selectedDrawingId) return;
        const targetD = drawings.find(x => x.id === selectedDrawingId);
        if (!targetD || (targetD.type !== 'LONG_POSITION' && targetD.type !== 'SHORT_POSITION')) return;
        if (targetD.points.length < 3) return;

        const isLong = (targetD.type === 'LONG_POSITION');
        const entryP = targetD.points[0].price;
        const slP = targetD.points[1].price;
        const tpP = targetD.points[2].price;
        let latestPrice = entryP;
        if (currentCandles && currentCandles.length > 0) {{
          latestPrice = currentCandles[currentCandles.length - 1].close;
        }}
        const orderType = isLong ? (entryP < latestPrice ? 'BUY_LIMIT' : 'BUY_STOP') : (entryP > latestPrice ? 'SELL_LIMIT' : 'SELL_STOP');

        if (window.qtBridge && window.qtBridge.onExecuteTradeFromDrawing) {{
          window.qtBridge.onExecuteTradeFromDrawing(JSON.stringify({{
            direction: isLong ? 'BUY' : 'SELL',
            order_type: orderType,
            entry: entryP,
            sl: slP,
            tp: tpP,
            drawing_id: targetD.id,
          }}));
        }}
      }});
    }}

    const beBtn = document.getElementById('prop-btn-move-be');
    if (beBtn) {{
      beBtn.addEventListener('click', (e) => {{
        e.stopPropagation();
        if (!selectedDrawingId) return;
        const targetD = drawings.find(x => x.id === selectedDrawingId);
        if (!targetD) return;

        if (window.qtBridge && window.qtBridge.onExecuteTradeFromDrawing) {{
          window.qtBridge.onExecuteTradeFromDrawing(JSON.stringify({{
            action: 'MOVE_BE',
            order_type: 'MOVE_BE',
            drawing_id: targetD.id,
          }}));
        }}
      }});
    }}
  }}

  // Handle Hit Testing
  function findHitHandle(x, y) {{
    for (let i = drawings.length - 1; i >= 0; i--) {{
      const d = drawings[i];
      if (!d.visible || !d.points || d.locked) continue;

      if (d.type === 'RECTANGLE' && d.points.length >= 2) {{
        const x1 = safeTimeToCoordinate(d.points[0].time);
        const y1 = safePriceToCoordinate(d.points[0].price);
        const x2 = safeTimeToCoordinate(d.points[1].time);
        const y2 = safePriceToCoordinate(d.points[1].price);

        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
          const minX = Math.min(x1, x2);
          const maxX = Math.max(x1, x2);
          const minY = Math.min(y1, y2);
          const maxY = Math.max(y1, y2);
          const midX = (minX + maxX) / 2;
          const midY = (minY + maxY) / 2;

          const handles = [
            {{ name: 'nw', hx: minX, hy: minY }},
            {{ name: 'n',  hx: midX, hy: minY }},
            {{ name: 'ne', hx: maxX, hy: minY }},
            {{ name: 'e',  hx: maxX, hy: midY }},
            {{ name: 'se', hx: maxX, hy: maxY }},
            {{ name: 's',  hx: midX, hy: maxY }},
            {{ name: 'sw', hx: minX, hy: maxY }},
            {{ name: 'w',  hx: minX, hy: midY }},
          ];

          for (const h of handles) {{
            if (Math.hypot(h.hx - x, h.hy - y) <= 12) {{
              return {{
                drawingId: d.id,
                drawing: d,
                type: 'rect_handle',
                handleName: h.name,
                minX: minX, maxX: maxX, minY: minY, maxY: maxY
              }};
            }}
          }}
        }}
      }}
      else if ((d.type === 'LONG_POSITION' || d.type === 'SHORT_POSITION') && d.points.length >= 3) {{
        const tStart = d.points[0].time;
        const tEnd = (d.points.length >= 4 && d.points[3].time) ? d.points[3].time : (tStart + 14400);

        let x1 = safeTimeToCoordinate(tStart);
        let x2 = safeTimeToCoordinate(tEnd);
        if (x1 === null && x2 !== null) x1 = x2 - 160;
        if (x2 === null && x1 !== null) x2 = x1 + 160;
        if (x1 === null && x2 === null) {{
          x1 = 100;
          x2 = 260;
        }}

        const minX = Math.min(x1, x2);
        const maxX = Math.max(x1, x2);
        const midX = (minX + maxX) / 2;

        const yEntry = safePriceToCoordinate(d.points[0].price);
        const ySL = safePriceToCoordinate(d.points[1].price);
        const yTP = safePriceToCoordinate(d.points[2].price);

        if (yEntry !== null && ySL !== null && yTP !== null) {{
          const posHandles = [
            {{ name: 'entry', hx: midX, hy: yEntry }},
            {{ name: 'tp',    hx: midX, hy: yTP }},
            {{ name: 'sl',    hx: midX, hy: ySL }},
            {{ name: 'left',  hx: minX, hy: yEntry }},
            {{ name: 'right', hx: maxX, hy: yEntry }},
          ];

          for (const ph of posHandles) {{
            if (Math.hypot(ph.hx - x, ph.hy - y) <= 12) {{
              return {{
                drawingId: d.id,
                drawing: d,
                type: 'pos_handle',
                handleName: ph.name
              }};
            }}
          }}
        }}
      }}
      else if (d.type === 'VOLUME_PROFILE' && d.points.length >= 2) {{
        const t1 = d.points[0].time;
        const t2 = d.points[1].time;
        const x1 = safeTimeToCoordinate(Math.min(t1, t2));
        const x2 = safeTimeToCoordinate(Math.max(t1, t2));
        const midY = container.clientHeight / 2;
        if (x1 !== null && Math.hypot(x1 - x, midY - y) <= 15) {{
          return {{ drawingId: d.id, pointIndex: 0, type: 'standard_handle', drawing: d }};
        }}
        if (x2 !== null && Math.hypot(x2 - x, midY - y) <= 15) {{
          return {{ drawingId: d.id, pointIndex: 1, type: 'standard_handle', drawing: d }};
        }}
      }}
      else {{
        for (let pIdx = 0; pIdx < d.points.length; pIdx++) {{
          const px = safeTimeToCoordinate(d.points[pIdx].time);
          const py = safePriceToCoordinate(d.points[pIdx].price);
          if (px !== null && py !== null && Math.hypot(px - x, py - y) <= 12) {{
            return {{ drawingId: d.id, pointIndex: pIdx, type: 'standard_handle', drawing: d }};
          }}
        }}
      }}
    }}
    return null;
  }}

  function findHitDrawingBody(x, y) {{
    const clickPrice = safeCoordinateToPrice(y);
    if (clickPrice === null) return null;

    for (let i = drawings.length - 1; i >= 0; i--) {{
      const d = drawings[i];
      if (!d.visible || !d.points || d.points.length === 0) continue;

      if (d.type === 'HORIZONTAL_LINE') {{
        const py = safePriceToCoordinate(d.points[0].price);
        if (py !== null && Math.abs(py - y) <= 10) return d;
      }}
      else if (d.type === 'VERTICAL_LINE') {{
        const px = safeTimeToCoordinate(d.points[0].time);
        if (px !== null && Math.abs(px - x) <= 10) return d;
      }}
      else if (d.type === 'RECTANGLE' && d.points.length >= 2) {{
        const x1 = safeTimeToCoordinate(d.points[0].time);
        const y1 = safePriceToCoordinate(d.points[0].price);
        const x2 = safeTimeToCoordinate(d.points[1].time);
        const y2 = safePriceToCoordinate(d.points[1].price);
        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
          const minX = Math.min(x1, x2) - 6;
          const maxX = Math.max(x1, x2) + 6;
          const minY = Math.min(y1, y2) - 6;
          const maxY = Math.max(y1, y2) + 6;
          if (x >= minX && x <= maxX && y >= minY && y <= maxY) return d;
        }}
      }}
      else if (d.type === 'VOLUME_PROFILE' && d.points.length >= 2) {{
        const t1 = d.points[0].time;
        const t2 = d.points[1].time;
        const x1 = safeTimeToCoordinate(Math.min(t1, t2));
        const x2 = safeTimeToCoordinate(Math.max(t1, t2));
        if (x1 !== null && x2 !== null) {{
          if (x >= x1 - 8 && x <= x2 + 8) return d;
        }}
      }}
      else if (d.type === 'PATH' && d.points.length >= 2) {{
        for (let pI = 0; pI < d.points.length - 1; pI++) {{
          const xA = safeTimeToCoordinate(d.points[pI].time);
          const yA = safePriceToCoordinate(d.points[pI].price);
          const xB = safeTimeToCoordinate(d.points[pI + 1].time);
          const yB = safePriceToCoordinate(d.points[pI + 1].price);
          if (xA !== null && yA !== null && xB !== null && yB !== null) {{
            if (distToSegment(x, y, xA, yA, xB, yB) <= 10) return d;
          }}
        }}
      }}
      else if (d.type === 'LONG_POSITION' || d.type === 'SHORT_POSITION') {{
        const tStart = d.points[0].time;
        const tEnd = (d.points.length >= 4 && d.points[3].time) ? d.points[3].time : (tStart + 14400);
        let x1 = safeTimeToCoordinate(tStart);
        let x2 = safeTimeToCoordinate(tEnd);
        if (x1 === null && x2 !== null) x1 = x2 - 160;
        if (x2 === null && x1 !== null) x2 = x1 + 160;
        if (x1 !== null && x2 !== null) {{
          const minX = Math.min(x1, x2);
          const maxX = Math.max(x1, x2);
          const yEntry = safePriceToCoordinate(d.points[0].price);
          const ySL = safePriceToCoordinate(d.points[1].price);
          const yTP = safePriceToCoordinate(d.points[2].price);
          if (yEntry !== null && ySL !== null && yTP !== null) {{
            const minY = Math.min(yEntry, ySL, yTP);
            const maxY = Math.max(yEntry, ySL, yTP);
            if (x >= minX && x <= maxX && y >= minY && y <= maxY) return d;
          }}
        }}
      }}
      else if (d.points.length >= 2) {{
        const x1 = safeTimeToCoordinate(d.points[0].time);
        const y1 = safePriceToCoordinate(d.points[0].price);
        const x2 = safeTimeToCoordinate(d.points[1].time);
        const y2 = safePriceToCoordinate(d.points[1].price);
        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
          const dist = distToSegment(x, y, x1, y1, x2, y2);
          if (dist <= 10) return d;
        }}
      }}
    }}
    return null;
  }}

  function distToSegment(px, py, x1, y1, x2, y2) {{
    const l2 = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
    if (l2 === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
  }}

  // Setup Interaction Events
  function setupInteractionEvents() {{
    container.addEventListener('mousemove', (e) => {{
      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const price = safeCoordinateToPrice(y);
      const time = safeCoordinateToTime(x);

      const isShift = (e.shiftKey || isShiftPressed);
      let effectiveX = x;
      let effectiveY = y;
      let effectivePrice = price;
      let effectiveTime = time;

      // When drawing with anchor points, apply Shift snap
      if (isShift && tempDrawingPoints.length > 0) {{
        const lastAnchor = tempDrawingPoints[tempDrawingPoints.length - 1];
        if (activeTool === 'RECTANGLE') {{
          const rx1 = safeTimeToCoordinate(lastAnchor.time);
          const ry1 = safePriceToCoordinate(lastAnchor.price);
          if (rx1 !== null && ry1 !== null) {{
            const dx = x - rx1;
            const dy = y - ry1;
            const side = Math.max(Math.abs(dx), Math.abs(dy));
            effectiveX = rx1 + (dx >= 0 ? side : -side);
            effectiveY = ry1 + (dy >= 0 ? side : -side);
            effectivePrice = safeCoordinateToPrice(effectiveY);
            effectiveTime = safeCoordinateToTime(effectiveX);
          }}
        }} else {{
          const snapped = getSnappedPoint(lastAnchor.time, lastAnchor.price, x, y);
          effectiveX = snapped.x;
          effectiveY = snapped.y;
          effectivePrice = (snapped.price !== null) ? snapped.price : price;
          effectiveTime = (snapped.time !== null) ? snapped.time : time;
        }}
      }}

      // Update Hover ID for responsive hover stats display
      const hitHandle = findHitHandle(x, y);
      const hitBody = findHitDrawingBody(x, y);
      const newHoverId = hitHandle ? hitHandle.drawingId : (hitBody ? hitBody.id : null);
      if (newHoverId !== hoveredDrawingId) {{
        hoveredDrawingId = newHoverId;
        scheduleRender();
      }}

      // Real-time Live Rubberband Preview & Persistent Crosshairs for ALL active tools
      if (activeTool !== 'CURSOR') {{
        liveMousePoint = {{
          x: effectiveX,
          y: effectiveY,
          price: effectivePrice,
          time: effectiveTime,
          rawX: x,
          rawY: y
        }};
        scheduleRender();
        return;
      }}

      // Active Handle Dragging with Shift Snap support
      if (draggingHandle) {{
        const targetD = drawings.find(d => d.id === draggingHandle.drawingId);
        if (!targetD) return;

        let curPrice = (price !== null) ? price : draggingHandle.startPrice;
        let curTime = (time !== null) ? time : draggingHandle.startTime;

        if (isShift && draggingHandle.type === 'standard_handle' && targetD.points && targetD.points.length >= 2) {{
          let anchorIdx = (draggingHandle.pointIndex === 0) ? 1 : 0;
          if (draggingHandle.pointIndex > 1) anchorIdx = draggingHandle.pointIndex - 1;
          const anchorP = targetD.points[anchorIdx];
          if (anchorP) {{
            const snapped = getSnappedPoint(anchorP.time, anchorP.price, x, y);
            if (snapped.price !== null) curPrice = snapped.price;
            if (snapped.time !== null) curTime = snapped.time;
          }}
        }}

        if (draggingHandle.type === 'standard_handle') {{
          if (targetD.points[draggingHandle.pointIndex]) {{
            targetD.points[draggingHandle.pointIndex].price = curPrice;
            targetD.points[draggingHandle.pointIndex].time = curTime;
          }}
        }}
        else if (draggingHandle.type === 'rect_handle') {{
          const hName = draggingHandle.handleName;
          const p0 = targetD.points[0];
          const p1 = targetD.points[1];

          const minT = Math.min(draggingHandle.origPoints[0].time, draggingHandle.origPoints[1].time);
          const maxT = Math.max(draggingHandle.origPoints[0].time, draggingHandle.origPoints[1].time);
          const minP = Math.min(draggingHandle.origPoints[0].price, draggingHandle.origPoints[1].price);
          const maxP = Math.max(draggingHandle.origPoints[0].price, draggingHandle.origPoints[1].price);

          let newMinT = minT, newMaxT = maxT, newMinP = minP, newMaxP = maxP;

          if (hName.includes('n')) newMaxP = curPrice;
          if (hName.includes('s')) newMinP = curPrice;
          if (hName.includes('w')) newMinT = curTime;
          if (hName.includes('e')) newMaxT = curTime;

          p0.time = newMinT;
          p0.price = newMaxP;
          p1.time = newMaxT;
          p1.price = newMinP;
        }}
        else if (draggingHandle.type === 'pos_handle') {{
          const hName = draggingHandle.handleName;
          if (hName === 'tp') {{
            targetD.points[2].price = curPrice;
          }} else if (hName === 'sl') {{
            targetD.points[1].price = curPrice;
          }} else if (hName === 'entry') {{
            const pDelta = curPrice - draggingHandle.startPrice;
            targetD.points[0].price = draggingHandle.origPoints[0].price + pDelta;
            targetD.points[1].price = draggingHandle.origPoints[1].price + pDelta;
            targetD.points[2].price = draggingHandle.origPoints[2].price + pDelta;
          }} else if (hName === 'right') {{
            const tDelta = curTime - draggingHandle.startTime;
            const origEnd = draggingHandle.origPoints[3] ? draggingHandle.origPoints[3].time : (draggingHandle.origPoints[0].time + 14400);
            if (targetD.points.length < 4) {{
              targetD.points.push({{ time: origEnd + tDelta, price: targetD.points[0].price }});
            }} else {{
              targetD.points[3].time = origEnd + tDelta;
            }}
          }} else if (hName === 'left') {{
            const tDelta = curTime - draggingHandle.startTime;
            targetD.points[0].time = draggingHandle.origPoints[0].time + tDelta;
            targetD.points[1].time = draggingHandle.origPoints[1].time + tDelta;
            targetD.points[2].time = draggingHandle.origPoints[2].time + tDelta;
          }}
        }}
        else if (draggingHandle.type === 'body') {{
          const priceDelta = curPrice - draggingHandle.startPrice;
          const timeDelta = curTime - draggingHandle.startTime;

          targetD.points.forEach((p, idx) => {{
            const orig = draggingHandle.origPoints[idx];
            if (orig) {{
              p.price = orig.price + priceDelta;
              p.time = orig.time + timeDelta;
            }}
          }});
        }}
        scheduleRender();
        return;
      }}

      // Hover Hit Testing & Cursors
      if (hitHandle) {{
        canvas.style.pointerEvents = 'auto';
        if (hitHandle.type === 'rect_handle') {{
          const hn = hitHandle.handleName;
          if (hn === 'nw' || hn === 'se') canvas.style.cursor = 'nwse-resize';
          else if (hn === 'ne' || hn === 'sw') canvas.style.cursor = 'nesw-resize';
          else if (hn === 'n' || hn === 's') canvas.style.cursor = 'ns-resize';
          else if (hn === 'e' || hn === 'w') canvas.style.cursor = 'ew-resize';
        }} else if (hitHandle.type === 'pos_handle') {{
          const hn = hitHandle.handleName;
          if (hn === 'tp' || hn === 'sl' || hn === 'entry') canvas.style.cursor = 'ns-resize';
          else canvas.style.cursor = 'ew-resize';
        }} else {{
          canvas.style.cursor = 'pointer';
        }}
      }} else {{
        if (hitBody && !hitBody.locked) {{
          canvas.style.pointerEvents = 'auto';
          canvas.style.cursor = 'grab';
        }} else {{
          canvas.style.pointerEvents = 'none';
          canvas.style.cursor = 'default';
        }}
      }}
    }});

    container.addEventListener('mouseleave', () => {{
      if (hoveredDrawingId !== null) {{
        hoveredDrawingId = null;
      }}
      if (activeTool !== 'CURSOR') {{
        liveMousePoint = null;
      }}
      scheduleRender();
    }});

    container.addEventListener('mousedown', (e) => {{
      if (e.target.closest('#drawing-prop-toolbar')) return;

      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      let price = safeCoordinateToPrice(y);
      let time = safeCoordinateToTime(x);

      const isShift = (e.shiftKey || isShiftPressed);
      if (isShift && tempDrawingPoints.length > 0) {{
        const lastAnchor = tempDrawingPoints[tempDrawingPoints.length - 1];
        if (activeTool === 'RECTANGLE') {{
          const rx1 = safeTimeToCoordinate(lastAnchor.time);
          const ry1 = safePriceToCoordinate(lastAnchor.price);
          if (rx1 !== null && ry1 !== null) {{
            const dx = x - rx1;
            const dy = y - ry1;
            const side = Math.max(Math.abs(dx), Math.abs(dy));
            const effX = rx1 + (dx >= 0 ? side : -side);
            const effY = ry1 + (dy >= 0 ? side : -side);
            price = safeCoordinateToPrice(effY);
            time = safeCoordinateToTime(effX);
          }}
        }} else {{
          const snapped = getSnappedPoint(lastAnchor.time, lastAnchor.price, x, y);
          if (snapped.price !== null) price = snapped.price;
          if (snapped.time !== null) time = snapped.time;
        }}
      }}

      // Active Tool Creation Mousedown
      if (activeTool !== 'CURSOR') {{
        if (price === null || time === null) return;

        // SINGLE-CLICK INSTANT DROP for Long & Short Positions
        if (activeTool === 'LONG_POSITION' || activeTool === 'SHORT_POSITION') {{
          const isLong = (activeTool === 'LONG_POSITION');
          const entryP = price;
          const slP = isLong ? (entryP * 0.995) : (entryP * 1.005);
          const tpP = isLong ? (entryP * 1.010) : (entryP * 0.990);
          const tStart = time;
          const tEnd = time + 14400; // 4 hours standard width

          const finalPoints = [
            {{ time: tStart, price: entryP }},
            {{ time: tStart, price: slP }},
            {{ time: tStart, price: tpP }},
            {{ time: tEnd, price: entryP }}
          ];

          finishCreation(finalPoints);
          return;
        }}

        // Single-click line tools
        if (activeTool === 'HORIZONTAL_LINE' || activeTool === 'VERTICAL_LINE') {{
          finishCreation([{{ time: time, price: price }}]);
          return;
        }}
        if (activeTool === 'TEXT') {{
          const userText = prompt('Enter text label:');
          if (userText) {{
            finishCreation([{{ time: time, price: price }}], userText);
          }} else {{
            setActiveTool('CURSOR');
          }}
          return;
        }}

        // Multi-point tools: First Click or Second Click
        if (activeTool === 'PATH') {{
          if (tempDrawingPoints.length === 0) {{
            tempDrawingPoints.push({{ time: time, price: price }});
            startCreationPoint = {{ x: x, y: y, time: time, price: price }};
            isCreatingDrawing = true;
            liveMousePoint = {{ x: x, y: y, price: price, time: time, rawX: x, rawY: y }};
            scheduleRender();
          }} else {{
            const lastP = tempDrawingPoints[tempDrawingPoints.length - 1];
            const lastX = safeTimeToCoordinate(lastP.time);
            const lastY = safePriceToCoordinate(lastP.price);
            if (lastX !== null && lastY !== null && Math.hypot(x - lastX, y - lastY) < 10) {{
              if (tempDrawingPoints.length >= 2) {{
                finishCreation(tempDrawingPoints);
              }}
            }} else {{
              tempDrawingPoints.push({{ time: time, price: price }});
              scheduleRender();
            }}
          }}
          return;
        }}

        if (tempDrawingPoints.length === 0) {{
          tempDrawingPoints.push({{ time: time, price: price }});
          startCreationPoint = {{ x: x, y: y, time: time, price: price }};
          isCreatingDrawing = true;
          liveMousePoint = {{ x: x, y: y, price: price, time: time, rawX: x, rawY: y }};
          scheduleRender();
        }} else {{
          finishCreation([tempDrawingPoints[0], {{ time: time, price: price }}]);
        }}
        return;
      }}

      // Cursor Mode: Handle Hit
      const hitHandle = findHitHandle(x, y);
      if (hitHandle) {{
        selectedDrawingId = hitHandle.drawingId;
        draggingHandle = {{
          drawingId: hitHandle.drawingId,
          type: hitHandle.type,
          handleName: hitHandle.handleName,
          pointIndex: hitHandle.pointIndex,
          startPrice: price,
          startTime: time,
          origPoints: hitHandle.drawing.points.map(p => ({{ ...p }}))
        }};
        canvas.style.pointerEvents = 'auto';
        chart.applyOptions({{ handleScroll: false, handleScale: false }});
        scheduleRender();
        return;
      }}

      // Cursor Mode: Drawing Body Hit
      const hitBody = findHitDrawingBody(x, y);
      if (hitBody) {{
        selectedDrawingId = hitBody.id;
        if (!hitBody.locked) {{
          draggingHandle = {{
            drawingId: hitBody.id,
            type: 'body',
            startPrice: price,
            startTime: time,
            origPoints: hitBody.points.map(p => ({{ ...p }}))
          }};
          canvas.style.pointerEvents = 'auto';
          canvas.style.cursor = 'grabbing';
          chart.applyOptions({{ handleScroll: false, handleScale: false }});
        }}
        scheduleRender();
        return;
      }}

      // Deselect if clicked on empty chart area
      if (selectedDrawingId) {{
        selectedDrawingId = null;
        propToolbar.style.display = 'none';
        scheduleRender();
      }}
    }});

    container.addEventListener('dblclick', (e) => {{
      if (activeTool === 'PATH' && tempDrawingPoints.length >= 2) {{
        finishCreation(tempDrawingPoints);
      }}
    }});

    window.addEventListener('mouseup', (e) => {{
      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      let price = safeCoordinateToPrice(y);
      let time = safeCoordinateToTime(x);

      const isShift = (e.shiftKey || isShiftPressed);
      if (isShift && tempDrawingPoints.length > 0) {{
        const lastAnchor = tempDrawingPoints[tempDrawingPoints.length - 1];
        if (activeTool === 'RECTANGLE') {{
          const rx1 = safeTimeToCoordinate(lastAnchor.time);
          const ry1 = safePriceToCoordinate(lastAnchor.price);
          if (rx1 !== null && ry1 !== null) {{
            const dx = x - rx1;
            const dy = y - ry1;
            const side = Math.max(Math.abs(dx), Math.abs(dy));
            const effX = rx1 + (dx >= 0 ? side : -side);
            const effY = ry1 + (dy >= 0 ? side : -side);
            price = safeCoordinateToPrice(effY);
            time = safeCoordinateToTime(effX);
          }}
        }} else {{
          const snapped = getSnappedPoint(lastAnchor.time, lastAnchor.price, x, y);
          if (snapped.price !== null) price = snapped.price;
          if (snapped.time !== null) time = snapped.time;
        }}
      }}

      // Drag-to-Draw Release Handling for Line Tools
      if (activeTool !== 'CURSOR' && isCreatingDrawing && startCreationPoint) {{
        if (activeTool === 'PATH') return;

        const dist = Math.hypot(x - startCreationPoint.x, y - startCreationPoint.y);
        if (dist > 15 && price !== null && time !== null) {{
          finishCreation([tempDrawingPoints[0], {{ time: time, price: price }}]);
          return;
        }}
        isCreatingDrawing = false;
        return;
      }}

      // Handle Drag Release
      if (draggingHandle) {{
        const targetD = drawings.find(d => d.id === draggingHandle.drawingId);
        if (targetD && window.qtBridge && window.qtBridge.onDrawingUpdated) {{
          window.qtBridge.onDrawingUpdated(JSON.stringify(targetD));
        }}
        draggingHandle = null;
        if (activeTool === 'CURSOR') {{
          canvas.style.pointerEvents = 'none';
          canvas.style.cursor = 'default';
          chart.applyOptions({{ handleScroll: true, handleScale: true }});
        }}
        scheduleRender();
      }}
    }});

    function finishCreation(pts, customText) {{
      const isFib = (activeTool === 'FIBONACCI');
      const isLong = (activeTool === 'LONG_POSITION');
      const isShort = (activeTool === 'SHORT_POSITION');
      const isVP = (activeTool === 'VOLUME_PROFILE');
      const isPath = (activeTool === 'PATH');

      let col = '#2962ff';
      if (isFib) col = '#ff9800';
      if (isLong) col = '#26a69a';
      if (isShort) col = '#ef5350';
      if (isVP) col = '#2962ff';
      if (isPath) col = '#2962ff';

      const newDrawing = {{
        id: 'draw_' + Date.now(),
        type: (activeTool === 'MEASURE') ? 'TRENDLINE' : activeTool,
        symbol: currentSymbol,
        points: pts,
        text: customText || '',
        style: {{
          color: col,
          line_width: (isPath ? 2 : 1.5),
          line_style: 'solid',
          fill_color: isLong ? 'rgba(38, 166, 154, 0.25)' : (isShort ? 'rgba(239, 83, 80, 0.25)' : 'rgba(41, 98, 255, 0.20)'),
          opacity: 0.20,
          font_size: 13
        }},
        metadata: isVP ? {{ num_bins: 30, va_percentage: 0.70, poc_color: '#f23645' }} : {{}},
        visible: true
      }};

      drawings.push(newDrawing);
      tempDrawingPoints = [];
      liveMousePoint = null;
      isCreatingDrawing = false;
      startCreationPoint = null;
      selectedDrawingId = newDrawing.id;
      setActiveTool('CURSOR');
      scheduleRender();

      if (window.qtBridge && window.qtBridge.onDrawingCreated) {{
        window.qtBridge.onDrawingCreated(JSON.stringify(newDrawing));
      }}
    }}

    window.addEventListener('keydown', (e) => {{
      if (e.key === 'Shift') {{
        isShiftPressed = true;
        if (liveMousePoint && tempDrawingPoints.length > 0) {{
          const lastAnchor = tempDrawingPoints[tempDrawingPoints.length - 1];
          const rawX = (liveMousePoint.rawX !== undefined) ? liveMousePoint.rawX : liveMousePoint.x;
          const rawY = (liveMousePoint.rawY !== undefined) ? liveMousePoint.rawY : liveMousePoint.y;
          const snapped = getSnappedPoint(lastAnchor.time, lastAnchor.price, rawX, rawY);
          liveMousePoint.x = snapped.x;
          liveMousePoint.y = snapped.y;
          liveMousePoint.price = (snapped.price !== null) ? snapped.price : liveMousePoint.price;
          liveMousePoint.time = (snapped.time !== null) ? snapped.time : liveMousePoint.time;
        }}
        scheduleRender();
      }}
      if (e.key === 'Enter') {{
        if (activeTool === 'PATH' && tempDrawingPoints.length >= 2) {{
          finishCreation(tempDrawingPoints);
          return;
        }}
      }}
      if (e.key === 'Escape') {{
        if (activeTool === 'PATH' && tempDrawingPoints.length >= 2) {{
          finishCreation(tempDrawingPoints);
          return;
        }} else if (activeTool !== 'CURSOR') {{
          setActiveTool('CURSOR');
          return;
        }}
      }}
      if (e.key === 'Delete' || e.key === 'Backspace') {{
        if (selectedDrawingId) {{
          const idDel = selectedDrawingId;
          drawings = drawings.filter(d => d.id !== idDel);
          selectedDrawingId = null;
          propToolbar.style.display = 'none';
          if (window.qtBridge && window.qtBridge.onDrawingDeleted) {{
            window.qtBridge.onDrawingDeleted(idDel);
          }}
          scheduleRender();
        }}
      }}
    }});

    window.addEventListener('keyup', (e) => {{
      if (e.key === 'Shift') {{
        isShiftPressed = false;
        if (liveMousePoint && liveMousePoint.rawX !== undefined) {{
          liveMousePoint.x = liveMousePoint.rawX;
          liveMousePoint.y = liveMousePoint.rawY;
          liveMousePoint.price = safeCoordinateToPrice(liveMousePoint.rawY);
          liveMousePoint.time = safeCoordinateToTime(liveMousePoint.rawX);
        }}
        scheduleRender();
      }}
    }});
  }}

  window.addEventListener('DOMContentLoaded', initChart);
</script>
</body>
</html>
"""
