import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.api.health import health
from unittest.mock import patch, AsyncMock
import asyncio

async def test_health_url():
    test_urls = [
        "https://api.open-meteo.com",
        "https://api.open-meteo.com/",
        "https://api.open-meteo.com/v1",
        "https://api.open-meteo.com/v1/",
    ]

    for test_url in test_urls:
        settings = get_settings()
        original_url = settings.open_meteo_base_url
        settings.open_meteo_base_url = test_url
        
        try:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                # Mock a successful response
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_get.return_value = mock_response
                
                # Mock Supabase health check
                with patch("app.api.health.check_supabase_health", new_callable=AsyncMock) as mock_db:
                    mock_db.return_value = {"status": "ONLINE"}
                    
                    result = await health()
                    
                    call_args = mock_get.call_args
                    if call_args:
                        url_called = call_args[0][0]
                        if url_called == "https://api.open-meteo.com/v1/forecast":
                            print(f"PASS (URL): Input '{test_url}' -> '{url_called}'")
                        else:
                            print(f"FAIL (URL): Input '{test_url}' -> '{url_called}'")
                            
                        if result["checks"]["open_meteo"] == "ONLINE":
                            print(f"PASS (Status): Status is ONLINE")
                        else:
                            print(f"FAIL (Status): Status is {result['checks']['open_meteo']}")
        finally:
            settings.open_meteo_base_url = original_url

if __name__ == "__main__":
    asyncio.run(test_health_url())
