
import pytest
import psycopg2
from unittest.mock import patch

import database
from app import create_order
TEST_DB_CONFIG = {
    **database.DB_CONFIG,
    "dbname": "weather_orders_test"
}

# FIXTURES
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create tables once before all tests in this session"""
    database.create_tables(config=TEST_DB_CONFIG)
    yield

@pytest.fixture(autouse=True)
def clean_tables():
    """Wipe all rows before each test for a clean slate"""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM orders")
                cur.execute("DELETE FROM users")
    finally:
        conn.close()
    yield


# HELPER
def run_create_order_with_real_db(user_id: int, fake_weather: dict) -> dict:
    with patch("app.get_user") as mock_get_user, \
         patch("app.get_weather") as mock_get_weather, \
         patch("app.save_order") as mock_save_order:

        # Route DB calls to real test database
        mock_get_user.side_effect = lambda uid: database.get_user(uid, config=TEST_DB_CONFIG)
        mock_save_order.side_effect = lambda user_id, product: \
            database.save_order(user_id=user_id, product=product, config=TEST_DB_CONFIG)

        # Return controlled weather data
        mock_get_weather.return_value = fake_weather

        return create_order(user_id)

# COMBINED SCENARIO TESTS
class TestCombinedScenario:

    def test_snow_creates_jacket_order_in_db(self):
        # Arrange: create a real user in test DB
        user_id = database.create_user("Alice", "Astana", config=TEST_DB_CONFIG)

        # Act: run the full flow
        result = run_create_order_with_real_db(
            user_id,
            fake_weather={"temperature": -15.0, "condition": "snow"}
        )
        # Assert: check return value
        assert result["product"] == "jacket"
        assert result["user_id"] == user_id
        assert "order_id" in result
        assert result["order_id"] > 0

        # Assert: verify it was ACTUALLY written to the database
        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert len(orders) == 1
        assert orders[0]["product"] == "jacket"
        assert orders[0]["user_id"] == user_id

    def test_rain_creates_umbrella_order_in_db(self):
        """SCENARIO: User in rainy city → umbrella ordered and saved"""
        user_id = database.create_user("Bob", "London", config=TEST_DB_CONFIG)

        result = run_create_order_with_real_db(
            user_id,
            fake_weather={"temperature": 12.0, "condition": "rain"}
        )

        assert result["product"] == "umbrella"

        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert orders[0]["product"] == "umbrella"

    def test_sunny_creates_sunglasses_order_in_db(self):
        """SCENARIO: User in sunny city → sunglasses ordered and saved"""
        user_id = database.create_user("Carol", "Dubai", config=TEST_DB_CONFIG)

        result = run_create_order_with_real_db(
            user_id,
            fake_weather={"temperature": 42.0, "condition": "sunny"}
        )

        assert result["product"] == "sunglasses"

        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert orders[0]["product"] == "sunglasses"

    def test_multiple_users_get_independent_orders(self):
        """
        SCENARIO: Two users in different cities place orders.
        Each should only have their own orders.
        """
        alice_id = database.create_user("Alice", "Astana", config=TEST_DB_CONFIG)
        bob_id   = database.create_user("Bob",   "Dubai",  config=TEST_DB_CONFIG)

        run_create_order_with_real_db(alice_id, {"temperature": -5.0, "condition": "snow"})
        run_create_order_with_real_db(bob_id,   {"temperature": 40.0, "condition": "sunny"})

        alice_orders = database.get_orders_for_user(alice_id, config=TEST_DB_CONFIG)
        bob_orders   = database.get_orders_for_user(bob_id,   config=TEST_DB_CONFIG)

        assert alice_orders[0]["product"] == "jacket"
        assert bob_orders[0]["product"]   == "sunglasses"

        # Cross-contamination check
        assert len(alice_orders) == 1
        assert len(bob_orders)   == 1

    def test_nonexistent_user_raises_and_saves_nothing(self):
        """
        SCENARIO: Order for user that doesn't exist.
        Should raise ValueError. Nothing saved to DB.
        """
        with patch("app.get_user") as mock_get_user, \
             patch("app.get_weather") as mock_get_weather, \
             patch("app.save_order") as mock_save_order:

            mock_get_user.side_effect = lambda uid: database.get_user(uid, config=TEST_DB_CONFIG)
            mock_get_weather.return_value = {"temperature": 10.0, "condition": "rain"}
            mock_save_order.side_effect = lambda user_id, product: \
                database.save_order(user_id=user_id, product=product, config=TEST_DB_CONFIG)

            with pytest.raises(ValueError, match="not found"):
                create_order(user_id=99999)

            # Nothing should be in orders table
            conn = psycopg2.connect(**TEST_DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM orders")
                count = cur.fetchone()[0]
            conn.close()

            assert count == 0, "No orders should be created for non-existent user"

    def test_order_id_is_unique_for_each_call(self):
        """
        SCENARIO: Two orders for the same user get different IDs.
        Verifies auto-increment works correctly.
        """
        user_id = database.create_user("Dave", "Almaty", config=TEST_DB_CONFIG)

        result1 = run_create_order_with_real_db(user_id, {"temperature": 5.0, "condition": "rain"})
        result2 = run_create_order_with_real_db(user_id, {"temperature": 3.0, "condition": "snow"})

        assert result1["order_id"] != result2["order_id"]

        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert len(orders) == 2