import re

from bs4 import BeautifulSoup, Tag

from app.env import logger


def extract_auction_ids(soup: BeautifulSoup) -> list[str | None]:
    """Extract auction IDs from the auction table."""
    auction_ids: list[str | None] = []
    table: Tag | None = soup.find("table", class_="table-striped")

    if not table:
        logger.warning("Table not found")
        return auction_ids

    rows: list[Tag] = table.find_all("tr")[1:]  # Skip header row

    for tr in rows:
        cells: list[Tag] = tr.find_all("td")
        if cells and len(cells) > 1:
            auction_link: Tag | None = cells[1].find("a")
            if auction_link:
                onclick: str = auction_link.get("onclick", "")
                match: re.Match[str] | None = re.search(
                    r"/pokebay/auction/(\d+)/",
                    onclick,
                )
                auction_ids.append(match.group(1) if match else None)
            else:
                auction_ids.append(None)

    return auction_ids
