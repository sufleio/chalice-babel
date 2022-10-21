from datetime import datetime, timedelta
from decimal import Decimal

from chalice_babel import Babel, format_currency, format_decimal, format_number, format_percent, format_scientific

from app import app
from chalice import Chalice
from chalice.test import Client

babel = Babel(app)

n = 1099


def test_basics():
    with Client(app) as client:
        # response = client.http.get('/')
        # assert response.json_body == {'hello': 'world'}
        assert format_number(n) == u"1,099"
        assert format_decimal(Decimal("1010.99")) == u"1,010.99"
        assert format_currency(n, "USD") == "$1,099.00"
        assert format_percent(0.19) == "19%"
        assert format_scientific(10000) == u"1E4"  # d = datetime(2010, 4, 12, 13, 46)


# delta = timedelta(days=6)

# babel.Babel(app)
