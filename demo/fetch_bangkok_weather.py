#!/usr/bin/env python3
"""ดึงอุณหภูมิสูงสุด/ต่ำสุด 7 วันล่าสุดของ Bangkok จาก Open-Meteo API (ฟรี ไม่ต้องใช้ API key)."""

from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request

import certifi
from dataclasses import dataclass
from datetime import datetime

BANGKOK_LAT = 13.7563
BANGKOK_LON = 100.5018
TIMEZONE = "Asia/Bangkok"
API_BASE = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class DailyWeather:
    date: str
    temp_max: float
    temp_min: float


def fetch_bangkok_weather(days: int = 7) -> list[DailyWeather]:
    """ดึงข้อมูลอุณหภูมิรายวัน — 7 วัน = past_days=6 + forecast_days=1."""
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
        payload = json.load(response)

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
    """แปลง YYYY-MM-DD เป็นชื่อวันภาษาไทย."""
    weekdays = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"วัน{weekdays[dt.weekday()]} {dt.day}/{dt.month}/{dt.year}"


def main() -> None:
    records = fetch_bangkok_weather()

    print("อุณหภูมิ Bangkok — 7 วันล่าสุด (Open-Meteo, timezone Asia/Bangkok)\n")
    print(f"{'วันที่':<12} {'สูงสุด (°C)':>12} {'ต่ำสุด (°C)':>12}")
    print("-" * 38)

    for row in records:
        print(f"{row.date:<12} {row.temp_max:>12.1f} {row.temp_min:>12.1f}")

    hottest = max(records, key=lambda r: r.temp_max)
    print()
    print(
        f"วันร้อนที่สุด: {format_thai_date(hottest.date)} "
        f"(อุณหภูมิสูงสุด {hottest.temp_max:.1f}°C, ต่ำสุด {hottest.temp_min:.1f}°C)"
    )


if __name__ == "__main__":
    main()
