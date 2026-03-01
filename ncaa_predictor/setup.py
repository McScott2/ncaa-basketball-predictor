"""
Setup configuration for NCAA Basketball Prediction Engine
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ncaa-basketball-predictor",
    version="1.0.0",
    author="Sports Analytics Team",
    description="Advanced ML system for NCAA basketball predictions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ncaa_predictor",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Sports"
    ],
    python_requires=">=3.9",
    install_requires=[
        "scikit-learn>=1.3.2",
        "numpy>=1.24.3",
        "pandas>=2.0.3",
        "xgboost>=2.0.0",
        "lightgbm>=4.0.0",
        "catboost>=1.2.2",
        "tensorflow>=2.13.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "scipy>=1.11.4",
        "joblib>=1.3.2"
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "jupyter>=1.0.0",
            "notebook>=7.0.0"
        ],
        "viz": [
            "matplotlib>=3.8.0",
            "seaborn>=0.13.0",
            "plotly>=5.17.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "ncaa-predict=ncaa_predictor.cli:main"
        ]
    }
)
