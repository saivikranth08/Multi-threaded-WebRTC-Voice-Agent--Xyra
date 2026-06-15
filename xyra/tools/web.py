# ─────────────────────────────────────────────
#  XYRA — Web Tools (with Redis Caching)
#  Tools related to web search, news, weather
# ─────────────────────────────────────────────

import asyncio
import logging
import requests
from tavily import TavilyClient
from xyra.config import TAVILY_API_KEY, OPENWEATHER_API_KEY, NEWS_API_KEY
from xyra.db import db

logger = logging.getLogger("xyra.tools.web")


# ── Tool Definitions ──────────────────────────

async def silent_data_fetch(query: str) -> str:
    """
    Search the internet silently to fetch raw text data for yourself to read.
    Use this when you need real-time information to answer a question.
    DO NOT use this if the user asks you to "show" them a website or visually open Chrome.
    """
    query_clean = query.strip().lower()
    cache_key = f"cache:search:{query_clean}"

    # 1. Try to fetch from Redis cache
    if db.redis_client:
        try:
            cached_val = await db.redis_client.get(cache_key)
            if cached_val:
                logger.info(f"[Cache HIT] Redis cache HIT for search query: '{query_clean}'")
                return cached_val
        except Exception as e:
            logger.warning(f"[Cache Error] Redis cache read error for query '{query_clean}': {e}")

    logger.info(f"[Cache MISS] Redis cache MISS. Fetching search results for: '{query_clean}'...")

    # 2. Cache miss -> Fetch search results in a thread pool
    try:
        def fetch():
            client = TavilyClient(api_key=TAVILY_API_KEY)
            return client.search(
                query=query,
                max_results=5,
                search_depth="advanced"
            )

        response = await asyncio.to_thread(fetch)

        results = []
        for r in response.get("results", []):
            results.append(
                f"📌 {r['title']}\n"
                f"🔗 {r['url']}\n"
                f"📝 {r['content'][:300]}...\n"
            )

        if not results:
            result_str = "No results found for your search."
        else:
            result_str = f"Search results for '{query}':\n\n" + "\n---\n".join(results)

        # 3. Cache the successful result in Redis (Expires in 2 hours / 7200 seconds)
        if db.redis_client and results:
            try:
                await db.redis_client.setex(cache_key, 7200, result_str)
                logger.info(f"[Cache SAVE] Cached search results for '{query_clean}' in Redis (TTL: 7200s).")
            except Exception as e:
                logger.warning(f"[Cache Warning] Failed to cache search results in Redis: {e}")

        return result_str

    except Exception as e:
        return f"Search failed: {str(e)}"


async def get_weather(city: str) -> str:
    """
    Get current weather conditions for any city.
    Use this when the user asks about weather,
    temperature, humidity, or climate in any location.
    """
    city_clean = city.strip().lower()
    cache_key = f"cache:weather:{city_clean}"

    # 1. Try to fetch from Redis cache
    if db.redis_client:
        try:
            cached_val = await db.redis_client.get(cache_key)
            if cached_val:
                logger.info(f"[Cache HIT] Redis cache HIT for weather in: '{city_clean}'")
                return cached_val
        except Exception as e:
            logger.warning(f"[Cache Error] Redis cache read error for weather in '{city_clean}': {e}")

    logger.info(f"[Cache MISS] Redis cache MISS. Fetching weather for: '{city_clean}'...")

    # 2. Cache miss -> Fetch weather in a thread pool
    try:
        def fetch():
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }
            return requests.get(url, params=params, timeout=10)

        response = await asyncio.to_thread(fetch)
        data = response.json()

        if response.status_code != 200:
            return f"Could not get weather for '{city}'. Please check the city name."

        weather     = data["weather"][0]["description"].capitalize()
        temp        = data["main"]["temp"]
        feels_like  = data["main"]["feels_like"]
        humidity    = data["main"]["humidity"]
        wind_speed  = data["wind"]["speed"]
        city_name   = data["name"]
        country     = data["sys"]["country"]
        lat         = data["coord"]["lat"]
        lon         = data["coord"]["lon"]

        result_str = (
            f"🌍 Weather in {city_name}, {country}:\n"
            f"🌤  Condition  : {weather}\n"
            f"🌡  Temperature: {temp}°C (Feels like {feels_like}°C)\n"
            f"💧 Humidity   : {humidity}%\n"
            f"💨 Wind Speed : {wind_speed} m/s\n"
            f"📍 Coordinates: {lat},{lon}"
        )

        # 3. Cache the weather response in Redis (Expires in 30 minutes / 1800 seconds)
        if db.redis_client:
            try:
                await db.redis_client.setex(cache_key, 1800, result_str)
                logger.info(f"[Cache SAVE] Cached weather for '{city_clean}' in Redis (TTL: 1800s).")
            except Exception as e:
                logger.warning(f"[Cache Warning] Failed to cache weather in Redis: {e}")

        return result_str

    except Exception as e:
        return f"Weather fetch failed: {str(e)}"


async def get_news(topic: str = "world", count: int = 5) -> str:
    """
    Get latest news headlines on any topic.
    Use this when the user asks for news, current events,
    headlines, or what's happening in the world or on
    a specific topic like tech, sports, business, science.
    """
    topic_clean = topic.strip().lower()
    cache_key = f"cache:news:{topic_clean}:{count}"

    # 1. Try to fetch from Redis cache
    if db.redis_client:
        try:
            cached_val = await db.redis_client.get(cache_key)
            if cached_val:
                logger.info(f"[Cache HIT] Redis cache HIT for news on: '{topic_clean}'")
                return cached_val
        except Exception as e:
            logger.warning(f"[Cache Error] Redis cache read error for news topic '{topic_clean}': {e}")

    logger.info(f"[Cache MISS] Redis cache MISS. Fetching news for: '{topic_clean}'...")

    # 2. Cache miss -> Fetch news headlines in a thread pool
    try:
        def fetch():
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": topic,
                "apiKey": NEWS_API_KEY,
                "pageSize": count,
                "sortBy": "publishedAt",
                "language": "en"
            }
            return requests.get(url, params=params, timeout=10)

        response = await asyncio.to_thread(fetch)
        data = response.json()

        if data.get("status") != "ok":
            return f"Could not fetch news: {data.get('message', 'Unknown error')}"

        articles = data.get("articles", [])
        if not articles:
            return f"No news found for topic: '{topic}'"

        results = []
        for i, article in enumerate(articles, 1):
            results.append(
                f"{i}. 📰 {article['title']}\n"
                f"   🗞  {article['source']['name']} | "
                f"{article['publishedAt'][:10]}\n"
                f"   🔗 {article['url']}"
            )

        result_str = f"Latest news on '{topic}':\n\n" + "\n\n".join(results)

        # 3. Cache the news response in Redis (Expires in 1 hour / 3600 seconds)
        if db.redis_client:
            try:
                await db.redis_client.setex(cache_key, 3600, result_str)
                logger.info(f"[Cache SAVE] Cached news for '{topic_clean}' in Redis (TTL: 3600s).")
            except Exception as e:
                logger.warning(f"[Cache Warning] Failed to cache news in Redis: {e}")

        return result_str

    except Exception as e:
        return f"News fetch failed: {str(e)}"


# ── Registration Helper ───────────────────────

def register_web_tools(mcp):
    """Register all web tools to the MCP server."""
    mcp.tool()(search_web)
    mcp.tool()(get_weather)
    mcp.tool()(get_news)
