import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_quantity_and_item(auction_str: str) -> Tuple[int, str]:
    """
    Parse auction string into quantity and item name.
    
    Handles formats like:
        - "5x Rare Candy" -> (5, "Rare Candy")
        - "Master Ball" -> (1, "Master Ball")
        - "10x Ultra Ball" -> (10, "Ultra Ball")
    
    Args:
        auction_str: Raw auction string from the table
        
    Returns:
        Tuple of (quantity, item_name)
    """
    if not auction_str or not isinstance(auction_str, str):
        logger.warning(f"Invalid auction string received: {auction_str}")
        return 1, ""
    
    auction_str = auction_str.strip()
    
    # Check for quantity pattern (e.g., "5x Item Name")
    if "x " in auction_str:
        parts: list[str] = auction_str.split("x ", 1)
        
        try:
            quantity: int = int(parts[0].strip())
            item: str = " ".join(parts[1].strip().split())
            
            logger.debug(f"Parsed '{auction_str}' -> Quantity: {quantity}, Item: '{item}'")
            return quantity, item
            
        except (ValueError, IndexError) as e:
            logger.warning(
                f"Failed to parse quantity from '{auction_str}': {e}. "
                f"Defaulting to quantity 1"
            )
            item = " ".join(auction_str.strip().split())
            return 1, item
    
    # No quantity specified, default to 1
    item = " ".join(auction_str.strip().split())
    logger.debug(f"No quantity found in '{auction_str}', defaulting to 1x '{item}'")
    return 1, item