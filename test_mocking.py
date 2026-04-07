
import pytest
import requests
from unittest.mock import patch, MagicMock, call

from app import get_weather, create_order

#Success Scenarios
class TestWeatherApiSuccess:

    @patch("app.requests.get")
    def test_returns_correct_temperature(self, mock_get):
        #Verify temperature is correctly extracted from API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 18.5, "condition": "sunny"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        result = get_weather("Almaty")
        assert result["temperature"] == 18.5

    @patch("app.requests.get")
    def test_returns_correct_condition(self, mock_get):
        #Verify condition is correctly extracted from API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 2.0, "condition": "snow"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        result = get_weather("Astana")
        assert result["condition"] == "snow"

    @patch("app.requests.get")
    def test_api_called_with_correct_city(self, mock_get):
        #The city name must appear in the URL sent to the API
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 20.0, "condition": "sunny"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        get_weather("Bishkek")

        # Check the URL that was used
        actual_url = mock_get.call_args[0][0]
        assert "Bishkek" in actual_url

#Error / Failure Scenarios
class TestWeatherApiFailures:

    @patch("app.requests.get")
    def test_timeout_raises_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        with pytest.raises(requests.exceptions.Timeout):
            get_weather("Almaty")

    @patch("app.requests.get")
    def test_connection_error_raises_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("No internet")
        with pytest.raises(requests.exceptions.ConnectionError):
            get_weather("Almaty")

    @patch("app.requests.get")
    def test_http_500_raises_exception(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response
        with pytest.raises(requests.exceptions.HTTPError):
            get_weather("Almaty")

    @patch("app.requests.get")
    def test_http_404_raises_exception(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        with pytest.raises(requests.exceptions.HTTPError):
            get_weather("FakeCity123")

    @patch("app.requests.get")
    def test_empty_response_raises_valueerror(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        with pytest.raises(ValueError):
            get_weather("Almaty")

    @patch("app.requests.get")
    def test_response_missing_condition_raises_valueerror(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 20.0}  # missing condition!
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        with pytest.raises(ValueError, match="Invalid API response"):
            get_weather("Almaty")

    @patch("app.requests.get")
    def test_response_missing_temperature_raises_valueerror(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"condition": "sunny"}  # missing temperature!
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        with pytest.raises(ValueError, match="Invalid API response"):
            get_weather("Almaty")

#Verifying System Behavior Under Failures
class TestCreateOrderWithApiFailures:

    @patch("app.save_order")
    @patch("app.get_weather")
    @patch("app.get_user")
    def test_api_timeout_prevents_order_creation(self, mock_get_user, mock_get_weather, mock_save_order):
        mock_get_user.return_value = {"id": 1, "name": "Alice", "city": "Almaty"}
        mock_get_weather.side_effect = requests.exceptions.Timeout("Timed out")
        with pytest.raises(requests.exceptions.Timeout):
            create_order(user_id=1)
        mock_save_order.assert_not_called()

    @patch("app.save_order")
    @patch("app.get_weather")
    @patch("app.get_user")
    def test_invalid_api_data_prevents_order_creation(self, mock_get_user, mock_get_weather, mock_save_order):
        mock_get_user.return_value = {"id": 1, "name": "Alice", "city": "Almaty"}
        mock_get_weather.side_effect = ValueError("Invalid API response")
        with pytest.raises(ValueError):
            create_order(user_id=1)

        mock_save_order.assert_not_called()

#call_count and advanced mock assertions
class TestMockAssertions:
    @patch("app.requests.get")
    def test_api_called_exactly_once(self, mock_get):
        #The API should be called exactly 1 time per get_weather() call
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 15.0, "condition": "rain"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        get_weather("Almaty")
        assert mock_get.call_count == 1   

    @patch("app.requests.get")
    def test_api_called_twice_for_two_cities(self, mock_get):
        #Calling get_weather twice should make 2 API calls
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 10.0, "condition": "rain"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        get_weather("Almaty")
        get_weather("London")
        assert mock_get.call_count == 2