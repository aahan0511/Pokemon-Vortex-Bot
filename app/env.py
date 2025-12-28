import logging
import os
from pathlib import Path

import dotenv

# Load environment variables
dotenv.load_dotenv()

# Validate SESSION_ID
SESSION_ID: str | None = os.getenv("SESSION_ID")
if not SESSION_ID:
    raise ValueError(
        "SESSION_ID environment variable is required. "
        "Please set it in your .env file."
    )

# Create required directories
DIRS = ["debug", "out"]
for directory in DIRS:
    Path(directory).mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug/app.log"),
        logging.StreamHandler(),
    ],
)

logger: logging.Logger = logging.getLogger(__name__)
logger.info("Environment initialized successfully")
logger.debug(f"Required directories created: {', '.join(DIRS)}")