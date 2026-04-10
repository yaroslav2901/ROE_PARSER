#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Парсер для Рівнеобленерго (ROE) — версія 1 (UA)

import asyncio
import re
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
import os
from typing import Optional, Dict
from bs4 import BeautifulSoup

TZ = ZoneInfo("Europe/Kyiv")
URL = "https://www.roe.vsei.ua/disconnections"
OUTPUT_FILE = "out/Rivneoblenergo.json"

LOG_DIR = "logs"
FULL_LOG_FILE = os.path.join(LOG_DIR, "full_log.log")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs("out", exist_ok=True)


def log(message: str) -> None:
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} [roe_parser] {message}"
    print(line)
    with open(FULL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


async def fetch_html() -> str:
    """Отримує HTML сторінки ROE."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()
        try:
            log(f"🌐 Відкриваю сторінку {URL}")
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("table", timeout=30000)

            await asyncio.sleep(2)

            html = await page.content()
            log(f"✅ HTML завантажено ({len(html)} байт)")
            return html
        finally:
            await browser.close()


def parse_time_ranges(time_str: str) -> list:
    """
    Парсить рядок з часовими діапазонами типу:
    '04:00 - 08:00  11:00 - 14:00  17:00 - 20:00'
    або '00:00 - 04:00  10:00 - 13:00  16:00 - 18:00  23:00 - 23:59'
    
    Повертає список кортежів (start_hour, end_hour)
    """
    ranges = []
    # Знаходимо всі діапазони формату HH:MM - HH:MM
    pattern = r'(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})'
    matches = re.findall(pattern, time_str)
    
    for match in matches:
        start_h, start_m, end_h, end_m = map(int, match)
        
        # Якщо 23:59, то це фактично 24:00 (кінець дня)
        if end_h == 23 and end_m == 59:
            end_h = 24
        
        ranges.append((start_h, end_h))
    
    return ranges


def create_hourly_schedule(time_ranges: list) -> Dict[str, str]:
    """
    Створює погодинний розклад на основі часових діапазонів.
    За замовчуванням всі години - "yes", відключені - "no"
    
    Година в JSON:
    "1" = 00:00-01:00
    "2" = 01:00-02:00
    ...
    "24" = 23:00-00:00
    """
    schedule = {str(h): "yes" for h in range(1, 25)}
    
    for start_h, end_h in time_ranges:
        # start_h та end_h - це години у форматі 0-23
        # Потрібно конвертувати в формат 1-24
        
        # Діапазон 00:00-04:00 означає години 1,2,3,4
        # Діапазон 10:00-13:00 означає години 11,12,13
        # Діапазон 23:00-23:59 означає годину 24
        
        if start_h == end_h:
            continue
        
        if start_h < end_h:
            # Звичайний діапазон у межах одного дня
            for h in range(start_h, end_h):
                hour_key = str(h + 1)
                schedule[hour_key] = "no"
        else:
            # Діапазон через північ (наприклад 23:00-02:00)
            for h in range(start_h, 24):
                hour_key = str(h + 1)
                schedule[hour_key] = "no"
            for h in range(0, end_h):
                hour_key = str(h + 1)
                schedule[hour_key] = "no"
    
    return schedule


def parse_schedule(html: str):
    """Парсинг графіка відключень з таблиці."""
    results: Dict[str, Dict] = {}
    soup = BeautifulSoup(html, 'html.parser')
    
    # Визначаємо вчорашню дату
    today = datetime.now(TZ).date()
    yesterday = today - timedelta(days=1)
    log(f"📆 Сьогодні: {today.strftime('%d.%m.%Y')}, Вчора: {yesterday.strftime('%d.%m.%Y')}")
    
    # Шукаємо час оновлення
    update_info = None
    update_text = soup.find(text=re.compile(r'Оновлено:'))
    if update_text:
        update_match = re.search(r'(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})', update_text.parent.get_text())
        if update_match:
            update_info = update_match.group(1)
            log(f"🕒 Знайдено час оновлення: {update_info}")
    
    if not update_info:
        update_info = datetime.now(TZ).strftime("%d.%m.%Y %H:%M")
        log(f"⚠️ Час оновлення не знайдено, використовую поточний: {update_info}")
    
    # Знаходимо таблицю з графіком
    table = soup.find('table')
    if not table:
        log("❌ Таблицю не знайдено")
        return results, update_info
    
    rows = table.find_all('tr')
    if len(rows) < 2:
        log("❌ Недостатньо рядків у таблиці")
        return results, update_info
    
    # Перший рядок з датами та підчергами
    header_rows = [r for r in rows if r.find_all('td') and any('Підчерга' in cell.get_text() for cell in r.find_all('td'))]
    
    # Шукаємо рядки з даними (дати)
    data_rows = []
    for row in rows:
        cells = row.find_all('td')
        if cells:
            first_cell = cells[0].get_text(strip=True)
            # Перевіряємо чи це дата формату DD.MM.YYYY
            if re.match(r'\d{2}\.\d{2}\.\d{4}', first_cell):
                # Перевіряємо чи це вчорашня дата
                try:
                    day, month, year = map(int, first_cell.split('.'))
                    date_obj = datetime(year, month, day, tzinfo=TZ).date()
                    
                    if date_obj < today:
                        log(f"⏭️ Пропускаю дату {first_cell} — це минула дата")
                        continue
                except ValueError:
                    log(f"⚠️ Помилка парсингу дати: {first_cell}")
                    continue
                
                # Перевіряємо чи немає статусу "Очікується"
                row_text = row.get_text()
                if 'Очікується' in row_text or 'очікується' in row_text.lower():
                    log(f"⏭️ Пропускаю дату {first_cell} — статус 'Очікується'")
                    continue
                data_rows.append((first_cell, cells))
    
    if not data_rows:
        log("⚠️ Не знайдено рядків з датами")
        return results, update_info
    
    # Парсимо кожен рядок з датою
    for date_str, cells in data_rows:
        log(f"📅 Обробляю дату: {date_str}")
        
        # Конвертуємо дату в timestamp
        try:
            day, month, year = map(int, date_str.split('.'))
            date_obj = datetime(year, month, day, tzinfo=TZ)
            ts = int(date_obj.timestamp())
        except ValueError:
            log(f"⚠️ Помилка парсингу дати: {date_str}")
            continue
        
        results[str(ts)] = {}
        
        # Обробляємо кожну підчергу (стовпці після дати)
        subqueue_num = 1
        for i, cell in enumerate(cells[1:], start=1):
            time_str = cell.get_text(strip=True)
            #if not time_str or time_str == '':
            #    continue    
            # Визначаємо номер черги і підчерги
            queue_num = ((i - 1) // 2) + 1
            sub_num = ((i - 1) % 2) + 1
            group_id = f"GPV{queue_num}.{sub_num}"
            
            # Парсимо часові діапазони
            time_ranges = parse_time_ranges(time_str)
            
            if time_ranges:
                schedule = create_hourly_schedule(time_ranges)
                results[str(ts)][group_id] = schedule
                log(f"✔️ {group_id} — знайдено {len(time_ranges)} діапазонів відключень")
            else:
                # Якщо немає відключень - весь день світло
                results[str(ts)][group_id] = {str(h): "yes" for h in range(1, 25)}
                log(f"✔️ {group_id} — без відключень")        
        
    return results, update_info


async def main() -> bool:
    log("=" * 60)
    log("🚀 Запуск парсера Рівнеобленерго")
    log("=" * 60)

    try:
        html = await fetch_html()
        results, update_info = parse_schedule(html)

        if not results:
            log("❌ Не вдалося розпарсити жодного графіка — завершую роботу")
            return False

        # DIFF — чи змінились дані?
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            old_data = old.get("fact", {}).get("data", {})

            if json.dumps(old_data, sort_keys=True) == json.dumps(results, sort_keys=True):
                log("ℹ️ Дані не змінилися — пропускаю запис у JSON")
                return False

        # Сортуємо дати
        sorted_results = dict(sorted(results.items(), key=lambda x: int(x[0])))

        # today timestamp
        today = datetime.now(TZ).date()
        today_ts = int(datetime(today.year, today.month, today.day, tzinfo=TZ).timestamp())

        # Формуємо фінальний JSON
        new_json = {
            "regionId": "Rivne",
            "lastUpdated": datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "fact": {
                "data": sorted_results,
                "update": update_info,
                "today": today_ts,
            },
            "preset": {
                "time_zone": {
                    str(i): [
                        f"{i - 1:02d}-{i:02d}",
                        f"{i - 1:02d}:00",
                        f"{i:02d}:00",
                    ]
                    for i in range(1, 25)
                },
                "time_type": {
                    "yes": "Світло є",
                    "maybe": "Можливе відключення",
                    "no": "Світла немає",
                    "first": "Світла не буде перші 30 хв.",
                    "second": "Світла не буде другі 30 хв.",
                },
            },
        }

        log(f"💾 Записую JSON у файл → {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(new_json, f, ensure_ascii=False, indent=2)

        log("✅ JSON успішно оновлено")
        log("=" * 60)
        return True

    except Exception as e:
        log(f"❌ Помилка: {e}")
        import traceback
        log(traceback.format_exc())
        return False


if __name__ == "__main__":
    asyncio.run(main())