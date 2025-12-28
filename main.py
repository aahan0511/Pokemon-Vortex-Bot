import logging
import sys

from app.browse_auctions import browse_auctions

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for the Pokemon Vortex auction scraper.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("=" * 60)
    logger.info("Pokemon Vortex Auction Scraper - Starting")
    logger.info("=" * 60)
    
    try:
        df = browse_auctions(filter_type="items")
        
        if df.empty:
            logger.warning("No auction data was scraped")
            return 1
        
        logger.info("=" * 60)
        logger.info(f"Scraping completed successfully - {len(df)} auctions found")
        logger.info("=" * 60)
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        return 1
        
    except Exception as e:
        logger.exception(f"Fatal error during scraping: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)