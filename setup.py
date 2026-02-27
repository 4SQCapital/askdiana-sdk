from setuptools import setup, find_packages

setup(
    name="askdiana",
    version="0.3.0",
    packages=find_packages(),
    install_requires=["requests>=2.20.0", "python-dotenv>=0.19.0"],
    extras_require={
        "app": ["flask>=2.0"],
    },
    entry_points={
        "console_scripts": [
            "askdiana=askdiana.cli:main",
        ],
    },
    python_requires=">=3.8",
    description="Python SDK for the Ask DIANA Extension API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="4SQ Capital",
    url="https://github.com/4SQCapital/ask",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
