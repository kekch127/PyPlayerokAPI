from setuptools import setup, find_packages


def readme():
    with open('README.md', 'r', encoding = 'utf-8') as f:
        return f.read()


def requires():
    with open('requirements.txt', 'r') as f:
        return f.read().splitlines()



setup(
    name = 'PyPlayerokAPI',
    version = '1.0.2',
    author = 'kekch127',
    description = 'Неофициальная асинхронная Python-библиотека для взаимодействия с торговой площадкой Playerok через GraphQL API и систему потоковых событий.',
    long_description = readme(),
    long_description_content_type='text/markdown',
    url = 'https://github.com/kekch127/PyPlayerokAPI',
    packages = find_packages(),
    install_requires = requires(),
    classifiers = [
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    keywords = 'python playerok playerokapi api websocket requests tls_requests curl_cffi',
    project_urls = {
        "Github": "https://github.com/kekch127"
    },
    python_requires = '>3.11'
)