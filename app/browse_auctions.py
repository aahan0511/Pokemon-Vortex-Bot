import os

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from app.env import SESSION_ID, logger
from app.utils.extract_auction_ids import extract_auction_ids
from app.utils.extract_quantity_and_item import extract_quantity_and_item
from app.utils.get_budget import get_budget


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
