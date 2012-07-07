import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

install_requires = []
dependency_links = []
for l in open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines():
    l = l.strip()
    if '://' in l:
        dependency_links += [l]
    else:
        install_requires += [l]

setup(
    name = "faxcelerate",
    version = "0.1.1",
    author = "Emanuele Pucciarelli",
    author_email = "ep@corp.it",
    description = ("A Django-based web interface for HylaFAX."),
    license = "AGPL",
    keywords = "hylafax fax",
    url = "http://faxcelerate.com",
    packages=['faxcelerate'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Communications :: Fax",
        "License :: OSI Approved :: GNU Affero General Public License v3",
    ],
    install_requires=install_requires,
    dependency_links=dependency_links,
)
