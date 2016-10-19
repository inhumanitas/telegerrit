# coding: utf-8
from time import sleep

from telegerrit.telegram.bot import bot


def main():
    while True:
        try:
            bot.polling()
        except:
            sleep(6)


if __name__ == '__main__':
    main()
