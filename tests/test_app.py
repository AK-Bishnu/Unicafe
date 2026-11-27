import sys
from pathlib import Path

# Add project root to Python import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from unittest.mock import patch
import app

@pytest.fixture
def sample_menu():
    return [
        {"id": 1, "name": "Burger", "price": 150, "stock": 10},
        {"id": 2, "name": "Coffee", "price": 50, "stock": 10},
        {"id": 3, "name": "Fries", "price": 60, "stock": 10}
    ]


def test_discount_applied_for_three_items(sample_menu):
    with patch("app.get_menu", return_value=sample_menu):
        cart = {"1": 1, "2": 1, "3": 1}

        subtotal, discount, total = app.calculate_bill(cart)

        assert subtotal == 260
        assert discount == 26
        assert total == 234


def test_no_discount_for_two_items(sample_menu):
    with patch("app.get_menu", return_value=sample_menu):
        cart = {"1": 1, "2": 1}

        subtotal, discount, total = app.calculate_bill(cart)

        assert subtotal == 200
        assert discount == 0
        assert total == 200


def test_add_item_to_cart(sample_menu):
    app.app.config["TESTING"] = True

    with patch("app.get_menu", return_value=sample_menu):
        client = app.app.test_client()

        response = client.post("/add/1")

        assert response.status_code == 302

        with client.session_transaction() as session:
            assert session["cart"]["1"] == 1


def test_unavailable_item_not_added(sample_menu):
    app.app.config["TESTING"] = True

    with patch("app.get_menu", return_value=sample_menu):
        client = app.app.test_client()

        response = client.post("/add/99")

        assert response.status_code == 302

        with client.session_transaction() as session:
            assert session.get("cart", {}) == {}
