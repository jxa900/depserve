"""
flask-depserve
--------

Handles Kickstarting VMs in the dhcpd.conf file and presenting the dhcpd.conf file as JSON for other services to consume
"""

from setuptools import setup

setup(
    name='flask-depserve',
    version='0.1.0',
    url='https://github.com/ncicloudteam/depserve',
    license='BSD',
    author='Michael Chapman',
    author_email='michael.chapman@anu.edu.au',
    description='Handles Kickstarting VMs in the dhcpd.conf file and presenting the dhcpd.conf file as JSON for other services to consume',
    long_description=__doc__,
    py_modules=['depserve'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['Flask','gunicorn'],
)
