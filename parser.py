import httpx
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://college.snation.kz"
JOURNAL_LIST_URL = f"{BASE_URL}/kz/tko/control/journals"

async def get_journal_with_cookie(cookie: str):
    """
    Получает HTML всех журналов для пользователя по cookie.
    Возвращает готовую строку с предметами и оценками.
    """
    now = datetime.now()
    headers = {
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": JOURNAL_LIST_URL,
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        # 1️⃣ Загружаем список предметов
        resp = await client.get(JOURNAL_LIST_URL, headers=headers)
        if resp.status_code != 200:
            return f"⚠️ Ошибка при загрузке списка предметов ({resp.status_code})"

        soup = BeautifulSoup(resp.text, "html.parser")

        subject_links = []
        for a in soup.find_all("a", href=True):
            if "/kz/tko/control/journals/" in a["href"]:
                name = a.get_text(strip=True)
                journal_id = a["href"].split("/")[-1]
                if journal_id.isdigit():
                    subject_links.append((name, journal_id))

        if not subject_links:
            return "⚠️ Не удалось найти журналы. Проверь cookie."

        results = [f"📘 *Оценки за {now.month:02d}/{now.year}:*"]

        # 2️⃣ Для каждого предмета парсим таблицу
        for subject, journal_id in subject_links:
            load_url = f"{JOURNAL_LIST_URL}/{journal_id}/load-table"
            params = {"year_month": f"{now.month:02d}/{now.year}"}

            headers.update({
                "Accept": "text/html, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{JOURNAL_LIST_URL}/{journal_id}",
            })

            try:
                r = await client.get(load_url, headers=headers, params=params)
                if r.status_code != 200:
                    results.append(f"{subject}: ⚠️ Ошибка {r.status_code}")
                    continue

                grades = extract_grades_from_html(r.text)
                if grades:
                    avg = round(sum(map(int, grades)) / len(grades), 1)
                    results.append(f"📚 *{subject}*: {', '.join(grades)} (ср. {avg})")
                else:
                    results.append(f"📚 *{subject}*: ⚠️ Оценок не найдено")

            except Exception as e:
                results.append(f"{subject}: ⚠️ Ошибка ({e})")

        return "\n".join(results)

def extract_grades_from_html(html: str):
    """
    Извлекает оценки из HTML по div.sc-journal__table--cell-value
    """
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", class_="sc-journal__table--cell-value")
    grades = [div.get_text(strip=True) for div in divs if div.get_text(strip=True).isdigit()]
    return grades
