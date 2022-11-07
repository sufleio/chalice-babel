# Chalice Babel

Chalice-Babel is a localization package inspired by Flask-Babel for AWS Chalice framework which is uses with help babel, pytz packages. Functionalty is the same like Flask-Babel but this package has a extra feature. You can add your translation strings without touching .po translation files help of export and import feature.

## Installation

``` bash
pip install chalice_babel
```

## Configuration

For the default configuration values you need to add `babel_config` json into `chalicelib/__init__.py` file like below example. If not specify Chalice-Babel will use default values below table.

```python
# __init__.py

babel_config = {
    "BABEL_DEFAUL_LOCALE": "en",
    "BABEL_DEFAUL_TIMEZONE": "UTC",
    "BABEL_TRANSLATION_DIRECTORIES": ["translations", "locale"],
    "BABEL_DOMAIN": "messages",
    "LANGUAGES": ["en", "tr"],
}

```

Chalice-Babel has the following configuration values that can be used to change some internal defaults:
| Key | Description |
| :--------: | :-------: |
| BABEL_DEFAUL_LOCALE | The default locale language when local selector function not used. Default value is `"en"`| 
| BABEL_DEFAUL_TIMEZONE | The default timezone when local timezone selector functiofunction used. Default value is `"UTC"`| 
| BABEL_TRANSLATION_DIRECTORIES | List of strings for translations folder names. Default value is `"transtalions"` | 
| BABEL_DOMAIN | The message domain used by the application. Defaults to `"messages"`. | 
| LANGUAGES | List of language strings you want to support |

## Usage

To use Chalice-Babel you need to give app you created to **Babel** object. Jinja support comes default **True** if you don't want to use jinja support you need to add configre_jinja = False to **Babel** object.

``` python
from chalice import Chalice
from chalice_babel import Babel

app = Chalice(app_name="chalice_babel")
babel = Babel(app)

@babel.localeselector
def get_locale():
    langs = babel.parse_language_header()
    return babel.best_match(langs)
```

Chalice-Babel uses local selector function returned language code to make translations possible so this decorator needs to be defined. If you need to localize something about time zones additionaly you need to define timezone selector decorator as well.

## Format Numbers

To format numbers you can use theese functions:

* format_number()
* format_decimal()
* format_currency()
* format_percent()
* format_scientific()

``` bash
>>> from chalice_babel import format_number
>>> return format_number(2022)
2,022
```

``` bash
>>> from chalice_babel import format_decimal
>>> return format_decimal(2.022)
2,022
```

``` bash
>>> from chalice_babel import format_currency
>>> return format_currency(2.022, "USD")
$2,022.00
```

``` bash
>>> from chalice_babel import format_percent
>>> return format_percent(20.22)
2,022%
```

``` bash
>>> from chalice_babel import format_scientific
>>> return format_scientific(20220000)
2.022E10
```


## Formatting Dates
To format dates you can use below functions. All of them uses datetime objects as first parameter and a format strings as second parameter.

* format_datetime()
* format_date()
* format_time()
* format_timedelta()

``` bash

>>> from chalice_babel import format_datetime
>>> from datetime import datetime

>>> format_datetime(datetime(1987, 3, 5, 17, 12))
Mar 5, 1987 5:12:00 PM

>>> format_datetime(datetime(1987, 3, 5, 17, 12), 'full')
Thursday, March 5, 1987 5:12:00 PM World (GMT) Time

>>> format_datetime(datetime(1987, 3, 5, 17, 12), 'short')
3/5/87 5:12 PM

>>> format_datetime(datetime(1987, 3, 5, 17, 12), 'dd mm yyy')
05 12 1987

```

## Translating Application

When it comes to translations this is why Chalice-Babel built. It is uses **gettext** together with **Python-Babel**. All you need to do import **gettext()** or **ngettext()** functions then mark strings or text using one of this functions you  want to be translated.
To translate singular strings you can use **gettext()** and if strings have plural form you can use **ngettext()**.


``` python
from chalice_babel import gettext, ngettext

gettext(u'A simple string')
gettext(u'Value: %(value)s', value=42)
ngettext(u'%(num)s Apple', u'%(num)s Apples', number_of_apples)
```

If you want to evaluate strings translation you can use **lazy_gettext()** function.

After mark all strings you want to translate it is time to create special template file called `.pot` that contains all the translated strings. 
Before the creating pot file you need to define `babel.cfg` configuration file next to your `app.py`, which is necessary to  use `pybabel` commands.


``` python

# babel.cfg
[python: **.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_

```

When you are ready it is time to extract translated strings to `.pot` file. You all need to do run the following `pybabel` command.


``` bash
pybabel extract -F babel.cfg -o messages.pot .
```


If you used `lazy_gettext()` function in your application you need to exract this translation strings using this `pybabel` command.


``` bash
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
```


Above commands will generate `messages.pot` file from `babel.cfg` configuration file. Now it is time to initialize first translation language.

First of all you should create `"en"` folder with first command below after that you are free to create other languages you want. This is nessary because `export` and `import` command will use this `"en"` folder as a default. This commands explained in the next section.



``` bash
 pybabel init -i messages.pot -d chalicelib/translations -l en

 pybabel init -i messages.pot -d chalicelib/translations -l de
```
 

`-d` translation folder which contains language folders. This folder should be located in `chalicelib` folder. The reason is Chalice packaging this folder when you deploy you application. It you create this folder outside of `chalicelib` folder translation will not work.
If you chooce another name then the `translations` you should add this name to `BABEL_TRANSLATION_DIRECTORIES` list in the configuration file.

After you generate your language folders you can edit `translations/{language_code}/LC_MESSAGES/messages.po`files to add your translation strings.

When you done with your translations only you need to compile translations with `pybabel compile` command.


``` bash
pybabel compile -d chalicelib/translations
```

When you changed marked strings or add new translation strings you need to update `messages.pot` file.


``` bash
 pybabel update -i messages.pot -d chalicelib/translations
```

End of this operations some strings can marked `fuzzy` in **.po** files. When this happen you need to check and fix manually this strings.

If you need more information for above commands and how **Babel** works you can checkout [babel](https://babel.pocoo.org/en/latest/) documentation

## Export & Import

When you have a large application with support for many languages, it means that your application contains a lot of strings and text that needs to be translated, and at some point it becomes a pain to manage and replace all those translation files. `"export_strings"` and `"import_strings"` commands makes this process easy to manage.

### Export

With help of `chalice_babel export_strings` command you can export all marked translation strings from `.po` files as a json file and you can easyly check which strings or texts translated correctly or not needs to be translated. 

``` bash
Usage: chalice_babel export_strings [options] [args]

Options:
  -l, --lang               source language for export translation strings, default "en"
  -D, --domain             domains of PO files, default "messages"
  -t, --translation_folder foldername to base directory containing the catalogs under chalicelib folder. Default "translations"
  -o, --output_dir         output path for translation strings json file. Default location is where app.py is located
  -f, --filename           translation strings json filename. Default "translation_strings"

```

For example if you have `"ja"` and `"de"` languages you wanted to support. Export command will generate json file like below.

```json
{
    "currency": {
        "en": "",
        "ja": "",
        "de": ""
    },
    "message": {
        "en": "",
        "ja": "メッセージ",
        "de": "Botschaft"
    },
    "Hello": {
        "en": "",
        "ja": "こんにちわ",
        "de": "Halo"
    }
}
```


### Import

If you generated your translation strings json file now you can edit this file to change or add translations. For example `"currency"` string didn't translated on above example. You can add translation strings for this key. After that when you run `chalice_babel import_strings` command this changes will implemented to corresponding `.po` files. End of this operation you should run `pybabel compile`.

``` bash
Usage: chalice_babel import_strings [options] [args]

Options:
  -D, --domain             domains of PO files, default "messages"
  -t, --translation_folder foldername to base directory containing the catalogs under chalicelib folder. Default "translations"
  -o, --input_dir          input path for translation strings json file. Default location is where app.py is located
  -f, --filename           translation strings json filename. Default "translation_strings"

```

## Contributing

Contributions are always welcome!

If you one to help us you can open your pr and we can discuss your new feature.
