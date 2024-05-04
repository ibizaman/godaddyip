from codecs import open as _open
from os import path

from setuptools import setup

HERE = path.abspath(path.dirname(__file__))
VERSION = "0.1.4"
PACKAGE = "godaddyip"

with _open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name=PACKAGE,
    version=VERSION,
    description="Maintains A and CNAME records matching current ip in Godaddy.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Pierre Penninckx",
    author_email="ibizapeanut@gmail.com",
    license="GPLv3",
    packages=[PACKAGE.lower()],
    url="https://github.com/ibizaman/" + PACKAGE.lower(),
    download_url="https://github.com/ibizaman/{}/archive/{}.tar.gz".format(
        PACKAGE.lower(), VERSION
    ),
    keywords=["godaddy", "dyndns"],
    entry_points={
        "console_scripts": ["{0}={0}.__main__:main".format(PACKAGE.lower())],
    },
    install_requires=[
        "requests==2.31.0",
        "pyyaml==6.0.1",
    ],
    extras_require={
        "test": ["black"],
    },
)
