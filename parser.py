import httpx
from bs4 import BeautifulSoup

async def get_journal_with_cookie(cookie: str) -> str:
    """
    Загружает страницу журнала по cookie пользователя.
    """
    url = "https://college.snation.kz/kz/tko/control/journals/873751/load-table?year_month=10%2F2025"
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                return response.text
            else:
                print(f"⚠️ Ошибка HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке: {e}")
    return None


def extract_grades_from_html(html: str) -> str:
    """
    Извлекает оценки (points) из HTML журнала Snation College.
    Работает с таблицей, где каждая строка — предмет, а ячейки — оценки.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Находим таблицу журнала (ищем все строки tr)
    rows = soup.find_all("tr")
    if not rows:
        return "⚠️ Таблица с оценками не найдена."

    result = []
    for row in rows:
        # Предмет — обычно в первом <td> с классом 'discipline_name' или просто первый
        subject_cell = row.find("td", class_="discipline_name") or row.find("td")
        if not subject_cell:
            continue

        subject_name = subject_cell.get_text(strip=True)
        if not subject_name:
            continue

        # Ищем оценки — могут быть в <td data-points="X"> или внутри <div class="points">
        points_cells = row.find_all(lambda tag: tag.name == "td" and ("points" in tag.get("class", []) or tag.get("data-points")))
        points = []

        for cell in points_cells:
            # Извлекаем атрибут или текст
            val = cell.get("data-points") or cell.get_text(strip=True)
            if val and val.isdigit():
                points.append(val)

        # Альтернативный вариант (на случай, если оценки в <div> внутри)
        if not points:
            for div in row.find_all("div", class_="points"):
                text = div.get_text(strip=True)
                if text:
                    points.append(text)

        if points:
            result.append(f"📘 *{subject_name}*: {', '.join(points)}")

    if not result:
        return "⚠️ Не удалось извлечь оценки. Возможно, структура сайта изменилась."

    return "\n".join(result)
