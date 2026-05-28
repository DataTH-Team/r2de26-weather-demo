#!/usr/bin/env python3
"""ดึงสภาพอากาศกรุงเทพฯ 7 วัน → raw JSON → Pandas summary → HTML dashboard."""

from __future__ import annotations

import json
import ssl
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import certifi
import pandas as pd

BANGKOK_LAT = 13.7563
BANGKOK_LON = 100.5018
TIMEZONE = "Asia/Bangkok"
API_BASE = "https://api.open-meteo.com/v1/forecast"
DAYS = 7

WEEKDAYS_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]


@dataclass(frozen=True)
class DailyWeather:
    date: str
    temp_max: float
    temp_min: float


def demo_root() -> Path:
    """Resolve demo/ from this script: demo/.cursor/skills/.../scripts/."""
    return Path(__file__).resolve().parents[4]


def fetch_payload(days: int = DAYS) -> dict:
    params = {
        "latitude": BANGKOK_LAT,
        "longitude": BANGKOK_LON,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": TIMEZONE,
        "past_days": days - 1,
        "forecast_days": 1,
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=30, context=ssl_context) as response:
        return json.load(response)


def parse_records(payload: dict) -> list[DailyWeather]:
    daily = payload["daily"]
    return [
        DailyWeather(date=date, temp_max=tmax, temp_min=tmin)
        for date, tmax, tmin in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
        )
    ]


def format_thai_date(iso_date: str) -> str:
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"วัน{WEEKDAYS_TH[dt.weekday()]} {dt.day}/{dt.month}/{dt.year}"


def save_raw(payload: dict, root: Path, ts: str) -> Path:
    raw_path = root / "data" / "raw" / f"bangkok_weather_{ts}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return raw_path


def build_dataframe(records: list[DailyWeather]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "วันที่": r.date,
                "วัน (ไทย)": format_thai_date(r.date),
                "สูงสุด (°C)": round(r.temp_max, 1),
                "ต่ำสุด (°C)": round(r.temp_min, 1),
                "ช่วง (°C)": round(r.temp_max - r.temp_min, 1),
            }
            for r in records
        ]
    )


def weather_icon(temp_max: float) -> str:
    if temp_max >= 36:
        return "🔥"
    if temp_max >= 33:
        return "☀️"
    if temp_max >= 30:
        return "🌤️"
    if temp_max >= 28:
        return "⛅"
    return "🌥️"


def short_day(iso_date: str) -> str:
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return WEEKDAYS_TH[dt.weekday()]


def compute_kpis(records: list[DailyWeather]) -> dict:
    hottest = max(records, key=lambda r: r.temp_max)
    coolest = min(records, key=lambda r: r.temp_min)
    widest = max(records, key=lambda r: r.temp_max - r.temp_min)
    avg_max = sum(r.temp_max for r in records) / len(records)
    avg_min = sum(r.temp_min for r in records) / len(records)
    trend = records[-1].temp_max - records[0].temp_max
    if trend > 0.5:
        trend_label, trend_class = f"อุ่นขึ้น +{trend:.1f}°C", "up"
    elif trend < -0.5:
        trend_label, trend_class = f"เย็นลง {trend:.1f}°C", "down"
    else:
        trend_label, trend_class = "คงที่", "flat"
    return {
        "start_date": records[0].date,
        "end_date": records[-1].date,
        "hottest_day": format_thai_date(hottest.date),
        "hottest_date": hottest.date,
        "hottest_max": hottest.temp_max,
        "hottest_min": hottest.temp_min,
        "coolest_day": format_thai_date(coolest.date),
        "coolest_date": coolest.date,
        "coolest_max": coolest.temp_max,
        "coolest_min": coolest.temp_min,
        "avg_max": avg_max,
        "avg_min": avg_min,
        "max_range": widest.temp_max - widest.temp_min,
        "max_range_day": format_thai_date(widest.date),
        "max_range_date": widest.date,
        "trend_label": trend_label,
        "trend_class": trend_class,
    }


def _daily_cards(records: list[DailyWeather], kpis: dict) -> str:
    cards = []
    global_min = min(r.temp_min for r in records)
    global_max = max(r.temp_max for r in records)
    span = global_max - global_min or 1

    for r in records:
        classes = ["day-card"]
        if r.date == kpis["hottest_date"]:
            classes.append("day-card--hot")
        if r.date == kpis["coolest_date"]:
            classes.append("day-card--cool")
        bar_left = (r.temp_min - global_min) / span * 100
        bar_width = (r.temp_max - r.temp_min) / span * 100
        dt = datetime.strptime(r.date, "%Y-%m-%d")
        cards.append(
            f"""<article class="{' '.join(classes)}">
  <div class="day-card__icon">{weather_icon(r.temp_max)}</div>
  <div class="day-card__day">{short_day(r.date)}</div>
  <div class="day-card__date">{dt.day}/{dt.month}</div>
  <div class="day-card__temps">
    <span class="temp-max">{r.temp_max:.0f}°</span>
    <span class="temp-sep">/</span>
    <span class="temp-min">{r.temp_min:.0f}°</span>
  </div>
  <div class="day-card__bar">
    <div class="day-card__bar-fill" style="left:{bar_left:.1f}%;width:{bar_width:.1f}%"></div>
  </div>
</article>"""
        )
    return "\n".join(cards)


def _svg_chart(records: list[DailyWeather], width: int = 900, height: int = 320) -> str:
    margin = {"top": 32, "right": 24, "bottom": 56, "left": 56}
    inner_w = width - margin["left"] - margin["right"]
    inner_h = height - margin["top"] - margin["bottom"]

    all_temps = [t for r in records for t in (r.temp_min, r.temp_max)]
    y_min = min(all_temps) - 1.5
    y_max = max(all_temps) + 1.5
    y_span = y_max - y_min or 1

    def x_pos(i: int) -> float:
        return margin["left"] + (i / max(len(records) - 1, 1)) * inner_w

    def y_pos(temp: float) -> float:
        return margin["top"] + inner_h - ((temp - y_min) / y_span) * inner_h

    max_pts = []
    min_pts = []
    area_pts = []
    dots = []
    x_labels = []

    for i, r in enumerate(records):
        cx = x_pos(i)
        y_top = y_pos(r.temp_max)
        y_bot = y_pos(r.temp_min)
        max_pts.append(f"{cx:.1f},{y_top:.1f}")
        min_pts.append(f"{cx:.1f},{y_bot:.1f}")
        dots.append(f'<circle cx="{cx:.1f}" cy="{y_top:.1f}" r="5" fill="#ff6b35" stroke="#fff" stroke-width="2"/>')
        dots.append(f'<circle cx="{cx:.1f}" cy="{y_bot:.1f}" r="5" fill="#4dabf7" stroke="#fff" stroke-width="2"/>')
        x_labels.append(
            f'<text x="{cx:.1f}" y="{height - 28}" text-anchor="middle" '
            f'font-size="12" fill="#64748b">{short_day(r.date)}</text>'
        )
        x_labels.append(
            f'<text x="{cx:.1f}" y="{height - 12}" text-anchor="middle" '
            f'font-size="11" fill="#94a3b8">{r.date[5:]}</text>'
        )

    for i in reversed(range(len(records))):
        cx, y_bot = x_pos(i), y_pos(records[i].temp_min)
        area_pts.append(f"{cx:.1f},{y_bot:.1f}")
    for i, r in enumerate(records):
        cx, y_top = x_pos(i), y_pos(r.temp_max)
        area_pts.append(f"{cx:.1f},{y_top:.1f}")

    y_ticks = []
    for tick in range(int(y_min), int(y_max) + 1):
        y = y_pos(tick)
        y_ticks.append(
            f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{width - margin["right"]}" '
            f'y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4"/>'
        )
        y_ticks.append(
            f'<text x="{margin["left"] - 12}" y="{y + 5:.1f}" text-anchor="end" '
            f'font-size="12" fill="#64748b">{tick}°C</text>'
        )

    return f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="กราฟอุณหภูมิรายวัน">
  <defs>
    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ff6b35" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#4dabf7" stop-opacity="0.15"/>
    </linearGradient>
    <linearGradient id="maxLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ff922b"/>
      <stop offset="100%" stop-color="#ff6b35"/>
    </linearGradient>
    <linearGradient id="minLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#74c0fc"/>
      <stop offset="100%" stop-color="#339af0"/>
    </linearGradient>
  </defs>
  <rect x="{margin['left']}" y="{margin['top']}" width="{inner_w}" height="{inner_h}" fill="#f8fafc" rx="8"/>
  {''.join(y_ticks)}
  <polygon points="{' '.join(area_pts)}" fill="url(#areaGrad)"/>
  <polyline points="{' '.join(max_pts)}" fill="none" stroke="url(#maxLine)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="{' '.join(min_pts)}" fill="none" stroke="url(#minLine)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  {''.join(dots)}
  {''.join(x_labels)}
</svg>"""


def render_html(records: list[DailyWeather], kpis: dict, df: pd.DataFrame, fetched_at: str) -> str:
    table_rows = []
    for _, row in df.iterrows():
        row_class = ""
        badge = ""
        if row["วันที่"] == kpis["hottest_date"]:
            row_class = ' class="row-hot"'
            badge = ' <span class="badge badge-hot">ร้อนสุด</span>'
        elif row["วันที่"] == kpis["coolest_date"]:
            row_class = ' class="row-cool"'
            badge = ' <span class="badge badge-cool">เย็นสุด</span>'
        table_rows.append(
            f"<tr{row_class}><td>{row['วันที่']}</td><td>{row['วัน (ไทย)']}{badge}</td>"
            f"<td><strong>{row['สูงสุด (°C)']}</strong></td>"
            f"<td>{row['ต่ำสุด (°C)']}</td>"
            f"<td>{row['ช่วง (°C)']}</td></tr>"
        )

    chart = _svg_chart(records)
    daily_cards = _daily_cards(records, kpis)
    trend_arrow = {"up": "↑", "down": "↓", "flat": "→"}[kpis["trend_class"]]

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>สภาพอากาศกรุงเทพฯ — Dashboard 7 วัน</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    :root {{
      --bg: #0f172a;
      --surface: #ffffff;
      --surface-2: #f1f5f9;
      --text: #0f172a;
      --muted: #64748b;
      --hot: #ff6b35;
      --hot-bg: #fff4ed;
      --cool: #339af0;
      --cool-bg: #e7f5ff;
      --accent: #6366f1;
      --shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
      --radius: 16px;
      font-family: "Sarabun", system-ui, sans-serif;
    }}
    body {{
      margin: 0;
      background: linear-gradient(160deg, #0f172a 0%, #1e3a5f 45%, #f8fafc 45%);
      color: var(--text);
      min-height: 100vh;
    }}
    .page {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    .hero {{
      color: #fff;
      padding: 1rem 0 2.5rem;
    }}
    .hero__eyebrow {{
      display: inline-block;
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 999px;
      padding: 0.35rem 0.9rem;
      font-size: 0.8rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin-bottom: 0.75rem;
    }}
    .hero h1 {{
      margin: 0 0 0.5rem;
      font-size: clamp(1.75rem, 4vw, 2.5rem);
      font-weight: 700;
      line-height: 1.2;
    }}
    .hero__meta {{
      color: rgba(255,255,255,0.75);
      font-size: 0.95rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem 1.25rem;
    }}
    .hero__meta span::before {{ content: "•"; margin-right: 0.5rem; opacity: 0.5; }}
    .hero__meta span:first-child::before {{ content: none; }}

    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .kpi-card {{
      background: var(--surface);
      border-radius: var(--radius);
      padding: 1.25rem 1.35rem;
      box-shadow: var(--shadow);
      border: 1px solid #e2e8f0;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card::after {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 4px;
      background: var(--accent);
    }}
    .kpi-card--hot::after {{ background: linear-gradient(90deg, #ff922b, #ff6b35); }}
    .kpi-card--cool::after {{ background: linear-gradient(90deg, #74c0fc, #339af0); }}
    .kpi-card--avg::after {{ background: linear-gradient(90deg, #a78bfa, #6366f1); }}
    .kpi-card--range::after {{ background: linear-gradient(90deg, #34d399, #10b981); }}
    .kpi-card--trend::after {{ background: linear-gradient(90deg, #fbbf24, #f59e0b); }}
    .kpi-card__label {{
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 500;
      margin-bottom: 0.35rem;
    }}
    .kpi-card__value {{
      font-size: 1.85rem;
      font-weight: 700;
      line-height: 1.1;
      margin-bottom: 0.35rem;
    }}
    .kpi-card__sub {{
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .kpi-card--hot .kpi-card__value {{ color: var(--hot); }}
    .kpi-card--cool .kpi-card__value {{ color: var(--cool); }}
    .trend-up {{ color: #ef4444; }}
    .trend-down {{ color: #3b82f6; }}
    .trend-flat {{ color: #64748b; }}

    .panel {{
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid #e2e8f0;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .panel__header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1.25rem;
    }}
    .panel__title {{
      font-size: 1.1rem;
      font-weight: 700;
      margin: 0;
    }}
    .panel__subtitle {{ font-size: 0.85rem; color: var(--muted); margin: 0; }}
    .legend {{
      display: flex;
      gap: 1.25rem;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .legend__item {{ display: flex; align-items: center; gap: 0.4rem; }}
    .legend__dot {{
      width: 12px; height: 12px; border-radius: 50%;
    }}
    .legend__dot--max {{ background: #ff6b35; }}
    .legend__dot--min {{ background: #339af0; }}

    .daily-grid {{
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 0.75rem;
    }}
    @media (max-width: 900px) {{
      .daily-grid {{ grid-template-columns: repeat(4, 1fr); }}
    }}
    @media (max-width: 560px) {{
      .daily-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    .day-card {{
      background: var(--surface-2);
      border-radius: 12px;
      padding: 1rem 0.75rem;
      text-align: center;
      border: 2px solid transparent;
      transition: transform 0.15s, box-shadow 0.15s;
    }}
    .day-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(15,23,42,0.1);
    }}
    .day-card--hot {{
      background: var(--hot-bg);
      border-color: #ffc9a8;
    }}
    .day-card--cool {{
      background: var(--cool-bg);
      border-color: #a5d8ff;
    }}
    .day-card__icon {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
    .day-card__day {{ font-weight: 600; font-size: 0.95rem; }}
    .day-card__date {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 0.5rem; }}
    .day-card__temps {{ font-size: 1.1rem; font-weight: 700; }}
    .temp-max {{ color: var(--hot); }}
    .temp-min {{ color: var(--cool); font-weight: 500; }}
    .temp-sep {{ color: #cbd5e1; margin: 0 0.1rem; }}
    .day-card__bar {{
      margin-top: 0.65rem;
      height: 6px;
      background: #e2e8f0;
      border-radius: 999px;
      position: relative;
      overflow: hidden;
    }}
    .day-card__bar-fill {{
      position: absolute;
      top: 0; bottom: 0;
      background: linear-gradient(90deg, #339af0, #ff6b35);
      border-radius: 999px;
    }}

    .chart-wrap svg {{ width: 100%; height: auto; display: block; }}

    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}
    thead th {{
      background: var(--surface-2);
      padding: 0.75rem 1rem;
      text-align: left;
      font-weight: 600;
      color: var(--muted);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    tbody td {{
      padding: 0.85rem 1rem;
      border-bottom: 1px solid #e2e8f0;
    }}
    tbody tr:hover {{ background: #f8fafc; }}
    tbody tr:last-child td {{ border-bottom: none; }}
    td:nth-child(n+3), th:nth-child(n+3) {{ text-align: right; }}
    td:nth-child(n+3) {{ font-variant-numeric: tabular-nums; }}
    .row-hot {{ background: var(--hot-bg); }}
    .row-cool {{ background: var(--cool-bg); }}
    .badge {{
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.15rem 0.45rem;
      border-radius: 999px;
      margin-left: 0.35rem;
      vertical-align: middle;
    }}
    .badge-hot {{ background: #ffe8d9; color: #c2410c; }}
    .badge-cool {{ background: #d0ebff; color: #1864ab; }}

    .footer {{
      text-align: center;
      color: var(--muted);
      font-size: 0.8rem;
      padding-top: 0.5rem;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div class="hero__eyebrow">Weather Analytics Dashboard</div>
      <h1>สภาพอากาศกรุงเทพฯ<br/>7 วันล่าสุด</h1>
      <div class="hero__meta">
        <span>📍 Bangkok (13.7563°N, 100.5018°E)</span>
        <span>📅 {kpis['start_date']} – {kpis['end_date']}</span>
        <span>🕐 อัปเดต {fetched_at}</span>
        <span>🔗 Open-Meteo · Asia/Bangkok</span>
      </div>
    </header>

    <section class="kpi-grid">
      <div class="kpi-card kpi-card--hot">
        <div class="kpi-card__label">🔥 วันร้อนที่สุด</div>
        <div class="kpi-card__value">{kpis['hottest_max']:.1f}°C</div>
        <div class="kpi-card__sub">{kpis['hottest_day']}</div>
      </div>
      <div class="kpi-card kpi-card--cool">
        <div class="kpi-card__label">❄️ วันเย็นที่สุด</div>
        <div class="kpi-card__value">{kpis['coolest_min']:.1f}°C</div>
        <div class="kpi-card__sub">{kpis['coolest_day']}</div>
      </div>
      <div class="kpi-card kpi-card--avg">
        <div class="kpi-card__label">📊 อุณหภูมิเฉลี่ย</div>
        <div class="kpi-card__value">{kpis['avg_max']:.1f}° / {kpis['avg_min']:.1f}°</div>
        <div class="kpi-card__sub">สูงสุด / ต่ำสุด</div>
      </div>
      <div class="kpi-card kpi-card--range">
        <div class="kpi-card__label">📏 ช่วงอุณหภูมิสูงสุด</div>
        <div class="kpi-card__value">{kpis['max_range']:.1f}°C</div>
        <div class="kpi-card__sub">{kpis['max_range_day']}</div>
      </div>
      <div class="kpi-card kpi-card--trend">
        <div class="kpi-card__label">📈 แนวโน้ม 7 วัน</div>
        <div class="kpi-card__value trend-{kpis['trend_class']}">{trend_arrow} {kpis['trend_label']}</div>
        <div class="kpi-card__sub">เทียบวันแรก vs วันสุดท้าย</div>
      </div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">พยากรณ์รายวัน</h2>
          <p class="panel__subtitle">อุณหภูมิสูงสุด / ต่ำสุด แต่ละวัน</p>
        </div>
      </div>
      <div class="daily-grid">
        {daily_cards}
      </div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">กราฟแนวโน้มอุณหภูมิ</h2>
          <p class="panel__subtitle">ช่วง max–min รายวัน (°C)</p>
        </div>
        <div class="legend">
          <span class="legend__item"><span class="legend__dot legend__dot--max"></span> สูงสุด</span>
          <span class="legend__item"><span class="legend__dot legend__dot--min"></span> ต่ำสุด</span>
        </div>
      </div>
      <div class="chart-wrap">{chart}</div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">ตารางข้อมูลรายละเอียด</h2>
          <p class="panel__subtitle">ข้อมูลดิบ 7 วัน — พร้อม export / วิเคราะห์ต่อ</p>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>วันที่</th><th>วัน</th>
              <th>สูงสุด (°C)</th><th>ต่ำสุด (°C)</th><th>ช่วง (°C)</th>
            </tr>
          </thead>
          <tbody>
            {''.join(table_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <p class="footer">Generated by bangkok-weather-dashboard · Data source: Open-Meteo API</p>
  </div>
</body>
</html>"""


def save_dashboard(html: str, root: Path, ts: str) -> Path:
    out_path = root / "output" / f"bangkok_weather_dashboard_{ts}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> int:
    root = demo_root()
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    payload = fetch_payload()
    records = parse_records(payload)
    raw_path = save_raw(payload, root, ts)

    df = build_dataframe(records)
    kpis = compute_kpis(records)
    html = render_html(records, kpis, df, fetched_at)
    dash_path = save_dashboard(html, root, ts)

    print("=== สภาพอากาศกรุงเทพฯ — 7 วันล่าสุด ===\n")
    print(df[["วันที่", "วัน (ไทย)", "สูงสุด (°C)", "ต่ำสุด (°C)", "ช่วง (°C)"]].to_string(index=False))
    print()
    print(f"วันร้อนที่สุด: {kpis['hottest_day']} (สูงสุด {kpis['hottest_max']:.1f}°C)")
    print(f"วันเย็นที่สุด: {kpis['coolest_day']} (ต่ำสุด {kpis['coolest_min']:.1f}°C)")
    print(f"อุณหภูมิสูงสุดเฉลี่ย: {kpis['avg_max']:.1f}°C")
    print(f"อุณหภูมิต่ำสุดเฉลี่ย: {kpis['avg_min']:.1f}°C")
    print()
    print(f"Raw:       {raw_path.relative_to(root)}")
    print(f"Dashboard: {dash_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
