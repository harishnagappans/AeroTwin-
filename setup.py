from setuptools import setup, find_packages

setup(
    name="aerotwin",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    py_modules=["actual", "twin", "detect", "rul", "engine"],
)
