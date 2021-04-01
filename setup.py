from setuptools import setup, find_packages

from prism_api import __version__

setup(
    name='prism_api',
    version=__version__,
    packages=find_packages(),
    url='https://bitbucket.org/rexdev/prism-api',
    license='Copyright 2021 REX',
    author='REX Engineering',
    author_email='engineering@rexhomes.com',
    description=('API service for Prism'),
)
