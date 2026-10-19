from datetime import date, timedelta
from app.main import calculate_total, validate_delivery_date


def test_calculate_total_for_selected_products():
    assert calculate_total(["caixa", "caneca"]) == 43.00


def test_calculate_total_ignores_unknown_product():
    assert calculate_total(["caixa", "produto-inexistente"]) == 25.00


def test_delivery_date_must_be_after_today():
    today = date(2026, 10, 19)
    assert validate_delivery_date(today + timedelta(days=1), today=today) is True
    assert validate_delivery_date(today, today=today) is False
