from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="snowreport",
        packages=find_packages(exclude=["snowreport_tests"]),
        install_requires=[
            "dagster",
            "dagit",
            "dagster-cloud",
            "dagster-k8s",
            "dagster-dbt",
            "pandas",
            "dagster-gcp",
            "google.cloud",
            "google-auth",
            "pandas_gbq",
            "dbt-bigquery"
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )
