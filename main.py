import logging
import os
import re
from typing import Tuple

import dotenv
import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

dotenv.load_dotenv()
SESSION_ID: str | None = os.getenv("SESSION_ID")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug/app.log"),
        logging.StreamHandler(),
    ],
)

logger: logging.Logger = logging.getLogger()
logger.debug("APPLICATION STARTED")


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
                    r"/pokebay/auction/(\d+)/", onclick
                )
                auction_ids.append(match.group(1) if match else None)
            else:
                auction_ids.append(None)

    return auction_ids


def extract_quantity_and_item(auction_str: str) -> Tuple[int, str]:
    """
    Parse auction string into quantity and item name.

    Examples:
        "5x Rare Candy" -> (5, "Rare Candy")
        "Master Ball" -> (1, "Master Ball")
    """
    if "x " in auction_str:
        parts: list[str] = auction_str.split("x ", 1)
        try:
            quantity: int = int(parts[0].strip())
            item: str = " ".join(parts[1].strip().split())
            return quantity, item
        except (ValueError, IndexError):
            item = " ".join(auction_str.strip().split())
            return 1, item
    else:
        item = " ".join(auction_str.strip().split())
        return 1, item


def browse_auctions(filter_type: str = "items") -> pd.DataFrame:
    """
    Scrape Pokemon Vortex auctions, stopping when prices exceed budget.

    Args:
        filter_type: Type of auction to filter ("items", "pokemon", etc.)

    Returns:
        DataFrame containing all scraped auction data
    """
    url: str = f"https://www.pokemon-vortex.com/pokebay/browse/?order=pricelow&filter={filter_type}&search=&ajax=1"
    headers: dict[str, str] = {
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

    response: requests.Response = requests.post(url, headers=headers, data={})
    soup: BeautifulSoup = BeautifulSoup(response.text, "lxml")

    pagination_elements: list[Tag] = soup.select("div.pagination div.page-num")
    total_pages: int = int(pagination_elements[-1].text.strip())
    logger.info(f"Total pages to scrape: {total_pages}")

    # Process first page
    df: pd.DataFrame = pd.read_html(response.text)[0]
    df["Current Price"] = (
        df["Current Price"].str.replace("$", "").str.replace(",", "").astype(int)
    )

    extracted: pd.Series = df["Auction"].apply(extract_quantity_and_item)
    df["Quantity"] = extracted.apply(lambda x: x[0])
    df["Item"] = extracted.apply(lambda x: x[1])
    df["Auction ID"] = extract_auction_ids(soup)

    df.to_csv("debug/auctions_progressive.csv", index=False)
    logger.info(f"PAGES SCRAPED: 1/{total_pages}")

    budget: int = get_budget()

    # Process remaining pages
    for page in range(2, total_pages + 1):
        try:
            page_url: str = f"{url}&page={page}"
            page_response: requests.Response = requests.post(
                page_url, headers=headers, data={}
            )
            page_soup: BeautifulSoup = BeautifulSoup(page_response.text, "lxml")

            page_df: pd.DataFrame = pd.read_html(page_response.text)[0]
            page_df["Current Price"] = (
                page_df["Current Price"]
                .str.replace("$", "")
                .str.replace(",", "")
                .astype(int)
            )

            extracted = page_df["Auction"].apply(extract_quantity_and_item)
            page_df["Quantity"] = extracted.apply(lambda x: x[0])
            page_df["Item"] = extracted.apply(lambda x: x[1])
            page_df["Auction ID"] = extract_auction_ids(page_soup)

            page_df.to_csv(
                "debug/auctions_progressive.csv", mode="a", header=False, index=False
            )

            df = pd.concat([df, page_df], ignore_index=True)
            logger.info(f"PAGES SCRAPED: {page}/{total_pages} - Total rows: {len(df)}")

            # Stop if prices exceed budget
            if page_df["Current Price"].iloc[-1] > budget:
                logger.info(
                    f"Stopping: Price ${page_df['Current Price'].iloc[-1]} exceeds budget ${budget}"
                )
                break

        except Exception as e:
            logger.error(f"ERROR SCRAPING PAGE {page}: {e}")
            continue

    # Save final results and cleanup
    df.to_csv("out/auctions_final.csv", index=False)
    if os.path.exists("debug/auctions_progressive.csv"):
        os.remove("debug/auctions_progressive.csv")

    logger.info(f"SCRAPING COMPLETE: Scraped {len(df)} rows")
    return df


if __name__ == "__main__":
    browse_auctions()
    logger.debug("APPLICATION ENDED")
