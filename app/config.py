import logging
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)


class Config:
    DB_HOST = "qa.example.com"
    DB_USER = "sa"


class DevConfig(Config):
    schema = 'v2board_dev'
    # 594269.xyz
    main_domain = '594269.xyz'



class ProdConfig(Config):
    # Load environment variables from .env file
    load_dotenv()
    # Get environment variables
    mysql_url = os.getenv("mysql_url")
    schema = os.getenv("mysql_schema")
    main_domain = os.getenv("cf_main_domain")
    zone_id = os.getenv("cf_zone_id")
    api_token = os.getenv("cf_api_token")
    users = {
        os.getenv("login_username"): generate_password_hash(os.getenv("login_password")),
    }


mapping = {
    'dev': DevConfig,
    'prod': ProdConfig
}

# 环境选择
APP_ENV = os.environ.get('APP_ENV', 'prod').lower()
cfg = mapping[APP_ENV]()

