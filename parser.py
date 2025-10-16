import httpx
from bs4 import BeautifulSoup
import re

async def get_journal_with_cookie(cookie: str) -> str | None:
    """Загружает страницу журнала с сайта college.snation.kz"""
    try:
        # Ищем XSRF токен внутри cookie
        match = re.search(r"XSRF-TOKEN=([^;]+)", cookie)
        xsrf_token = match.group(1) if match else None

        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Referer": "https://college.snation.kz/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        if xsrf_token:
            headers["X-XSRF-TOKEN"] = xsrf_token

        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            url = "https://college.snation.kz/kz/tko/control/journals"
            resp = await client.get(url, headers=headers)

            # Если редирект на логин — cookie неверна
            if "login" in str(resp.url):
                return None

            if resp.status_code == 200:
                return resp.text
            else:
                print("Ошибка запроса:", resp.status_code, resp.text[:200])
                return None

    except Exception as e:
        print("Ошибка при загрузке журнала:", e)
        return None


def extract_grades_from_html(html: str) -> str:
    """Извлекает оценки из HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # Ищем таблицу оценок
    grades = []
    for cell in soup.select("td.sc-journal__table--cell-value"):
        text = cell.get_text(strip=True)
        if text.isdigit():
            grades.append(text)

    if not grades:
        return "⚠️ Не удалось найти оценки в журнале."

    avg = round(sum(map(int, grades)) / len(grades), 2)
    result = "📊 *Оценки:*\n" + ", ".join(grades) + f"\n\nСредний балл: *{avg}*"
    return result


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
