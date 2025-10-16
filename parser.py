import httpx
from bs4 import BeautifulSoup

async def get_journal_with_cookie(cookie: str) -> str | None:
    url = "https://college.snation.kz/kz/tko/control/journals"
    headers = {"Cookie": cookie, "User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        if "Журнал" in response.text or "journal" in response.text:
            return response.text
    return None

def extract_grades_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    grades = []

    for row in soup.select("tr"):
        cols = [col.get_text(strip=True) for col in row.find_all("td")]
        if len(cols) >= 3 and cols[-1].isdigit():
            grades.append(f"• {cols[0]} — {cols[-1]} баллов")

    if not grades:
        return "📭 Оценки не найдены."
    return "\n".join(grades)
