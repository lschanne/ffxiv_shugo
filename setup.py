from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="ffxiv_shugo",
    version="0.1",
    description="Shugo Boy's scripts and apps to assist in FFXIV adventuring.",
    long_description=long_description,
    author="Shugo Boy",
    # url="",
    packages=find_packages(),
    # packages=["ffixv_shugo"],
    # package_dir={"ffxiv_shugo": "src"},
    python_requires=">=3.9.5",
    install_requires=[
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3",
        "numpy==1.23.5",
        "pandas==1.5.3",
        "pyxivapi==0.5.1",
        "selenium==4.11.2",
        "streamlit==1.22.0",
    ],
)