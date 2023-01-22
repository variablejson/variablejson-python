from setuptools import find_packages, setup

setup(
    name='variablejson',
    packages=find_packages(include=['variable_json']),
    version='0.1.0',
    description='JSON parser with in-JSON variables',
    author='Noah Davis',
    license='MIT',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)
