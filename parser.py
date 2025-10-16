import httpx
from bs4 import BeautifulSoup

JOURNAL_URL = "https://college.snation.kz/student/journal"

async def get_journal_with_cookie(cookie: str):
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(JOURNAL_URL, headers=headers)
        if response.status_code == 200 and "Журнал" in response.text:
            return response.text
        return None

def extract_grades_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return "⚠️ Не удалось найти таблицу оценок."

    rows = table.find_all("tr")
    result = ["📘 *Твои оценки:*"]
    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) >= 2:
            result.append(f"{cols[0]} — {cols[1]}")
    return "\n".join(result)
