# Authors: Dominik Zuercher, Valeria Glauser

import os

from setuptools import find_packages, setup

requirements = ["pyyaml", "pandas", "argparse", "pathlib", "numpy",
                "matplotlib", "PyHyphen", "frogress", "multiprocessing"]

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read().replace(".. :changelog", "")


PACKAGE_PATH = os.path.abspath(os.path.join(__file__, os.pardir))

setup(
    name="nice-plots",
    version="0.1.0",
    description="Automated generation of plots for survey data",
    long_description=open('README.rst').read(),
    author="Dominik Zuercher, Valeria Glauser",
    author_email="dominikzuercher@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    license="MIT License",
    zip_safe=False,
    keywords="nice-plots",
    classifiers=[
        'Development Status :: 3 - Alpha',
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points={
        'console_scripts': [
            "nice-plots = niceplots.main:main"
        ]
    }
)
