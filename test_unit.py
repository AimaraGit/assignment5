"""
    pytest test_unit.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from app import suggest_product, get_weather, create_order

class TestSuggestProduct:
    def test_rain_returns_umbrella(self):
        """When it rains → suggest umbrella"""
        weather = {"temperature": 15.0, "condition": "rain"}
        result = suggest_product(weather)
        assert result == "umbrella"

    def test_sunny_returns_sunglasses(self):
        """When it's sunny → suggest sunglasses"""
        weather = {"temperature": 30.0, "condition": "sunny"}
        result = suggest_product(weather)
        assert result == "sunglasses"

    def test_snow_returns_jacket(self):
        """When it snows → suggest jacket"""
        weather = {"temperature": -5.0, "condition": "snow"}
        result = suggest_product(weather)
        assert result == "jacket"

    def test_unknown_condition_returns_unknown(self):
        """Unknown weather → return 'unknown' gracefully"""
        weather = {"temperature": 20.0, "condition": "tornado"}
        result = suggest_product(weather)
        assert result == "unknown"

    def test_condition_is_case_insensitive(self):
        """'RAIN', 'Rain', 'rain' should all work the same"""
        assert suggest_product({"condition": "RAIN"}) == "umbrella"
        assert suggest_product({"condition": "Rain"}) == "umbrella"

    def test_missing_condition_returns_unknown(self):
        """If 'condition' key is missing, return 'unknown' not crash"""
        result = suggest_product({})
        assert result == "unknown"

class TestGetWeather:
    @patch("app.requests.get")       # intercept requests.get inside app.py
    def test_successful_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "temperature": 25.0,
            "condition": "sunny"
        }
        mock_response.raise_for_status.return_value = None  
        mock_get.return_value = mock_response
        result = get_weather("Almaty")

        assert result["temperature"] == 25.0
        assert result["condition"] == "sunny"

        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]       
        assert "Almaty" in call_url

    @patch("app.requests.get")
    def test_rain_condition(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"temperature": 12.0, "condition": "rain"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_weather("London")
        assert result["condition"] == "rain"

    @patch("app.requests.get")
    def test_invalid_api_response_raises_valueerror(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"temp": 20}   # missing required fields!
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid API response"):
            get_weather("Paris")

    @patch("app.requests.get")
    def test_api_timeout_raises_exception(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout("Connection timed out")

        with pytest.raises(req.exceptions.Timeout):
            get_weather("Tokyo")

    @patch("app.requests.get")
    def test_api_server_error_raises_exception(self, mock_get):
        import requests as req
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        with pytest.raises(req.exceptions.HTTPError):
            get_weather("Berlin")

#Testing create_order (mock DB + mock API)

class TestCreateOrder:
    @patch("app.save_order")       # mock DB write
    @patch("app.get_weather")      # mock API call
    @patch("app.get_user")         # mock DB read
    def test_successful_order_flow(self, mock_get_user, mock_get_weather, mock_save_order):
        # Pretend the DB returned this user
        mock_get_user.return_value = {"id": 1, "name": "Alice", "city": "Almaty"}

        # Pretend the weather API returned this
        mock_get_weather.return_value = {"temperature": -3.0, "condition": "snow"}

        # Pretend save_order returned order ID 42
        mock_save_order.return_value = 42

        # Run the real function
        result = create_order(user_id=1)

        # Check result
        assert result["order_id"] == 42
        assert result["product"] == "jacket"     # snow → jacket
        assert result["user_id"] == 1
        assert result["weather"]["condition"] == "snow"

        # Verify each dependency was called correctly
        mock_get_user.assert_called_once_with(1)
        mock_get_weather.assert_called_once_with("Almaty")
        mock_save_order.assert_called_once_with(user_id=1, product="jacket")

    @patch("app.save_order")
    @patch("app.get_weather")
    @patch("app.get_user")
    def test_user_not_found_raises_valueerror(self, mock_get_user, mock_get_weather, mock_save_order):
        mock_get_user.return_value = None   # user not found
        with pytest.raises(ValueError, match="not found"):
            create_order(user_id=999)
        # These should not have been called at all
        mock_get_weather.assert_not_called()
        mock_save_order.assert_not_called()

    @patch("app.save_order")
    @patch("app.get_weather")
    @patch("app.get_user")
    def test_order_for_rainy_city(self, mock_get_user, mock_get_weather, mock_save_order):
        """User in a rainy city should get 'umbrella'"""
        mock_get_user.return_value = {"id": 2, "name": "Bob", "city": "London"}
        mock_get_weather.return_value = {"temperature": 10.0, "condition": "rain"}
        mock_save_order.return_value = 99

        result = create_order(user_id=2)
        assert result["product"] == "umbrella"

    @patch("app.save_order")
    @patch("app.get_weather")
    @patch("app.get_user")
    def test_db_failure_during_save(self, mock_get_user, mock_get_weather, mock_save_order):
        """If saving order fails, exception should propagate"""
        mock_get_user.return_value = {"id": 1, "name": "Alice", "city": "Almaty"}
        mock_get_weather.return_value = {"temperature": 25.0, "condition": "sunny"}
        mock_save_order.side_effect = Exception("DB connection lost")

        with pytest.raises(Exception, match="DB connection lost"):
            create_order(user_id=1)