# coding: utf-8

from time import sleep
import logging

from telegerrit.telegram.bot import bot

logger = logging.getLogger(__name__)


def main():
    while True:
        logger.info('Starting bot')
        try:
            bot.polling()
        except Exception as e:
            logger.error(e)
            sleep(6)


if __name__ == '__main__':
    main()
