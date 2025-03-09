"""
setup.py for the ss_roster2csv project.

This file works alongside your pyproject.toml. 
Many modern Python tools (like build, pip, etc.) can rely on pyproject.toml exclusively, 
but a setup.py can still be included for backwards compatibility or explicit usage.
"""

import setuptools

setuptools.setup(
    name="ss_roster2csv",
    version="0.1.0",
    description="Parse TU rosters from PDF or text into a CSV format.",
    author="Malik Koné",
    author_email="malik.kone@pm.me",
    packages=setuptools.find_packages(),
    python_requires=">=3.10",
    # if you have direct dependencies, they can go here:
    install_requires=[
        "pandas>=1.5",
        # "some-other-lib>=X.Y"
    ],
    # if you prefer classifiers:
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        # If you want a CLI entry point:
        "console_scripts": [
            "ss_roster2csv=ss_roster2csv.cli:main",
        ],
    },
)
