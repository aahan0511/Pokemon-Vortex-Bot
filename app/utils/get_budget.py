import logging

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.env import SESSION_ID

logger = logging.getLogger(__name__)

# Constants
POKEMART_URL = "https://www.pokemon-vortex.com/pokemart/"
REQUEST_TIMEOUT = 30


def get_budget() -> int:
    """
    Fetch current account balance from Pokemon Vortex pokemart.
    
    Returns:
        Current account balance in dollars
        
    Raises:
        ValueError: If cash element cannot be found or parsed
        requests.RequestException: If the HTTP request fails
    """
    logger.info("Fetching current account budget from pokemart")
    
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

    try:
        response: requests.Response = requests.get(
            POKEMART_URL, 
            headers=headers, 
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.debug(f"Successfully fetched pokemart page (status: {response.status_code})")
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch pokemart page: {e}")
        raise

    # Parse HTML
    soup: BeautifulSoup = BeautifulSoup(response.text, "lxml")
    cash_element: Tag | None = soup.find("div", id="yourCash")
    
    if not cash_element:
        logger.error("Could not find cash element with id 'yourCash' on page")
        raise ValueError("Could not find cash element on page")

    # Extract and parse budget value
    cash_text = cash_element.text.strip()
    logger.debug(f"Raw cash text: '{cash_text}'")
    
    try:
        # Expected format: "Your Cash: $1,234,567"
        if "$" not in cash_text:
            raise ValueError(f"Unexpected cash format (no $ symbol): '{cash_text}'")
            
        budget_str = cash_text.split("$")[1].replace(",", "")
        budget: int = int(budget_str)
        
        logger.info(f"Current account budget: ${budget:,}")
        return budget
        
    except (IndexError, ValueError) as e:
        logger.error(f"Failed to parse budget from text '{cash_text}': {e}")
        raise ValueError(f"Could not parse budget from: '{cash_text}'") from e