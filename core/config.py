from pydantic_settings import BaseSettings, SettingsConfigDict

from environs import Env


env = Env()
env.read_env()


class Settings(BaseSettings):
    # DB_HOST: str
    # DB_PORT: int
    # DB_USER: str
    # DB_PASS: str
    # DB_NAME: str

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = env.str("KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC_RAW: str = "news_raw"
    KAFKA_TOPIC_SAVED: str = "news_saved"
    KAFKA_TOPIC_TG_LINKS: str  = "tg_links"  # для ссылок из телеги

    @property
    def DATADASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{env('DB_USER')}:{env('DB_PASS')}@{env('DB_HOST')}:{env('DB_PORT')}/{env('DB_NAME')}"


    @property
    def DATADASE_URL_psycopg(self):
        return f"postgresql+psycopg://{env('DB_USER')}:{env('DB_PASS')}@{env('DB_HOST')}:{env('DB_PORT')}/{env('DB_NAME')}"


settings = Settings()
    