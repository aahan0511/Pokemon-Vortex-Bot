import os
import logging

import dotenv
import requests

dotenv.load_dotenv()
SESSION_ID = os.getenv("SESSION_ID")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Log to file
        logging.StreamHandler()           # Also log to console
    ]
)

logger = logging.getLogger()
logger.debug("Application started")

def login():
    url = "https://www.pokemon-vortex.com/login-auth/"

    payload = f"myusername={USERNAME}&mypassword={PASSWORD}&tz=Asia%2FCalcutta&submit=Log%20In"
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

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=payload,
    )

    if "The username or password you entered is incorrect." in response.text:
        logger.critical("LOGIN FAILED: Invalid Credentials")
        raise Exception("Invalid credentials")
        
    if USERNAME in response.text:
        logger.info("LOGIN SUCCESSFUL")
    else:
        logger.warning("LOGIN UNSURE: Username not in Response")
