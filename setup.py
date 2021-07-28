import os
from setuptools import setup

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, 'README.md')) as fh:
    long_description = fh.read()
with open(os.path.join(HERE, 'githubtest', '__init__.py')) as fh:
    version = fh.readline().split('"')[1]

setup(
    name='githubtest',
    version=version,
    url='https://github.com/damoti/githubtest',
    license='BSD',
    description='Testing framework for writing GitHub Apps in Python.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Lex Berezhny',
    author_email='lex@damoti.com',
    keywords='github,ci,unittest,integration',
    python_requires='>=3.8',
    packages=['githubtest'],
    install_requires=[
        'requests',
        'beautifulsoup4',
        'html5lib',
        'pyotp',
        'github3.py',
        'aiohttp',
        'python-slugify',
        'streamcontroller',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: Utilities',
    ],
)
