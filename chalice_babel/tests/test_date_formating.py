from datetime import datetime, timedelta
from decimal import Decimal

import chalice_babel as babel

from app import app
from chalice import Chalice
from chalice.test import Client

# from chalice_babel import Babel, format_decimal, format_number, format_percent, format_scientific, format_currency



def test_basics():
    babel.Babel(app)
    d = datetime(2010, 4, 12, 13, 46)
    delta = timedelta(days=6)

    with Client(app) as client:
        assert babel.format_datetime(d) == "Apr 12, 2010, 1:46:00 PM"
        assert babel.format_date(d) == "Apr 12, 2010"
        assert babel.format_time(d) == "1:46:00 PM"
        assert babel.format_timedelta(delta) == "1 week"
        assert babel.format_timedelta(delta, threshold=1) == "6 days"

    with Client(app) as client:
        app.chalice_babel["babel"].config["BABEL_DEFAULT_TIMEZONE"] = "Europe/Vienna"
        assert babel.format_datetime(d) == "Apr 12, 2010, 3:46:00 PM"
        assert babel.format_date(d) == "Apr 12, 2010"
        assert babel.format_time(d) == "3:46:00 PM"

    with Client(app) as client:
        app.chalice_babel["babel"].config["BABEL_DEFAULT_LOCALE"] = "de_DE"
        assert babel.format_datetime(d, "long") == "12. April 2010 um 15:46:00 MESZ"


def test_custom_formats():
    app.chalice_babel["babel"].config.update(BABEL_DEFAULT_LOCALE="en_US", BABEL_DEFAULT_TIMEZONE="Pacific/Johnston")
    b = babel.Babel(app)
    b.date_formats["datetime"] = "long"
    b.date_formats["datetime.long"] = "MMMM d, yyyy h:mm:ss a"
    d = datetime(2010, 4, 12, 13, 46)

    with Client(app) as client:
        assert babel.format_datetime(d) == "April 12, 2010 3:46:00 AM"


def test_custom_locale_selector():
    b = babel.Babel(app)
    d = datetime(2010, 4, 12, 13, 46)

    the_timezone = "UTC"
    the_locale = "en_US"

    @b.localeselector
    def select_locale():
        return the_locale

    @b.timezoneselector
    def select_timezone():
        return the_timezone

    with Client(app) as client:
        assert babel.format_datetime(d) == "Apr 12, 2010, 1:46:00 PM"

    the_locale = "de_DE"
    the_timezone = "Europe/Vienna"

    with Client(app) as client:
        assert babel.format_datetime(d) == "12.04.2010, 15:46:00"


def test_force_locale():
    b = babel.Babel(app)

    @b.localeselector
    def select_locale():
        return "de_DE"

    with Client(app) as client:
        assert str(babel.get_locale()) == "de_DE"
        with babel.force_locale("en_US"):
            assert str(babel.get_locale()) == "en_US"
        assert str(babel.get_locale()) == "de_DE"
