from setuptools import setup, find_packages

setup(
    name="magicmedia",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pypdf2",
        "newspaper3k",
        "ebooklib",
        "openai",
        "google-generativeai",
        "pypandoc",
        "websocket-client",
        "json_repair",
        "tiktoken",
        "html2text",
        "python-dotenv"
    ],
)
