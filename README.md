# Familjen scoreboard API

## Setup and running API
This assumes you run the API from VS code.
1. Install required packages with `pip install -r requirements.txt`
2. Create config file `instance\config.py`: Copy the `config.py.template` file and fill in the config values.
    * It is not necessary to fill in the email sender and SMTP config values for development.
3. Run the API by pressing <kbd>F5</kbd>

By default, the database will run in-memory, meaning that it will be reset with each restart of the API. To change this, edit the `SQLALCHEMY_DATABASE_URI` setting in the config file.

## API documentation
Swagger documentation for the API can be found in the root url, i.e. http://localhost:5000/
