"""
interchange_regression_utilities
Utilities to help with running the interchange regression tests
"""
from setuptools import find_packages, setup

setup(
    name="interchange_regression_utilities",
    author="Open Force Field Consortium",
    author_email="info@omsf.org",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "create_openmm_systems=interchange_regression_utilities.commands."
            "create_openmm_systems:main",
            "compare_openmm_systems=interchange_regression_utilities.commands."
            "compare_openmm_systems:main",
        ],
    },
    python_requires=">=3.6",
)
