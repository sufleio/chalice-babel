import json
import os
import re
from contextlib import contextmanager
from datetime import datetime
from io import StringIO

from functools import cached_property
from chalice_babel.lazy_string import LazyString

from babel.messages.pofile import Catalog, read_po, write_po

# TODO: Exception Fix
try:
    import app as current_app
except ModuleNotFoundError:
    pass

from babel import Locale, dates, numbers, support
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pytz import UTC, timezone
from werkzeug.datastructures import ImmutableDict

accept_language_re = "([A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})*|\*)(?:\s*;\s*q=(0(?:\.[0-9]{,3})?|1(?:\.0{,3})?))?(?:\s*,\s*|$)"  # noqa: W605


class Babel(object):

    default_date_formats = ImmutableDict(
        {
            "time": "medium",
            "date": "medium",
            "datetime": "medium",
            "time.short": None,
            "time.medium": None,
            "time.full": None,
            "time.long": None,
            "date.short": None,
            "date.medium": None,
            "date.full": None,
            "date.long": None,
            "datetime.short": None,
            "datetime.medium": None,
            "datetime.full": None,
            "datetime.long": None,
        }
    )

    def __init__(
        self,
        app,
        default_locale="en",
        default_timezone="UTC",
        default_domain="messages",
        config=None,
        date_formats=None,
        configure_jinja=True,
    ):
        self.app = app
        self._default_locale = default_locale
        self._default_timezone = default_timezone
        self._default_domain = default_domain
        self._date_formats = date_formats
        self.locale_selector_func = None
        self.timezone_selector_func = None
        self.config = self.config_file()
        self._configure_jinja = configure_jinja

        if not hasattr(app, "chalice_babel"):
            app.chalice_babel = {}
        app.chalice_babel["babel"] = self
        if self._date_formats is None:
            self._date_formats = self.default_date_formats.copy()

        self.date_formats = self._date_formats

        if self._configure_jinja:

            env = Environment(
                loader=FileSystemLoader(os.getcwd() + "/chalicelib/templates"),
                autoescape=select_autoescape(),
                extensions=["jinja2.ext.i18n"],
            )
            app.chalice_babel["jinja2_env"] = env
            app.chalice_babel["jinja2_env"].filters.update(
                datetimeformat=format_datetime,
                dateformat=format_date,
                timeformat=format_time,
                timedeltaformat=format_timedelta,
                numberformat=format_number,
                decimalformat=format_decimal,
                currencyformat=format_currency,
                percentformat=format_percent,
                scientificformat=format_scientific,
            )
            app.chalice_babel["jinja2_env"].install_gettext_callables(
                lambda x: get_translations().ugettext(x),
                lambda s, p, n: get_translations().ungettext(s, p, n),
                newstyle=True,
            )

    def config_file(self):
        try:
            from chalicelib import babel_config

            config = babel_config
        except KeyError:
            config = {
                "BABEL_DEFAULT_LOCALE": self._default_locale,
                "BABEL_DEFAULT_TIMEZONE": self.default_timezone,
            }
        return config

    def localeselector(self, f):
        self.locale_selector_func = f
        return f

    def timezoneselector(self, f):
        self.timezone_selector_func = f
        return f

    def parse_language_header(self):
        request = self.app.current_request
        langs = request.headers["accept-language"]
        return langs

    def best_match(self, lang_string):
        result = []

        result = []
        pieces = re.match(f"{accept_language_re}", lang_string.lower(), re.VERBOSE)
        request_lang = pieces.groups()[0]
        config = self.app.chalice_babel["babel"].config
        supported_langs = config.get("LANGUAGES", self._default_locale)
        if request_lang in supported_langs:
            return request_lang
        return self._default_locale

    @property
    def default_locale(self):

        config = self.app.chalice_babel["babel"].config
        babel_default_locale = config.get("BABEL_DEFAULT_LOCALE", self._default_locale)
        return Locale.parse(babel_default_locale)

    @property
    def default_timezone(self):

        config = self.app.chalice_babel["babel"].config
        babel_default_timezone = config.get(
            "BABEL_DEFAULT_TIMEZONE", self._default_timezone
        )
        return timezone(babel_default_timezone)

    @property
    def domain(self):

        config = self.app.chalice_babel["babel"].config
        babel_domain = config.get("BABEL_DOMAIN", self._default_domain)
        return babel_domain

    @cached_property
    def domain_instance(self):

        config = self.app.chalice_babel["babel"].config
        babel_domain = config.get("BABEL_DOMAIN", self._default_domain)
        return Domain(domain=babel_domain)

    def list_translations(self):

        result = []

        for dirname in self.translation_directories:
            if not os.path.isdir(dirname):
                continue

            for folder in os.listdir(dirname):
                locale_dir = os.path.join(dirname, folder, "LC_MESSAGES")
                if not os.path.isdir(locale_dir):
                    continue

                if any(x.endswith(".mo") for x in os.listdir(locale_dir)):
                    result.append(Locale.parse(folder))

        if not result:
            result.append(Locale.parse(self._default_locale))

        return result

    @property
    def translation_directories(self):
        config = self.app.chalice_babel["babel"].config
        directories = config.get("BABEL_TRANSLATION_DIRECTORIES", "translations")
        for path in directories:
            if os.path.isabs(path):
                yield path
            else:
                yield os.path.join(os.getcwd() + "/chalicelib/", path)

    def export_strings(
        self,
        lang="en",
        domain="messages",
        translation_folder="translations",
        output_dir=None,
        filename="translation_strings",
    ):
        translations = os.path.join(os.getcwd() + "/chalicelib/", translation_folder)
        po_path = f"{translations}/{lang}/LC_MESSAGES/{domain}.po"
        source_str = StringIO(open(po_path, "r", encoding="utf-8").read())
        source_catalog = read_po(source_str)
        for_tron = {
            message.id: {lang: message.string}
            for message in source_catalog
            if message.id
        }

        for locale in self.list_translations():
            locale = locale.language
            if locale != lang:
                target_str = StringIO(
                    open(
                        translations + "/" + locale + "/LC_MESSAGES/" + domain + ".po",
                        "r",
                        encoding="utf-8",
                    ).read()
                )
                target_catalog = read_po(target_str)

                for message in target_catalog:
                    if message.id and message.id in for_tron.keys():
                        for_tron[message.id][locale] = message.string

        if not output_dir:
            translation_file = os.getcwd() + "/" + filename + ".json"
            with open(translation_file, "w", encoding="utf-8") as outfile:
                json.dump(for_tron, outfile, ensure_ascii=False, indent=4)

        else:
            translation_file = os.getcwd() + "/" + output_dir + "/" + filename + ".json"
            if not os.path.exists(os.path.dirname(translation_file)):
                try:
                    os.makedirs(os.path.dirname(translation_file))
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            with open(translation_file, "w", encoding="utf-8") as outfile:
                json.dump(for_tron, outfile, ensure_ascii=False, indent=4)

    def import_strings(
        self,
        filename="translation_strings",
        translation_folder="translations",
        input_dir=None,
        domain="messages",
    ):
        translations = os.path.join(os.getcwd() + "/chalicelib/", translation_folder)
        if input_dir:
            from_tron = json.loads(
                open(
                    os.getcwd() + "/" + input_dir + "/" + filename + ".json",
                    "r",
                    encoding="utf-8",
                ).read()
            )
        else:
            from_tron = json.loads(
                open(
                    os.getcwd() + "/" + filename + ".json", "r", encoding="utf-8"
                ).read()
            )

        template_str = StringIO(open(f"{domain}.pot", "r", encoding="utf-8").read())
        template = read_po(template_str)

        for locale in self.list_translations():
            locale = locale.language
            new_catalog = Catalog(fuzzy=False)
            for id in from_tron:
                if locale in from_tron[id].keys():
                    new_catalog.add(id, from_tron[id][locale])
            new_catalog.update(template)
            po_path = f"{translations}/{locale}/LC_MESSAGES/{domain}.po"
            write_po(open(po_path, "wb"), new_catalog)


@contextmanager
def force_locale(locale):
    ctx = current_app.app.chalice_babel
    ctx["babel_locale"] = getattr(ctx, "babel_locale", None)
    orig_attrs = {}
    orig_attrs["babel_locale"] = getattr(ctx, "babel_locale", None)

    try:
        ctx["babel_locale"] = Locale.parse(locale)
        ctx["forced_babel_locale"] = ctx["babel_locale"]
        yield
    finally:
        if "forced_babel_locale" in ctx:
            del ctx["forced_babel_locale"]

        for key, value in orig_attrs.items():
            ctx[key] = value


def get_locale():

    babel = current_app.app.chalice_babel["babel"]
    locale = current_app.app.chalice_babel.get("babel_locale", None)
    if locale is None:
        if babel.locale_selector_func is None:
            locale = babel.default_locale
        else:
            rv = babel.locale_selector_func()
            if rv is None:
                locale = babel.default_locale
            else:
                locale = Locale.parse(rv)
    return locale


def get_timezone():

    babel = current_app.app.chalice_babel["babel"]
    if babel.timezone_selector_func is None:
        tzinfo = babel.default_timezone
    else:
        rv = babel.timezone_selector_func()
        if rv is None:
            tzinfo = babel.default_timezone
        else:
            tzinfo = timezone(rv) if isinstance(rv, str) else rv
    return tzinfo


def format_decimal(number, format=None):

    locale = get_locale()
    return numbers.format_decimal(number, format=format, locale=locale)


def format_number(number):

    locale = get_locale()
    return numbers.format_decimal(number, locale=locale)


def format_currency(
    number, currency, format=None, currency_digits=True, format_type="standard"
):

    locale = get_locale()
    return numbers.format_currency(
        number,
        currency,
        format=format,
        locale=locale,
        currency_digits=currency_digits,
        format_type=format_type,
    )


def format_percent(number, format=None):

    locale = get_locale()
    return numbers.format_percent(number, format=format, locale=locale)


def format_scientific(number, format=None):

    locale = get_locale()
    return numbers.format_scientific(number, format=format, locale=locale)


def get_translations():

    return get_domain().get_translations()


def _get_format(key, format):
    babel = current_app.app.chalice_babel["babel"]
    if format is None:
        format = babel.date_formats[key]
    if format in ("short", "medium", "full", "long"):
        rv = babel.date_formats["%s.%s" % (key, format)]
        if rv is not None:
            format = rv
    return format


def to_user_timezone(datetime):
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    tzinfo = get_timezone()
    return tzinfo.normalize(datetime.astimezone(tzinfo))


def to_utc(datetime):
    if datetime.tzinfo is None:
        datetime = get_timezone().localize(datetime)
    return datetime.astimezone(UTC).replace(tzinfo=None)


def format_datetime(datetime=None, format=None, rebase=True):
    format = _get_format("datetime", format)
    return _date_format(dates.format_datetime, datetime, format, rebase)


def format_date(date=None, format=None, rebase=True):
    if rebase and isinstance(date, datetime):
        date = to_user_timezone(date)
    format = _get_format("date", format)
    return _date_format(dates.format_date, date, format, rebase)


def format_time(time=None, format=None, rebase=True):
    format = _get_format("time", format)
    return _date_format(dates.format_time, time, format, rebase)


def format_timedelta(
    datetime_or_timedelta, granularity="second", add_direction=False, threshold=0.85
):

    if isinstance(datetime_or_timedelta, datetime):
        datetime_or_timedelta = datetime.utcnow() - datetime_or_timedelta
    return dates.format_timedelta(
        datetime_or_timedelta,
        granularity,
        threshold=threshold,
        add_direction=add_direction,
        locale=get_locale(),
    )


def _date_format(formatter, obj, format, rebase, **extra):
    locale = get_locale()
    extra = {}
    if formatter is not dates.format_date and rebase:
        extra["tzinfo"] = get_timezone()
    return formatter(obj, format, locale=locale, **extra)


class Domain:
    def __init__(self, translation_directories=None, domain="messages"):
        if isinstance(translation_directories, str):
            translation_directories = [translation_directories]
        self._translation_directories = translation_directories
        self.domain = domain
        self.cache = {}

    def __repr__(self):
        return "<Domain({!r}, {!r})>".format(self._translation_directories, self.domain)

    @property
    def translation_directories(self):

        if self._translation_directories is not None:
            return self._translation_directories
        babel = current_app.app.chalice_babel["babel"]
        return babel.translation_directories

    def get_translations_cache(self):
        return self.cache

    def get_translations(self):
        cache = self.get_translations_cache()
        locale = get_locale()
        try:
            return cache[str(locale), self.domain]
        except KeyError:
            translations = support.Translations()

            for dirname in self.translation_directories:
                catalog = support.Translations.load(dirname, [locale], self.domain)
                translations.merge(catalog)
                if hasattr(catalog, "plural"):
                    translations.plural = catalog.plural

            cache[str(locale), self.domain] = translations
            return translations

    def gettext(self, string, **variables):

        t = self.get_translations()
        s = t.ugettext(string)
        return s if not variables else s % variables

    def ngettext(self, singular, plural, num, **variables):

        variables.setdefault("num", num)
        t = self.get_translations()
        s = t.ungettext(singular, plural, num)
        return s if not variables else s % variables

    def pgettext(self, context, string, **variables):

        t = self.get_translations()
        s = t.upgettext(context, string)
        return s if not variables else s % variables

    def npgettext(self, context, singular, plural, num, **variables):

        variables.setdefault("num", num)
        t = self.get_translations()
        s = t.unpgettext(context, singular, plural, num)
        return s if not variables else s % variables

    def lazy_gettext(self, string, **variables):

        return LazyString(self.gettext, string, **variables)

    def lazy_ngettext(self, singular, plural, num, **variables):

        return LazyString(self.ngettext, singular, plural, num, **variables)


def get_domain():
    babel = current_app.app.chalice_babel["babel"]
    babel_domain = babel.domain_instance
    return babel_domain


def gettext(*args, **kwargs):
    return get_domain().gettext(*args, **kwargs)


_ = gettext


def ngettext(*args, **kwargs):
    return get_domain().ngettext(*args, **kwargs)


def pgettext(*args, **kwargs):
    return get_domain().pgettext(*args, **kwargs)


def lazy_gettext(*args, **kwargs):
    return LazyString(gettext, *args, **kwargs)


def lazy_ngettext(*args, **kwargs):
    return LazyString(ngettext, *args, **kwargs)


def render_template(template_name, context={}):

    jinja2_env = current_app.app.chalice_babel["jinja2_env"]
    template = jinja2_env.get_or_select_template(template_name)
    return template.render(context)


def render_template_string(source, **context):

    jinja2_env = current_app.app.chalice_babel["jinja2_env"]
    template = jinja2_env.from_string(source)
    return template.render(context)
