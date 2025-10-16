import httpx
from bs4 import BeautifulSoup

# Правильный адрес журнала
JOURNAL_URL = "https://college.snation.kz/kz/tko/control/journals"

async def get_journal_with_cookie(cookie: str):
    headers = {
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://college.snation.kz/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        response = await client.get(JOURNAL_URL, headers=headers)

        # Проверяем, реально ли открылась страница журнала
        if response.status_code == 200 and (
            "Журнал" in response.text or "баға" in response.text.lower()
        ):
            return response.text
        else:
            print(f"[DEBUG] Status: {response.status_code}")
            return None


def extract_grades_from_html(html: str) -> str:
    """Парсинг таблицы с оценками"""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return "⚠️ Не удалось найти таблицу с оценками."

    rows = table.find_all("tr")
    result = ["📘 *Твои оценки:*"]
    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) >= 2:
            subject = cols[0]
            grade = cols[-1]
            result.append(f"{subject} — {grade}")

    return "\n".join(result)
