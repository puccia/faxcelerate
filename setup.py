import os, re
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
        _, l = l.rsplit('#', 1)
        name, version = l.rsplit('-', 1)
        l = '%s==%s' % (name, version)
    install_requires += [l]

def parse_requirements(file_name):
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements

def parse_dependency_links(file_name):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))

    return dependency_links

req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')

print '%r' % parse_requirements(req_file)
print '%r' % parse_dependency_links(req_file)

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
    #install_requires=install_requires,
    #dependency_links=dependency_links,
	install_requires=parse_requirements(req_file),
	dependency_links=parse_dependency_links(req_file),
)
