import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://college.snation.kz"
JOURNAL_LIST_URL = f"{BASE_URL}/kz/tko/control/journals"


async def get_journal_with_cookie(cookie: str):
    """Парсит список всех журналов и оценки по каждому предмету"""
    headers = {
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": BASE_URL,
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        # 1️⃣ Загружаем список предметов
        list_resp = await client.get(JOURNAL_LIST_URL, headers=headers)
        if list_resp.status_code != 200:
            print(f"[DEBUG] Ошибка при загрузке списка журналов: {list_resp.status_code}")
            return None

        soup = BeautifulSoup(list_resp.text, "html.parser")
        subject_links = []

        # Ищем все ссылки на отдельные журналы
        for a in soup.find_all("a", href=True):
            if "/kz/tko/control/journal/" in a["href"]:
                subject_name = a.get_text(strip=True)
                subject_links.append((subject_name, BASE_URL + a["href"]))

        if not subject_links:
            return "⚠️ Не найдено ни одного предмета. Возможно, cookie недействительна."

        # 2️⃣ Обходим все журналы и собираем оценки
        all_grades = ["📘 *Твои журналы:*"]
        for subject, link in subject_links:
            try:
                resp = await client.get(link, headers=headers)
                if resp.status_code != 200:
                    all_grades.append(f"{subject} — ⚠️ ошибка ({resp.status_code})")
                    continue

                grades = extract_grades_from_html(resp.text)
                if grades:
                    all_grades.append(f"{subject}: {grades}")
                else:
                    all_grades.append(f"{subject}: ⚠️ оценки не найдены")

            except Exception as e:
                all_grades.append(f"{subject}: ⚠️ ошибка запроса ({e})")

        return "\n".join(all_grades)


def extract_grades_from_html(html: str) -> str:
    """Извлекает оценки из страницы отдельного предмета"""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return ""

    rows = table.find_all("tr")
    grades = []

    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) >= 2:
            grade = cols[-1]
            if grade.isdigit() or grade in ["5", "4", "3", "2"]:
                grades.append(grade)

    return ", ".join(grades) if grades else ""
