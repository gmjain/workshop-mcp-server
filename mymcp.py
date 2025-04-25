import requests
import yfinance as yf
from mcp.server.fastmcp import FastMCP, Context
import json

# Create a named server
mcp = FastMCP("Weather & Stock Data Server")

# ------------ Weather Tools ------------

@mcp.tool()
async def get_weather(ctx: Context, latitude: float, longitude: float) -> str:
    """
    Get current weather information for a specific location using latitude and longitude.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.

    Returns:
        A JSON string containing current weather data.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m&timezone=auto"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses
        weather_data = response.json()
        return json.dumps(weather_data, indent=2)
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"


@mcp.tool()
async def get_weather_forecast(ctx: Context, latitude: float, longitude: float, days: int = 7) -> str:
    """
    Get weather forecast for a specific location using latitude and longitude.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.
        days: Number of days for the forecast (default: 7, max: 16)

    Returns:
        A JSON string containing weather forecast data.
    """
    if days > 16:
        days = 16  # API limitation

    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours,wind_speed_10m_max&timezone=auto&forecast_days={days}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses
        forecast_data = response.json()
        return json.dumps(forecast_data, indent=2)
    except Exception as e:
        return f"Error fetching weather forecast: {str(e)}"


@mcp.tool()
async def get_location_coordinates(ctx: Context, location_name: str) -> str:
    """
    Get latitude and longitude for a location name using Open-Meteo Geocoding API.

    Args:
        location_name: The name of the location to get coordinates for. Only city name should be provided.

    Returns:
        A JSON string containing location data including coordinates.
    """
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=10&language=en&format=json"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses
        location_data = response.json()
        return json.dumps(location_data, indent=2)
    except Exception as e:
        return f"Error fetching location data: {str(e)}"


# ------------ Stock Tools ------------

@mcp.tool()
async def get_stock_price(ctx: Context, symbol: str) -> str:
    """
    Get the latest stock price information for a given ticker symbol.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).

    Returns:
        A JSON string containing current stock data.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Select relevant information
        data = {
            "symbol": symbol,
            "name": info.get("shortName", "N/A"),
            "price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
            "currency": info.get("currency", "USD"),
            "day_high": info.get("dayHigh", "N/A"),
            "day_low": info.get("dayLow", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "volume": info.get("volume", "N/A"),
            "average_volume": info.get("averageVolume", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A")
        }

        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching stock data for {symbol}: {str(e)}"


@mcp.tool()
async def get_stock_history(ctx: Context, symbol: str, period: str = "1mo") -> str:
    """
    Get historical stock price data for a given ticker symbol.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
        period: The time period for historical data. Options: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'

    Returns:
        A JSON string containing historical stock price data.
    """
    valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']

    if period not in valid_periods:
        return f"Invalid period: {period}. Valid options are: {', '.join(valid_periods)}"

    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)

        # Convert to a format suitable for JSON serialization
        data = []
        for date, row in history.iterrows():
            data.append({
                "date": date.strftime('%Y-%m-%d'),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"]
            })

        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching historical stock data for {symbol}: {str(e)}"


@mcp.tool()
async def search_stocks(ctx: Context, query: str) -> str:
    """
    Search for stocks that match a query string.

    Args:
        query: The search query (company name or partial symbol)

    Returns:
        A JSON string containing matching stock tickers.
    """
    try:
        # Use the Yahoo Finance API to search for stocks
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10&newsCount=0"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        search_results = response.json()

        quotes = search_results.get("quotes", [])

        results = []
        for quote in quotes:
            if "symbol" in quote:
                results.append({
                    "symbol": quote.get("symbol", ""),
                    "name": quote.get("longname", quote.get("shortname", "")),
                    "exchange": quote.get("exchange", ""),
                    "type": quote.get("quoteType", "")
                })

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching for stocks: {str(e)}"


# ------------ Prompts ------------

@mcp.prompt("weather-report")
async def weather_report_prompt(ctx: Context, location: str) -> str:
    """
    Generate a prompt for creating a weather report for a specific location.

    Args:
        location: The name of the location for the weather report

    Returns:
        A prompt for generating a weather report.
    """
    return f"""
    Generate a detailed weather report for {location}.

    First, I need to get the coordinates for this location. Only city name should be provided:
    {{{{get_location_coordinates(location_name="{location}")}}}}

    Using those coordinates, I'll fetch the current weather:
    {{{{get_weather(latitude=LATITUDE, longitude=LONGITUDE)}}}}

    And also get a 7-day forecast:
    {{{{get_weather_forecast(latitude=LATITUDE, longitude=LONGITUDE, days=7)}}}}

    Please provide a comprehensive weather report for {location} including:

    1. Current conditions (temperature, humidity, wind, etc.)
    2. Weather forecast for the next 7 days
    3. Any notable weather patterns or extreme conditions to be aware of

    Make the report informative but easy to understand.
    The expected output is tabular.
    """


@mcp.prompt("stock-analysis")
async def stock_analysis_prompt(ctx: Context, company: str) -> str:
    """
    Generate a prompt for analyzing a company's stock.

    Args:
        company: The company name or stock symbol to analyze

    Returns:
        A prompt for analyzing stock data.
    """
    return f"""
    Perform a detailed analysis of {company}'s stock.

    First, let me search for the correct stock symbol:
    {{{{search_stocks(query="{company}")}}}}

    Now, I'll get the current stock price and information:
    {{{{get_stock_price(symbol="SYMBOL")}}}}

    Let me also get the historical data for the past 3 months:
    {{{{get_stock_history(symbol="SYMBOL", period="3mo")}}}}

    Based on this data, please provide:

    1. Current stock performance summary
    2. Key price points (current, daily range, 52-week range)
    3. Recent price trends over the past 3 months
    4. Basic analysis of the company's financial health based on available metrics

    Make your analysis informative for someone interested in this stock but not necessarily an expert in finance.
    The expected output is tabular.
    """


# Run the server
if __name__ == "__main__":
    # Add server dependencies
    mcp.dependencies = ["requests", "yfinance"]
    mcp.run()
