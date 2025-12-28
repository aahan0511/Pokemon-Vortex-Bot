import logging
import os

import dotenv

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
