import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # -----------------------
    # Flask
    # -----------------------
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'

    # -----------------------
    # Azure Blob Storage
    # -----------------------
    BLOB_ACCOUNT = os.environ.get('BLOB_ACCOUNT') or 'ENTER_STORAGE_ACCOUNT_NAME'
    BLOB_STORAGE_KEY = os.environ.get('BLOB_STORAGE_KEY') or 'ENTER_BLOB_STORAGE_KEY'
    BLOB_CONTAINER = os.environ.get('BLOB_CONTAINER') or 'ENTER_IMAGES_CONTAINER_NAME'

    # -----------------------
    # Azure SQL Database
    # -----------------------
    SQL_SERVER = os.environ.get('SQL_SERVER') or 'ENTER_SQL_SERVER_NAME.database.windows.net'
    SQL_DATABASE = os.environ.get('SQL_DATABASE') or 'ENTER_SQL_DB_NAME'
    SQL_USER_NAME = os.environ.get('SQL_USER_NAME') or 'ENTER_SQL_SERVER_USERNAME'
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD') or 'ENTER_SQL_SERVER_PASSWORD'

    # SQLAlchemy connection string (ODBC Driver 18)
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{SQL_USER_NAME}:{SQL_PASSWORD}"
        f"@{SQL_SERVER}:1433/{SQL_DATABASE}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes"
        "&TrustServerCertificate=no"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------
    # Microsoft Authentication (AAD)
    # -----------------------
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET") or "ENTER_CLIENT_SECRET_HERE"
    CLIENT_ID = os.environ.get("CLIENT_ID") or "ENTER_CLIENT_ID_HERE"

    AUTHORITY = "https://login.microsoftonline.com/common"
    REDIRECT_PATH = "/getAToken"
    SCOPE = ["User.Read"]

    SESSION_TYPE = "filesystem"
