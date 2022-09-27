from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="snowreport",
        packages=find_packages(exclude=["snowreport_tests"]),
        install_requires=[
            "dagster",
            "pandas",
            "dagster-gcp",
            "google.cloud",
            "google-auth",
            "pandas_gbq"
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )
