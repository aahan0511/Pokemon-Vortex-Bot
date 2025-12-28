import logging
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from app.env import SESSION_ID
from app.utils.extract_auction_ids import extract_auction_ids
from app.utils.extract_quantity_and_item import extract_quantity_and_item
from app.utils.get_budget import get_budget

logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.pokemon-vortex.com/pokebay/browse/"
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.5  # Seconds between requests
PROGRESSIVE_CSV = Path("debug/auctions_progressive.csv")
FINAL_CSV = Path("out/auctions_final.csv")


def _get_headers() -> dict[str, str]:
    """Generate request headers with session cookie."""
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-length": "0",
        "content-type": "application/x-www-form-urlencoded",
        "dnt": "1",
        "origin": "https://www.pokemon-vortex.com",
        "priority": "u=1, i",
        "referer": "https://www.pokemon-vortex.com/pokebay/",
        "sec-ch-ua": '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Cookie": f"SESS={SESSION_ID}",
    }


def _process_page(response_text: str, soup: BeautifulSoup) -> pd.DataFrame:
    """
    Process a single page of auction data.

    Args:
        response_text: HTML response text
        soup: BeautifulSoup object of the page

    Returns:
        DataFrame with processed auction data
    """
    try:
        df: pd.DataFrame = pd.read_html(response_text)[0]
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse HTML table: {e}")
        return pd.DataFrame()

    # Validate required columns
    if df.empty or "Current Price" not in df.columns or "Auction" not in df.columns:
        logger.warning("DataFrame is empty or missing required columns")
        return pd.DataFrame()

    # Clean and convert price column
    df["Current Price"] = (
        df["Current Price"]
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(int)
    )

    # Extract quantity and item name
    extracted: pd.Series = df["Auction"].apply(extract_quantity_and_item)
    df["Quantity"] = extracted.apply(lambda x: x[0])
    df["Item"] = extracted.apply(lambda x: x[1])

    # Extract auction IDs
    df["Auction ID"] = extract_auction_ids(soup)

    logger.debug(
        f"Processed page: {len(df)} rows, "
        f"price range: ${df['Current Price'].min()} - ${df['Current Price'].max()}"
    )
    return df


def _get_total_pages(soup: BeautifulSoup) -> int:
    """
    Extract total number of pages from pagination.

    Args:
        soup: BeautifulSoup object of the first page

    Returns:
        Total number of pages
    """
    pagination_elements: list[Tag] = soup.select("div.pagination div.page-num")

    if not pagination_elements:
        logger.warning("No pagination elements found, assuming 1 page")
        return 1

    try:
        total_pages = int(pagination_elements[-1].text.strip())
        logger.info(f"Total pages available: {total_pages}")
        return total_pages
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse total pages: {e}")
        return 1


def browse_auctions(filter_type: str = "items") -> pd.DataFrame:
    """
    Scrape Pokemon Vortex auctions, stopping when prices exceed budget.

    Args:
        filter_type: Type of auction to filter ("items", "pokemon", etc.)

    Returns:
        DataFrame containing all scraped auction data
    """
    logger.info(f"Starting auction scraping with filter: {filter_type}")

    # Build URL and prepare request
    url: str = f"{BASE_URL}?order=pricelow&filter={filter_type}&search=&ajax=1"
    headers: dict[str, str] = _get_headers()

    # Fetch budget
    try:
        budget: int = get_budget()
    except Exception as e:
        logger.error(f"Failed to fetch budget: {e}")
        raise

    # Fetch first page
    try:
        logger.info("Fetching first page of auctions")
        response: requests.Response = requests.post(
            url, headers=headers, data={}, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

    except requests.RequestException as e:
        logger.error(f"Failed to fetch first page: {e}")
        raise

    soup: BeautifulSoup = BeautifulSoup(response.text, "lxml")
    total_pages: int = _get_total_pages(soup)

    # Process first page
    df: pd.DataFrame = _process_page(response.text, soup)

    if df.empty:
        logger.warning("First page returned no data")
        return df

    # Save progressive results
    df.to_csv(PROGRESSIVE_CSV, index=False)
    logger.info(
        f"Page 1/{total_pages} complete - "
        f"{len(df)} auctions, max price: ${df['Current Price'].max():,}"
    )

    # Process remaining pages
    for page in range(2, total_pages + 1):
        try:
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

            page_url: str = f"{url}&page={page}"
            logger.debug(f"Fetching page {page}/{total_pages}")

            page_response: requests.Response = requests.post(
                page_url, headers=headers, data={}, timeout=REQUEST_TIMEOUT
            )
            page_response.raise_for_status()

        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {page}: {e}")
            continue

        # Process page
        page_soup: BeautifulSoup = BeautifulSoup(page_response.text, "lxml")
        page_df: pd.DataFrame = _process_page(page_response.text, page_soup)

        if page_df.empty:
            logger.warning(f"Page {page} returned no data, skipping")
            continue

        # Append to progressive CSV
        page_df.to_csv(PROGRESSIVE_CSV, mode="a", header=False, index=False)
        df = pd.concat([df, page_df], ignore_index=True)

        logger.info(
            f"Page {page}/{total_pages} complete - "
            f"Total: {len(df)} auctions, "
            f"Page max price: ${page_df['Current Price'].max():,}"
        )

        # Check if we've exceeded budget
        if page_df["Current Price"].iloc[-1] > budget:
            logger.info(
                f"Stopping early: Last auction price ${page_df['Current Price'].iloc[-1]:,} "
                f"exceeds budget ${budget:,}"
            )
            break

    # Save final results
    df.to_csv(FINAL_CSV, index=False)
    logger.info(f"Saved final results to {FINAL_CSV}")

    # Cleanup progressive file
    if PROGRESSIVE_CSV.exists():
        PROGRESSIVE_CSV.unlink()
        logger.debug(f"Removed temporary file: {PROGRESSIVE_CSV}")

    logger.info(
        f"Scraping complete: {len(df)} total auctions, "
        f"price range: ${df['Current Price'].min():,} - ${df['Current Price'].max():,}"
    )
    return df
