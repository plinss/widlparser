"""Define PyPI package."""

import setuptools

with open('README.md', 'r') as readme_file:
	long_description = readme_file.read()

setuptools.setup(
	name='widlparser',
	version='0.0.0',  # version will get replaced by git version tag - do not edit
	author='Peter Linss',
	author_email='pypi@linss.com',
	description='WebIDL Parser',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/plinss/widlparser/',

	packages=['widlparser'],
	package_data={'widlparser': ['py.typed']},

	install_requires=[
		'typing-extensions>=3.7.4.1,<3.8',
	],
	extras_require={
		'dev': [
			'mypy<0.900',
			'flake8',
			'flake8-annotations',
			'flake8-bugbear',
			'flake8-commas',
			'flake8-continuation',
			'flake8-datetimez',
			'flake8-docstrings',
			'flake8-import-order',
			'flake8-literal',
			'flake8-noqa',
			'flake8-polyfill',
			'flake8-tabs',
			'flake8-type-annotations',
			'flake8-use-fstring',
			'pep8-naming',
		],
	},
	classifiers=[
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: MIT License',
		'Operating System :: OS Independent',
	],
	python_requires='>=3.7',
)
