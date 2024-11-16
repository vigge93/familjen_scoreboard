from setuptools import find_packages, setup

setup(
    name="familjen_scoreboard",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "Flask==3.1.0",
        "Flask-SQLAlchemy==3.1.1",
        "flask-restx==1.3.0",
        "gunicorn==21.2.0",
        "greenlet==3.0.3",
    ],
)
