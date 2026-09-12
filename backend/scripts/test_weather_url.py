import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.services.weather_service import fetch_rainfall
from unittest.mock import patch, AsyncMock
import asyncio

async def test_weather_urls():
    test_urls = [
        "https://api.open-meteo.com",
        "https://api.open-meteo.com/",
        "https://api.open-meteo.com/v1",
        "https://api.open-meteo.com/v1/",
    ]

    for test_url in test_urls:
        # Mock settings to return our test URL
        settings = get_settings()
        original_url = settings.open_meteo_base_url
        settings.open_meteo_base_url = test_url
        
        try:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                # We need it to raise an error so we don't have to mock the full response
                mock_get.side_effect = Exception("Stop execution")
                
                await fetch_rainfall(25.0, 91.0)
                
                # Check what URL was actually passed to httpx.AsyncClient.get
                call_args = mock_get.call_args
                if call_args:
                    url_called = call_args[0][0]
                    if url_called == "https://api.open-meteo.com/v1/forecast":
                        print(f"PASS: Input '{test_url}' resulted in correct URL '{url_called}'")
                    else:
                        print(f"FAIL: Input '{test_url}' resulted in incorrect URL '{url_called}'")
        finally:
            settings.open_meteo_base_url = original_url

if __name__ == "__main__":
    asyncio.run(test_weather_urls())
