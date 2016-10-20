
import logging
from logging import config

import os

base_dir = os.path.dirname(__file__)

token_file = os.path.join(base_dir, '.token')

bot_father_token = open(token_file).readlines()[0].strip()

db_path = os.path.join(base_dir, 'sqlite.db')

ssh_config = 'review'

gerrit_url_template = 'http://gerrit.tionix.loc/#/c/{change_id}/'

stikked_api_url = 'http://stikked.tionix.loc/api'

LOG_LEVEL = 'DEBUG'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s %(asctime)s %(message)s',
            'datefmt': '%m/%d/%Y %H:%M:%S',
        },
        'extended': {
            'format': '%(asctime)s - %(levelname)s - File: %(filename)s - '
                      '%(funcName)s() - Line: %(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
        },
        'keystoneclient': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
