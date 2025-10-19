from setuptools import setup, find_packages

setup(
    name="instagram-ai-bot",
    version="1.0.0",
    description="Instagram AI Bot with Cohere Integration",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "instagrapi==1.16.16",
        "requests==2.28.2",
        "python-dotenv==0.19.0",
        "pillow==9.5.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
