from setuptools import setup, find_packages

setup(
    name="personal_xpath_functions",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "lxml~=4.9.2",
        "lxml-stubs~=0.4.0",
        "w3lib~=2.1.1",
        "typeguard~=3.0.2",
        "typing_extensions~=4.5.0",
    ],
    author="Hitoshi Amano",
    author_email="seijro@gmail.com",
    description="personal used xpath funtions for me",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/amachang/personal-xpath-functions",
    classifiers=[],
)
