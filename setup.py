from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="conversational-emotion-ai",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A conversational AI that analyzes and responds to emotions in real-time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/conversational-emotion-ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "openai>=1.3.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.4.0",
        "pandas>=2.0.0",
        "plotly>=5.17.0",
        "httpx>=0.25.0",
        "PyYAML>=6.0.1",
        "python-multipart>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.1",
            "black>=23.7.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
            "types-PyYAML>=6.0.12",
            "types-requests>=2.31.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "emotion-ai=app:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
