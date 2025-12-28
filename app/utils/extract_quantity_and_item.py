from typing import Tuple


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
