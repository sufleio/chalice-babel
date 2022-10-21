import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()


setup(
    name="chalice_babel",
    version="1.0.0",
    author="Sufle",
    author_email="info@sufle.io",
    description="Chalice Babel Package",
    long_description_content_type="text/markdown",
    long_description=README,
    url="https://github.com/sufleio/chalice-babel",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "Babel>=2.10.3",
        "chalice>=1.26.6",
        "Jinja2>=3.1.2",
        "pytz>=2022.5",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-mock",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=False,
    entry_points="""
    [console_scripts]
    chalice_babel = chalice_babel.command.main:main
    
    [distutils.commands]
    import = chalice_babel.command.main:import_strings
    export_strings = chalice_babel.command.main:export_strings

    """,
)
