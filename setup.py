from distutils.core import setup
setup(
    name='githubtest',
    packages=['githubtest'],
    install_requires=[
        'requests',
        'beautifulsoup4',
        'html5lib',
        'pyotp',
        'github3.py',
    ]
)
