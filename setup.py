# -*- coding: utf-8 -*-
import re
import ast
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in frappe_graphql/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('frappe_graphql/__init__.py', 'rb') as f:
  version = str(ast.literal_eval(_version_re.search(
      f.read().decode('utf-8')).group(1)))

setup(
	name='frappe_graphql',
	version=version,
	description='GraphQL API Layer for Frappe Framework',
	author='Leam Technology Systems',
	author_email='info@leam.ae',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
