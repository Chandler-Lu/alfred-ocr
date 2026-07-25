# -*- coding: UTF-8 -*-
'''Packaging for alfred-ocr.

The Alfred workflow runs ``python src/main.py`` straight from the bundle and
needs no installation; this file exists for development installs and for
running the tool as ``alfred-ocr`` on the command line.
'''
from setuptools import find_packages, setup

with open('README.md', 'r', encoding='utf-8') as handle:
    LONG_DESCRIPTION = handle.read()

setup(
    name='alfred-ocr',
    version='5.0.0',
    description='Capture then OCR - Alfred for macOS, Quicker for Windows',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Chandler Lu',
    url='https://github.com/Chandler-Lu/alfred-ocr',
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    py_modules=['main', 'router'],
    python_requires='>=3.8',
    install_requires=['requests'],
    extras_require={
        'cnocr': ['cnocr[ort-cpu]'],
        'serve': ['cnocr[serve]'],
        'zxing': ['zxing-cpp', 'opencv-python'],
        'yaml': ['PyYAML'],
        'dev': ['pytest'],
    },
    entry_points={'console_scripts': ['alfred-ocr = main:main']},
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Graphics :: Capture',
    ],
)
