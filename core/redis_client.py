import redis.asyncio as redis

# создаём глобальное подключение
redis_client = redis.from_url("redis://localhost", decode_responses=True)
