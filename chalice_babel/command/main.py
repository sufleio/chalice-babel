# # import app
import optparse
import os
import sys

sys.path.insert(0, os.getcwd())

from chalice_babel import Babel

from app import app

babel = Babel(app)


from chalice import Chalice


try:
    # See: https://setuptools.pypa.io/en/latest/deprecated/distutils-legacy.html
    from setuptools import Command as _Command

    try:
        from setuptools.errors import BaseError, OptionError, SetupError
    except ImportError:  # Error aliases only added in setuptools 59 (2021-11).
        OptionError = SetupError = BaseError = Exception

except ImportError:
    from distutils.cmd import Command as _Command
    from distutils.errors import DistutilsError as BaseError
    from distutils.errors import DistutilsSetupError as SetupError
    from distutils.errors import OptionError as OptionError


class Command(_Command):
    as_args = None

    multiple_value_options = ()
    boolean_options = ()
    option_aliases = {}
    option_choices = {}

    def __init__(self, dist=None):
        self.distribution = dist
        self.initialize_options()
        self._dry_run = None
        self.verbose = False
        self.force = None
        self.help = 0
        self.finalized = 0


class export_strings(Command):

    description = "export translation strings from .po files"
    user_options = [
        ("lang=", "l", "lang"),
        ("domain", "D", "domain"),
        ("translation_folder", "t", "translation folder"),
        ("output_dir", "o", "output dir"),
        ("filename", "f", "filename"),
    ]
    boolean_options = ["no-wrap"]

    def initialize_options(self):
        self.lang = "en"
        self.domain = "messages"
        self.output_dir = None
        self.translation_folder = "translations"
        self.filename = "translation_strings"

    def finalize_options(self):
        pass
        # raise OptionError('you must specify the input file')

    def run(self):

        babel.export_strings(lang=self.lang, domain=self.domain, translation_folder= self.translation_folder, output_dir=self.output_dir, filename=self.filename)


class import_strings(Command):

    description = "import translation strings from json file to .po files"
    user_options = [
        ("domain", "D", "domain"),
        ("translation_folder", "t", "translation folder"),
        ("input_dir", "i", "input dir"),
        ("filename", "f", "filename"),
    ]
    boolean_options = ["no-wrap"]

    def initialize_options(self):
        self.domain = "messages"
        self.translation_folder = "translations"
        self.input_dir = None
        self.filename = "translation_strings"

    def finalize_options(self):
        pass

    def run(self):
        babel.import_strings(domain=self.domain, translation_folder=self.translation_folder, input_dir=self.input_dir, filename=self.filename)


class CommandLineInterface(object):

    usage = "%%prog %s [options] %s"
    version = "%%prog %s" % "0.4"
    commands = {
        "import_strings": "import translations from json file to .po files",
        "export_strings": "exports translations to json from .po files",
    }

    command_classes = {
        "import_strings": import_strings,
        "export_strings": export_strings,
    }

    def run(self, argv=None):

        if argv is None:
            argv = sys.argv

        self.parser = optparse.OptionParser(usage=self.usage % ("command", "[args]"), version=self.version)
        self.parser.disable_interspersed_args()
        self.parser.print_help = self._help

        options, args = self.parser.parse_args(argv[1:])

        if not args:
            self.parser.error("no valid command or option passed. " "Try the -h/--help option for more information.")

        cmdname = args[0]
        if cmdname not in self.commands:
            self.parser.error('unknown command "%s"' % cmdname)

        cmdinst = self._configure_command(cmdname, args[1:])
        return cmdinst.run()

    def _help(self):
        print(self.parser.format_help())
        print("commands:")
        longest = max([len(command) for command in self.commands])
        format = "  %%-%ds %%s" % max(8, longest + 1)
        commands = sorted(self.commands.items())
        for name, description in commands:
            print(format % (name, description))

    def _configure_command(self, cmdname, argv):

        cmdclass = self.command_classes[cmdname]
        cmdinst = cmdclass()
        assert isinstance(cmdinst, Command)
        cmdinst.initialize_options()

        parser = optparse.OptionParser(usage=self.usage % (cmdname, ""), description=self.commands[cmdname])
        as_args = getattr(cmdclass, "as_args", ())
        for long, short, help in cmdclass.user_options:
            name = long.strip("=")
            default = getattr(cmdinst, name.replace("-", "_"))
            strs = ["--%s" % name]
            if short:
                strs.append("-%s" % short)
            strs.extend(cmdclass.option_aliases.get(name, ()))
            choices = cmdclass.option_choices.get(name, None)
            if name == as_args:
                parser.usage += "<%s>" % name
            elif name in cmdclass.boolean_options:
                parser.add_option(*strs, action="store_true", help=help)
            elif name in cmdclass.multiple_value_options:
                parser.add_option(*strs, action="append", help=help, choices=choices)
            else:
                parser.add_option(*strs, help=help, default=default, choices=choices)
        options, args = parser.parse_args(argv)

        if as_args:
            setattr(options, as_args.replace("-", "_"), args)

        for key, value in vars(options).items():
            setattr(cmdinst, key, value)

        try:
            cmdinst.ensure_finalized()
        except OptionError as err:
            parser.error(str(err))

        return cmdinst


def main():
    return CommandLineInterface().run(sys.argv)


if __name__ == "__main__":
    main()
