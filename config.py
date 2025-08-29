import logging

# --- Kafka ---
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC_RAW = "news_raw"
KAFKA_TOPIC_SAVED = "news_saved"

# --- DB ---
DB_URL = "sqlite+aiosqlite:///news.db"

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,  # уровни: DEBUG / INFO / WARNING / ERROR / CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("news_aggregator.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("news_aggregator")
