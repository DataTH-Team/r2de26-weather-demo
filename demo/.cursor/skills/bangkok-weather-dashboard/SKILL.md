---
name: bangkok-weather-dashboard
description: >-
  ดึงสภาพอากาศกรุงเทพฯ 7 วันล่าสุดจาก Open-Meteo บันทึก raw JSON
  แล้วสร้าง Dashboard สรุป KPI ภาษาไทย (HTML + ตาราง Pandas).
  Use when the user asks for Bangkok weather, 7-day forecast/history,
  weather dashboard, KPI summary, or invokes /bangkok-weather-dashboard.
---

# Bangkok Weather Dashboard

Runbook สำหรับนักวิเคราะห์สภาพอากาศ — ดึงข้อมูล 7 วัน สร้าง Dashboard สรุป KPI

## Prerequisites

```bash
cd demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Workflow

```
Task Progress:
- [ ] Step 1: รัน pipeline script
- [ ] Step 2: ตรวจ raw JSON ใน data/raw/
- [ ] Step 3: เปิด Dashboard HTML ใน output/
- [ ] Step 4: สรุป KPI ให้ผู้ใช้เป็นภาษาไทย
```

### Step 1 — รัน pipeline

จากโฟลเดอร์ `demo/`:

```bash
python .cursor/skills/bangkok-weather-dashboard/scripts/run_dashboard.py
```

Script จะ:
1. เรียก Open-Meteo API (Bangkok 13.7563, 100.5018, timezone Asia/Bangkok)
2. บันทึก response ดิบ → `data/raw/bangkok_weather_{timestamp}.json` (append-only)
3. แสดงตาราง Pandas ภาษาไทยใน terminal
4. สร้าง Dashboard HTML → `output/bangkok_weather_dashboard_{timestamp}.html`

### Step 2 — ตรวจ raw layer

- ยืนยันว่ามีไฟล์ JSON ใหม่ใน `data/raw/`
- **ห้ามลบ** ไฟล์ใน `data/raw/` — เป็น audit trail

### Step 3 — เปิด Dashboard

บอกผู้ใช้ path ของไฟล์ HTML ล่าสุดใน `output/` ให้เปิดใน browser

### Step 4 — สรุป KPI (ภาษาไทย)

ใช้ template นี้:

```markdown
## สรุปสภาพอากาศกรุงเทพฯ — 7 วันล่าสุด

**ช่วงวันที่:** {start_date} – {end_date}
**แหล่งข้อมูล:** Open-Meteo (Asia/Bangkok)

| KPI | ค่า |
|-----|-----|
| วันร้อนที่สุด | {hottest_day} — สูงสุด {max}°C |
| วันเย็นที่สุด | {coolest_day} — ต่ำสุด {min}°C |
| อุณหภูมิสูงสุดเฉลี่ย | {avg_max}°C |
| อุณหภูมิต่ำสุดเฉลี่ย | {avg_min}°C |
| ช่วงอุณหภูมิ (max−min) สูงสุด | {max_range}°C วันที่ {max_range_day} |

**Dashboard:** `output/bangkok_weather_dashboard_{timestamp}.html`
**Raw data:** `data/raw/bangkok_weather_{timestamp}.json`
```

## Guardrails (จาก de-pipeline rules)

- Raw JSON → `data/raw/` เท่านั้น
- Append-only — ไม่ลบ/overwrite raw
- ตารางสรุปใช้ Pandas DataFrame (ไม่ print loop manual)
- อุณหภูมิทศนิยม 1 ตำแหน่ง

## API reference

```
https://api.open-meteo.com/v1/forecast
  ?latitude=13.7563&longitude=100.5018
  &daily=temperature_2m_max,temperature_2m_min
  &timezone=Asia/Bangkok
  &past_days=6&forecast_days=1
```

## Troubleshooting

| ปัญหา | แก้ไข |
|-------|-------|
| SSL error | ติดตั้ง `certifi` แล้วรันใหม่ |
| ModuleNotFoundError: pandas | `pip install -r requirements.txt` |
| ไม่มีโฟลเดอร์ output | script สร้างให้อัตโนมัติ |
