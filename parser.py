import httpx
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://college.snation.kz"
JOURNAL_LIST_URL = f"{BASE_URL}/kz/tko/control/journals"
LOAD_URL_TEMPLATE = JOURNAL_LIST_URL + "/{journal_id}/load-table?year_month={month}%2F{year}"


async def get_journal_with_cookie(cookie: str):
    """Парсит оценки напрямую из HTML таблицы журнала"""
    now = datetime.now()
    headers = {
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": JOURNAL_LIST_URL,
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        # 1️⃣ Загружаем список предметов
        resp = await client.get(JOURNAL_LIST_URL, headers=headers)
        if resp.status_code != 200:
            return f"⚠️ Ошибка при загрузке предметов: {resp.status_code}"

        # 2️⃣ Ищем ссылки на предметы
        soup = BeautifulSoup(resp.text, "html.parser")
        subject_links = []
        for a in soup.find_all("a", href=True):
            if "/kz/tko/control/journals/" in a["href"]:
                subject_name = a.get_text(strip=True)
                journal_id = a["href"].split("/")[-1]
                if journal_id.isdigit():
                    subject_links.append((subject_name, journal_id))

        if not subject_links:
            return "⚠️ Не удалось найти предметы. Проверь cookie."

        # 3️⃣ Собираем оценки с каждой страницы
        all_results = [f"📘 *Оценки за {now.month:02d}/{now.year}:*"]
        for subject, journal_id in subject_links:
            load_url = LOAD_URL_TEMPLATE.format(journal_id=journal_id, month=now.month, year=now.year)
            try:
                r = await client.get(load_url, headers=headers)
                if r.status_code != 200:
                    all_results.append(f"{subject}: ⚠️ Ошибка {r.status_code}")
                    continue

                grades = extract_grades_from_html(r.text)
                if grades:
                    all_results.append(f"{subject}: {grades}")
                else:
                    all_results.append(f"{subject}: ⚠️ Оценок нет")

            except Exception as e:
                all_results.append(f"{subject}: ⚠️ Ошибка ({e})")

        return "\n".join(all_results)


def extract_grades_from_html(html: str) -> str:
    """Извлекает оценки из HTML (div.sc-journal__table--cell-value)"""
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", class_="sc-journal__table--cell-value")
    grades = [div.get_text(strip=True) for div in divs if div.get_text(strip=True).isdigit()]
    return ", ".join(grades) if grades else ""
