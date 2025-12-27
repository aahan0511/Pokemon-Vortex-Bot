import logging
import os

import dotenv
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas import DataFrame

dotenv.load_dotenv()
SESSION_ID = os.getenv("SESSION_ID")
USERNAME = os.getenv("USER")
PASSWORD = os.getenv("PWD")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger()
logger.debug("Application started")


def login():
    url = "https://www.pokemon-vortex.com/login-auth/"

    payload = {
        "myusername": USERNAME,
        "mypassword": PASSWORD,
        "tz": "Asia/Calcutta",
        "submit": "Log In",
    }
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "dnt": "1",
        "origin": "https://www.pokemon-vortex.com",
        "priority": "u=0, i",
        "referer": "https://www.pokemon-vortex.com/login/?action=logout",
        "sec-ch-ua": '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Cookie": f"SESS={SESSION_ID}",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if "The username or password you entered is incorrect." in response.text:
        logger.critical("LOGIN FAILED: Invalid Credentials")
        raise Exception("Invalid credentials")

    if USERNAME in response.text:
        logger.info("LOGIN SUCCESSFUL")
    else:
        logger.warning("LOGIN UNSURE: Username not in Response")


def browse_auctions(filter_type):
    url = f"https://www.pokemon-vortex.com/pokebay/browse/?order=&filter={filter_type}&search=&ajax=1"

    payload = {}
    headers = {
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

    response = requests.request("POST", url, headers=headers, data=payload)

    html = response.text
    soup = BeautifulSoup(html, "lxml")

    total_pages = int(soup.select("div.pagination div.page-num")[-1].text.strip())
    logger.info(f"Total pages to scrape: {total_pages}")

    df: DataFrame = pd.read_html(html)[0]
    df.to_csv("auctions_progressive.csv", index=False)
    logger.info(f"PAGES SCRAPED: 1/{total_pages}")

    for page in range(2, total_pages + 1):
        try:
            page_url = url + "&page=" + str(page)
            page_response = requests.request(
                "POST", page_url, headers=headers, data=payload
            )

            page_html = page_response.text
            page_df = pd.read_html(page_html)[0]

            # Append to CSV (no header after first page)
            page_df.to_csv(
                "auctions_progressive.csv", mode="a", header=False, index=False
            )

            df = pd.concat([df, page_df], ignore_index=True)
            logger.info(f"PAGES SCRAPED: {page}/{total_pages} - Total rows: {len(df)}")

        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
            continue

    # Final save
    df.to_csv("auctions_final.csv", index=False)
    logger.info(f"Scraping complete! Total rows: {len(df)}")
    return df


if __name__ == "__main__":
    # login()
    browse_auctions("items")
