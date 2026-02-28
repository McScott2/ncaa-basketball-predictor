from setuptools import setup, find_packages

setup(
    name='football-beast',
    version='2.0.0',
    description='The most powerful football prediction engine - 8 market analysis with AI recommendations',
    author='Football Beast Team',
    author_email='dev@footballbeast.io',
    url='https://github.com/yourrepo/football-beast',
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'numpy>=1.24.3',
        'pandas>=2.0.3',
        'scikit-learn>=1.3.2',
        'xgboost>=2.0.0',
        'lightgbm>=4.0.0',
        'catboost>=1.2.2',
        'tensorflow>=2.13.0',
        'scipy>=1.11.0',
        'statsmodels>=0.14.0',
        'matplotlib>=3.7.2',
        'seaborn>=0.12.2',
        'plotly>=5.16.1',
        'joblib>=1.3.1',
        'python-dateutil>=2.8.2',
        'pytz>=2023.3'
    ],
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='football prediction betting ml ensemble',
    project_urls={
        'Bug Reports': 'https://github.com/yourrepo/football-beast/issues',
        'Source': 'https://github.com/yourrepo/football-beast',
    }
)
