import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.env import SESSION_ID


def get_budget() -> int:
    """Fetch current account balance from Pokemon Vortex pokemart."""
    url: str = "https://www.pokemon-vortex.com/pokemart/"
    headers: dict[str, str] = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "dnt": "1",
        "priority": "u=0, i",
        "referer": "https://www.pokemon-vortex.com/profile/",
        "sec-ch-ua": '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "Cookie": f"SESS={SESSION_ID}",
    }

    response: requests.Response = requests.get(url, headers=headers, timeout=30)
    soup: BeautifulSoup = BeautifulSoup(response.text, "lxml")

    cash_element: Tag | None = soup.find("div", id="yourCash")
    if not cash_element:
        raise ValueError("Could not find cash element on page")

    budget: int = int(cash_element.text.strip().split("$")[1].replace(",", ""))
    return budget
