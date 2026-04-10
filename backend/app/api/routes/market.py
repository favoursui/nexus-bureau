from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.stellar.wallet import get_public_key
from app.config import get_settings
import httpx
from datetime import datetime


settings = get_settings()
router = APIRouter(prefix="/market", tags=["market"])


def requires_payment(request: Request, amount: str = "0.01", currency: str = "XLM"):
    payment_hash = (
        request.headers.get("X-Payment") or
        request.headers.get("X-Payment-Hash")
    )
    if not payment_hash:
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "amount": amount,
                "currency": currency,
                "destination": get_public_key(),
                "network": settings.STELLAR_NETWORK,
                "description": "Access requires x402 micro-payment"
            },
            headers={
                "X-Payment-Amount": amount,
                "X-Payment-Currency": currency,
                "X-Payment-Destination": get_public_key(),
                "X-Payment-Network": settings.STELLAR_NETWORK
            }
        )
    return None


@router.get("/price/{symbol}")
async def get_price(symbol: str, request: Request):
    """Real-time crypto price. Costs 0.01 XLM."""
    payment_response = requires_payment(request, amount="0.01", currency="XLM")
    if payment_response:
        return payment_response

    symbol_map = {
        "BTC": "bitcoin", "ETH": "ethereum",
        "XLM": "stellar", "SOL": "solana",
        "USDC": "usd-coin", "BNB": "binancecoin"
    }

    coin_id = symbol_map.get(symbol.upper(), symbol.lower())

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true"
                }
            )
            data = res.json()

            if not data or coin_id not in data:
                return JSONResponse(
                    status_code=404,
                    content={"error": f"Symbol {symbol} not found"}
                )

            coin_data = data[coin_id]
            return {
                "symbol": symbol.upper(),
                "price_usd": coin_data.get("usd"),
                "change_24h": round(coin_data.get("usd_24h_change", 0), 2),
                "volume_24h": coin_data.get("usd_24h_vol"),
                "market_cap": coin_data.get("usd_market_cap"),
                "timestamp": datetime.now().isoformat(),
                "source": "Nexus Market API (via CoinGecko)",
                "paid": True
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch price: {str(e)}"}
        )


@router.get("/news")
async def get_news(request: Request):
    """Latest crypto news. Costs 0.02 XLM."""
    payment_response = requires_payment(request, amount="0.02", currency="XLM")
    if payment_response:
        return payment_response

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = client.search(
            query="cryptocurrency blockchain news today",
            max_results=5,
            search_depth="basic"
        )
        news = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:200],
                "source": r.get("url", "").split("/")[2] if r.get("url") else ""
            }
            for r in results.get("results", [])
        ]
        return {
            "news": news,
            "count": len(news),
            "timestamp": datetime.now().isoformat(),
            "source": "Nexus News API (via Tavily)",
            "paid": True
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch news: {str(e)}"}
        )


@router.get("/weather/{city}")
async def get_weather(city: str, request: Request):
    """Real-time weather data. Costs 0.01 XLM."""
    payment_response = requires_payment(request, amount="0.01", currency="XLM")
    if payment_response:
        return payment_response

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # First geocode the city
            geo_res = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            geo_data = geo_res.json()

            if not geo_data.get("results"):
                return JSONResponse(
                    status_code=404,
                    content={"error": f"City {city} not found"}
                )

            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]

            # Get weather
            weather_res = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                    "temperature_unit": "celsius"
                }
            )
            weather_data = weather_res.json()
            current = weather_data.get("current", {})

            # Map weather codes to conditions
            code = current.get("weather_code", 0)
            if code == 0: condition = "Clear"
            elif code <= 3: condition = "Partly Cloudy"
            elif code <= 48: condition = "Foggy"
            elif code <= 67: condition = "Rainy"
            elif code <= 77: condition = "Snowy"
            elif code <= 82: condition = "Showers"
            else: condition = "Stormy"

            return {
                "city": location["name"],
                "country": location.get("country", ""),
                "data": {
                    "temp_celsius": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "condition": condition
                },
                "timestamp": datetime.now().isoformat(),
                "source": "Nexus Weather API (via Open-Meteo)",
                "paid": True
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch weather: {str(e)}"}
        )


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str, request: Request):
    """Market sentiment from price movements. Costs 0.05 XLM."""
    payment_response = requires_payment(request, amount="0.05", currency="XLM")
    if payment_response:
        return payment_response

    symbol_map = {
        "BTC": "bitcoin", "ETH": "ethereum",
        "XLM": "stellar", "SOL": "solana"
    }

    coin_id = symbol_map.get(symbol.upper(), symbol.lower())

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={"localization": "false", "tickers": "false", "community_data": "true"}
            )
            data = res.json()

            price_change = data.get("market_data", {}).get("price_change_percentage_24h", 0)
            community = data.get("community_data", {})
            twitter_followers = community.get("twitter_followers", 0)

            # Calculate sentiment score
            score = 50
            if price_change > 5: score = 85
            elif price_change > 2: score = 72
            elif price_change > 0: score = 60
            elif price_change > -2: score = 45
            elif price_change > -5: score = 30
            else: score = 15

            if score >= 70: label = "Very Bullish"
            elif score >= 55: label = "Bullish"
            elif score >= 45: label = "Neutral"
            elif score >= 30: label = "Bearish"
            else: label = "Very Bearish"

            return {
                "symbol": symbol.upper(),
                "sentiment": {
                    "score": score,
                    "label": label,
                    "price_change_24h": round(price_change, 2),
                    "twitter_followers": twitter_followers
                },
                "timestamp": datetime.now().isoformat(),
                "source": "Nexus Sentiment API (via CoinGecko)",
                "paid": True
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch sentiment: {str(e)}"}
        )