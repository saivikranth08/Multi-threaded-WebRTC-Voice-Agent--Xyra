# ─────────────────────────────────────────────
#  XYRA — Database Manager
#  Handles connection pools to Postgres & Redis
# ─────────────────────────────────────────────

import logging
import asyncpg
import redis.asyncio as aioredis
from xyra import config

logger = logging.getLogger("xyra.db")


class DatabaseManager:
    def __init__(self):
        self.pg_pool = None
        self.redis_client = None

    async def connect(self):
        """Initialize asynchronous connections to Redis and PostgreSQL."""
        try:
            # 1. Connect to Redis (Async)
            logger.info(f"Connecting to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}...")
            self.redis_client = aioredis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True,  # Decodes byte responses to string automatically
            )
            # Send ping to verify connection
            await self.redis_client.ping()
            logger.info("[OK] Connected to Redis successfully.")

            # 2. Connect to PostgreSQL (Async Pool)
            logger.info(
                f"Connecting to PostgreSQL at {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}..."
            )
            self.pg_pool = await asyncpg.create_pool(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                min_size=1,
                max_size=10,
            )
            logger.info("[OK] Connected to PostgreSQL successfully.")

        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize database connections: {str(e)}")
            raise e

    async def disconnect(self):
        """Shutdown connection pools gracefully on worker shutdown."""
        if self.pg_pool:
            logger.info("Closing PostgreSQL connection pool...")
            await self.pg_pool.close()
            self.pg_pool = None
            logger.info("PostgreSQL pool closed.")

        if self.redis_client:
            logger.info("Closing Redis connection...")
            await self.redis_client.aclose()
            self.redis_client = None
            logger.info("Redis connection closed.")


# Singleton database instance to import elsewhere in the project
db = DatabaseManager()

async def save_message_log(room_name: str, role: str, content: str):
    """
    Saves a chat log entry into the PostgreSQL database asynchronously.
    """
    if not db.pg_pool:
        logger.debug("Skipped saving message: Database not connected.")
        return

    query = """
        INSERT INTO chat_logs (room_name, role, content, timestamp)
        VALUES ($1, $2, $3, NOW())
    """
    try:
        async with db.pg_pool.acquire() as conn:
            # Check if table exists first just in case
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id SERIAL PRIMARY KEY,
                    room_name VARCHAR(255),
                    role VARCHAR(50),
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute(query, room_name, role, content)
    except Exception as e:
        logger.error(f"Failed to save message log: {e}")
