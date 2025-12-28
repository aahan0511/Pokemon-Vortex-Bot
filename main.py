from app.browse_auctions import browse_auctions
from app.env import logger

logger.debug("APPLICATION STARTED")


if __name__ == "__main__":
    browse_auctions()
    logger.debug("APPLICATION ENDED")
