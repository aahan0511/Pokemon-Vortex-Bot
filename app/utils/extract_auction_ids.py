import logging
import re

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


def extract_auction_ids(soup: BeautifulSoup) -> list[str | None]:
    """
    Extract auction IDs from the auction table.

    Args:
        soup: BeautifulSoup object containing the page HTML

    Returns:
        List of auction IDs (or None for rows without valid IDs)
    """
    auction_ids: list[str | None] = []

    # Find the auction table
    table: Tag | None = soup.find("table", class_="table-striped")
    if not table:
        logger.warning("Auction table with class 'table-striped' not found")
        return auction_ids

    # Get all rows except header
    rows: list[Tag] = table.find_all("tr")
    if len(rows) <= 1:
        logger.warning("No auction rows found in table")
        return auction_ids

    data_rows = rows[1:]  # Skip header row
    logger.debug(f"Processing {len(data_rows)} auction rows")

    # Extract auction ID from each row
    for idx, tr in enumerate(data_rows, start=1):
        cells: list[Tag] = tr.find_all("td")

        if not cells or len(cells) <= 1:
            logger.debug(f"Row {idx}: Insufficient cells, skipping")
            auction_ids.append(None)
            continue

        # Look for auction link in second cell
        auction_link: Tag | None = cells[1].find("a")
        if not auction_link:
            logger.debug(f"Row {idx}: No auction link found")
            auction_ids.append(None)
            continue

        # Extract ID from onclick attribute
        onclick: str = auction_link.get("onclick", "")
        if not onclick:
            logger.debug(f"Row {idx}: No onclick attribute found")
            auction_ids.append(None)
            continue

        # Parse auction ID using regex
        match: re.Match[str] | None = re.search(
            r"/pokebay/auction/(\d+)/",
            onclick,
        )

        if match:
            auction_id = match.group(1)
            auction_ids.append(auction_id)
            logger.debug(f"Row {idx}: Extracted auction ID {auction_id}")
        else:
            logger.debug(
                f"Row {idx}: Could not extract auction ID from onclick: {onclick}"
            )
            auction_ids.append(None)

    logger.info(
        f"Extracted {len([aid for aid in auction_ids if aid])} valid auction IDs "
        f"out of {len(auction_ids)} total rows"
    )
    return auction_ids
