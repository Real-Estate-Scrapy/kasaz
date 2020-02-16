import os

BOT_NAME = 'kasaz'

SPIDER_MODULES = ['kasaz.spiders']
NEWSPIDER_MODULE = 'kasaz.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# DATABASE and PIPELINE
DATABASE = {
    'drivername': 'postgres',
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'username': os.environ.get('DB_USERNAME', 'user'),
    'password': os.environ.get('DB_PASSWORD', 'pwd'),
    'database': os.environ.get('DB_NAME', 'mydb')
}

ITEM_PIPELINES = {
   'kasaz.pipelines.PostgresDBPipeline': 330
}
