from setuptools import setup, find_packages

setup(
    name="ELEMENTS-VENV",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pillow',
        'opencv-python',
        'pygame',
    ]
) 