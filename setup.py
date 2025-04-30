"""Setup script for webexp package."""

import os
from setuptools import setup

setup(
    name='python-webflow-exporter',
    version=os.getenv("PACKAGE_VERSION", "0.0.0"),
    py_modules=['webexp'],
    install_requires=[
      'requests==2.32.3', 
      'argparse==1.4.0',
      'beautifulsoup4==4.13.4',
      'halo==0.0.31',
      'pylint==3.3.6',
      'setuptools==80.1.0'
    ],
    entry_points={
        'console_scripts': [
            'webexp = webexp:main'
        ]
    }
)
