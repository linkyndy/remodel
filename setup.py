"""
remodel
----------------

Very simple yet powerful and extensible Object Document Mapper for RethinkDB, written in Python.

"""

from setuptools import setup, find_packages


setup(
    name='remodel',
    version='1.0.0',
    url='http://github.com/linkyndy/remodel',
    license='MIT',
    author='Andrei Horak',
    author_email='linkyndy@gmail.com',
    description='RethinkDB ODM',
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'rethinkdb>=2.4',
        'inflection',
        'six'
    ],
    extras_require={
        'dev': [
            'pytest'
        ]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
