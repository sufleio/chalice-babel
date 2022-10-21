import chalice_babel as babel
from chalice_babel import (
    Domain,
    gettext,
    lazy_gettext,
    lazy_ngettext,
    ngettext,
    render_template_string,
)

from app import app
from chalice.test import Client


def test_basics():
    babel.Babel(app, default_locale="de_DE")

    with Client(app) as client:
        assert gettext(u"Hello %(name)s!", name="Peter") == "Hallo Peter!"
        assert ngettext(u"%(num)s Apple", u"%(num)s Apples", 3) == u"3 Äpfel"
        assert ngettext(u"%(num)s Apple", u"%(num)s Apples", 1) == u"1 Apfel"


def test_template_basics():
    babel.Babel(app, default_locale="de_DE")

    t = lambda x: render_template_string("{{ %s }}" % x)

    with Client(app) as client:
        assert t("gettext('Hello %(name)s!', name='Peter')") == u"Hallo Peter!"
        assert t("ngettext('%(num)s Apple', '%(num)s Apples', 3)") == u"3 Äpfel"
        assert t("ngettext('%(num)s Apple', '%(num)s Apples', 1)") == u"1 Apfel"
        assert (
            render_template_string(
                """
            {% trans %}Hello {{ name }}!{% endtrans %}
        """,
                name="Peter",
            ).strip()
            == "Hallo Peter!"
        )
        assert (
            render_template_string(
                """
            {% trans num=3 %}{{ num }} Apple
            {%- pluralize %}{{ num }} Apples{% endtrans %}
        """,
                name="Peter",
            ).strip()
            == u"3 Äpfel"
        )


def test_lazy_gettext():
    babel.Babel(app, default_locale="tr_TR")
    yes = lazy_gettext(u"Yes")
    with Client(app) as client:
        assert str(yes) == "Evet"
        assert yes.__html__() == "Evet"

    app.chalice_babel["babel"].config["BABEL_DEFAULT_LOCALE"] = "en_US"
    with Client(app) as client:
        assert str(yes) == "Yes"
        assert yes.__html__() == "Yes"


def test_lazy_ngettext():
    babel.Babel(app, default_locale="de_DE")
    one_apple = lazy_ngettext(u"%(num)s Apple", u"%(num)s Apples", 1)
    with Client(app) as client:
        assert str(one_apple) == "1 Apfel"
        assert one_apple.__html__() == "1 Apfel"
    two_apples = lazy_ngettext(u"%(num)s Apple", u"%(num)s Apples", 2)
    with Client(app) as client:
        assert str(two_apples) == u"2 Äpfel"
        assert two_apples.__html__() == u"2 Äpfel"


def test_list_translations():
    b = babel.Babel(app, default_locale="tr_TR")
    translations = b.list_translations()
    assert len(translations) == 2
    assert str(translations[0]) == "de"


def test_domain():
    b = babel.Babel(app, default_locale="de_DE")
    domain = Domain(domain="test")

    with Client(app) as client:
        assert domain.gettext("first") == "erste"
        assert babel.gettext("first") == "first"


def test_default_domain():
    b = babel.Babel(app, default_locale="tr_TR", default_domain="test")

    with Client(app) as client:
        assert babel.gettext("first") == "first"


def test_cache(mocker):
    load_mock = mocker.patch(
        "babel.support.Translations.load", side_effect=babel.support.Translations.load
    )

    b = babel.Babel(app, default_locale="de_DE")

    @b.localeselector
    def select_locale():
        return the_locale

    the_locale = "en_US"
    with Client(app) as client:
        assert b.domain_instance.get_translations_cache() == {}
        assert babel.gettext("Yes") == "Yes"
    assert load_mock.call_count == 2

    with Client(app) as client:
        assert set(b.domain_instance.get_translations_cache()) == {
            ("en_US", "messages")
        }
        assert babel.gettext("Yes") == "Yes"
    assert load_mock.call_count == 2

    the_locale = "de_DE"
    with Client(app) as client:
        assert set(b.domain_instance.get_translations_cache()) == {
            ("en_US", "messages")
        }
        assert babel.gettext("Yes") == "Ja"
    assert load_mock.call_count == 4

    the_locale = "en_US"
    with Client(app) as client:
        assert set(b.domain_instance.get_translations_cache()) == {
            ("en_US", "messages"),
            ("de_DE", "messages"),
        }
        assert babel.gettext("Yes") == "Yes"
    assert load_mock.call_count == 4

    the_locale = "de_DE"
    with Client(app) as client:
        assert set(b.domain_instance.get_translations_cache()) == {
            ("en_US", "messages"),
            ("de_DE", "messages"),
        }
        assert babel.gettext("Yes") == "Ja"
    assert load_mock.call_count == 4
