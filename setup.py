#!/usr/bin/env python

from distutils.core import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='widlparser',
    version=widlparser.__version__,
    description=widlparser.__doc__,
    long_description=readme,
    long_description_content_type="text/markdown",
    author=widlparser.__author__[0],
    author_email=widlparser.__email__[0],
    maintainer=widlparser.__maintainer__,
    maintainer_email=widlparser.__email__[1],
    platforms=['any'],
    url=widlparser.__url__,
    packages=['widlparser'],
    zip_safe=False,
)
