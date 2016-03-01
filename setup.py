#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    print('[replot] setuptools not found.')
    raise

with open('replot/__init__.py') as fh:
    for line in fh:
        line = line.strip()
        if line.startswith('__VERSION__'):
            version = line.split()[-1][1:-1]
            break

try:
    from pip.req import parse_requirements
    from pip.download import PipSession
except ImportError:
    print('[replot] pip not found.')
    raise

# parse_requirements() returns generator of pip.req.InstallRequirement objects
parsed_requirements = parse_requirements("requirements.txt",
                                         session=PipSession())

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
install_requires = [str(ir.req) for ir in parsed_requirements]

setup(
    name='replot',
    version=version,
    url='https://github.com/Phyks/replot/',
    author='Phyks (Lucas Verney)',
    author_email='phyks@phyks.me',
    license='MIT License',
    description='A (sane) Python plotting module, abstracting on top of Matplotlib.',
    packages=['replot'],
    install_requires=install_requires
)
