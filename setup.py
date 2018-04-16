from setuptools import setup, find_packages

setup(
    name="mc_launcher_core",
    version="0.0.9",
    license="MIT",
    url="https://github.com/tfff1OFFICIAL/mc_launcher_core",
    install_requires=["unpack200>=1.0.1"],
    python_requires=">=3",
    project_urls={
        "Source": "https://github.com/tfff1OFFICIAL/mc_launcher_core"
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3'
    ],
    keywords="minecraft mod launcher",
    packages=find_packages(exclude=[".idea", "*.ignore*"]),
    py_modules=["mc_launcher_core"]
)
