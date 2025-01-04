from setuptools import setup, find_packages
import os

# Read README.md content
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ditabase",
    version="0.1.0",
    packages=find_packages(),
    description="A Python library for data management with support for uniqueness constraints and item limits",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="José icaro",
    url="https://github.com/Icarogamer2441/ditabase",
    entry_points={
        'console_scripts': [
            'ditabase=ditabase.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 