
import pytest
import psycopg2
from unittest.mock import patch

import database
from app import create_order

TEST_DB_CONFIG = {
    **database.DB_CONFIG,           # copy all settings from database.py
    "dbname": "weather_orders_test" # override just the database name
}
# FIXTURES

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    database.create_tables(config=TEST_DB_CONFIG)
    yield   # tests run here
    # (nothing to clean up at session level)

@pytest.fixture(autouse=True)
def clean_tables():
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                # Delete orders first (foreign key constraint)
                cur.execute("DELETE FROM orders")
                cur.execute("DELETE FROM users")
    finally:
        conn.close()
    yield   # test runs here

# Helper: create a user directly in the test DB
def create_test_user(name: str, city: str) -> int:
    return database.create_user(name=name, city=city, config=TEST_DB_CONFIG)

#Database Layer Tests
class TestDatabaseLayer:

    def test_create_user_returns_id(self):
        """Creating a user should return a positive integer ID"""
        user_id = create_test_user("Alice", "Almaty")
        assert isinstance(user_id, int)
        assert user_id > 0

    def test_get_user_returns_correct_data(self):
        """After inserting, we should be able to read the same data back"""
        user_id = create_test_user("Bob", "London")

        user = database.get_user(user_id, config=TEST_DB_CONFIG)

        assert user is not None
        assert user["name"] == "Bob"
        assert user["city"] == "London"
        assert user["id"] == user_id

    def test_get_user_returns_none_for_missing_id(self):
        """Querying a non-existent user should return None, not crash"""
        result = database.get_user(99999, config=TEST_DB_CONFIG)
        assert result is None

    def test_save_order_returns_id(self):
        """Saving an order should return a positive integer ID"""
        user_id = create_test_user("Carol", "Paris")
        order_id = database.save_order(user_id=user_id, product="umbrella", config=TEST_DB_CONFIG)

        assert isinstance(order_id, int)
        assert order_id > 0

    def test_order_is_stored_in_database(self):
        """After saving, we should be able to retrieve the order from DB"""
        user_id = create_test_user("Dave", "Berlin")
        database.save_order(user_id=user_id, product="jacket", config=TEST_DB_CONFIG)

        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)

        assert len(orders) == 1
        assert orders[0]["product"] == "jacket"
        assert orders[0]["user_id"] == user_id

    def test_multiple_orders_for_same_user(self):
        """A user can have multiple orders — all should be retrievable"""
        user_id = create_test_user("Eve", "Tokyo")

        database.save_order(user_id=user_id, product="umbrella", config=TEST_DB_CONFIG)
        database.save_order(user_id=user_id, product="jacket", config=TEST_DB_CONFIG)

        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert len(orders) == 2

        products = [o["product"] for o in orders]
        assert "umbrella" in products
        assert "jacket" in products

    def test_two_users_data_stays_separate(self):
        """Orders for user A should not appear when querying user B"""
        user_a = create_test_user("Amber", "Almaty")
        user_b = create_test_user("Kaizer", "London")

        database.save_order(user_id=user_a, product="sunglasses", config=TEST_DB_CONFIG)

        orders_b = database.get_orders_for_user(user_b, config=TEST_DB_CONFIG)
        assert len(orders_b) == 0   # Bob has no orders

#Full Flow Integration Tests

class TestFullOrderFlow:
    def _patched_create_order(self, user_id, weather_response):
        # We patch get_user and save_order to use test DB config
        with patch("app.get_user") as mock_get_user, \
             patch("app.get_weather") as mock_get_weather, \
             patch("app.save_order") as mock_save_order:

            # get_user reads from REAL test DB
            mock_get_user.side_effect = lambda uid: database.get_user(uid, config=TEST_DB_CONFIG)

            # get_weather returns our fake weather
            mock_get_weather.return_value = weather_response

            # save_order writes to REAL test DB
            mock_save_order.side_effect = lambda user_id, product: \
                database.save_order(user_id=user_id, product=product, config=TEST_DB_CONFIG)

            return create_order(user_id)

    def test_full_flow_creates_order_in_db(self):
        user_id = create_test_user("Alice", "Almaty")
        result = self._patched_create_order(
            user_id,
            weather_response={"temperature": -2.0, "condition": "snow"}
        )
        # Check return value
        assert result["product"] == "jacket"
        assert result["user_id"] == user_id
        # Verify the order was ACTUALLY saved in the database
        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert len(orders) == 1
        assert orders[0]["product"] == "jacket"
    def test_full_flow_sunny_city(self):
        """User in a sunny city gets sunglasses"""
        user_id = create_test_user("Bob", "Dubai")
        result = self._patched_create_order(
            user_id,
            weather_response={"temperature": 40.0, "condition": "sunny"}
        )
        assert result["product"] == "sunglasses"
        orders = database.get_orders_for_user(user_id, config=TEST_DB_CONFIG)
        assert orders[0]["product"] == "sunglasses"