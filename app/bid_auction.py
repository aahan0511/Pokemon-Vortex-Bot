import logging

import requests

from app.env import SESSION_ID

logger = logging.getLogger(__name__)

# Constants
REQUEST_TIMEOUT = 30


def _get_headers() -> dict[str, str]:
    """Generate request headers with session cookie."""
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "dnt": "1",
        "origin": "https://www.pokemon-vortex.com",
        "priority": "u=1, i",
        "referer": "https://www.pokemon-vortex.com/pokebay/",
        "sec-ch-ua": '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "Cookie": f"SESS={SESSION_ID}",
    }


def _parse_bid_response(response_text: str) -> None:
    """
    Parse bid response and check for errors.

    Args:
        response_text: HTML response text from bid request

    Raises:
        ValueError: If bid failed for any reason
    """
    response_lower = response_text.lower()

    # Check for insufficient funds
    if "you do not have enough money to make a bid that high." in response_lower:
        logger.error("Bid failed: Insufficient funds")
        raise ValueError("You do not have enough money to make this bid")

    # Check for bid too low
    if "sorry, your bid wasn't high enough to place." in response_lower:
        logger.error("Bid failed: Bid amount too low")
        raise ValueError("Bid must be higher than the current price")

    # Check for auction ended
    if "Sorry, this auction has ended." in response_lower:
        logger.error("Bid failed: Auction has ended")
        raise ValueError("This auction has already ended")


def bid_auction(auction_id: str, price: int) -> None:
    """
    Place a bid on a Pokemon Vortex auction.

    Args:
        auction_id: The auction ID to bid on
        price: The bid amount in dollars

    Raises:
        ValueError: If bid failed (insufficient funds, too low, etc.)
        requests.RequestException: If the HTTP request fails
    """
    logger.info(f"Attempting to bid ${price:,} on auction {auction_id}")

    url = f"https://www.pokemon-vortex.com/pokebay/auction/{auction_id}/?&ajax=1"
    payload = f"bid={price}&quickbid={price}"
    headers = _get_headers()

    try:
        response: requests.Response = requests.post(
            url, headers=headers, data=payload, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.debug(f"Bid request sent successfully (status: {response.status_code})")

    except requests.RequestException as e:
        logger.error(f"Failed to send bid request for auction {auction_id}: {e}")
        raise

    # Parse response for errors (raises ValueError if bid failed)
    _parse_bid_response(response.text)

    logger.info(f"Successfully placed bid of ${price:,} on auction {auction_id}")
