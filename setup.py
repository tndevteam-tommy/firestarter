from setuptools import setup, find_packages

setup(
    name="firestarter",
    version="1.0.0",
    description="Firestarter: Thermodynamics & Bushcraft Physical Simulation Game",
    author="Thomas R. Nifong",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "moderngl>=5.8.2",
        "moderngl-window>=2.4.4",
        "pyglm>=2.7.0",
        "pygame-ce>=2.4.0",
        "pillow>=9.5.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "firestarter=main:main",
        ],
    },
)
