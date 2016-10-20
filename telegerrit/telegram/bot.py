# coding: utf-8
import logging
import os
from random import randint

import telebot
from telebot import types

from telegerrit import settings
from telegerrit.stikked.api import stikked
from telegerrit.telegram.setup import settings_list

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(settings.bot_father_token)
brother_path = 'brother.txt'
answers = []


def next_step_wrapper(fn):
    def wrapped(message):
        result = fn(message)
        msg = 'Stored' if result else 'Failed to store'
        bot.send_message(message.chat.id, msg,
                         reply_markup=types.ReplyKeyboardHide(selective=True))
        return result
    return wrapped


def process_step(message):
    setting_name = message.text
    for setting_obj in settings_list:
        if setting_name == setting_obj.name:
            if setting_obj.keyboard_options:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,
                                                   selective=True)
                markup.row(*setting_obj.keyboard_options)

                msg = bot.send_message(message.chat.id,
                                       setting_obj.text,
                                       reply_markup=markup)
            else:
                msg = bot.send_message(message.chat.id, setting_obj.text)

            bot.register_next_step_handler(
                msg, next_step_wrapper(setting_obj.next_step))


@bot.message_handler(commands=['setup'])
def setup_command(message):
    """
    Configure params for bot
    :param message: /setup config_key value
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=True)
    markup.row(*map(unicode, settings_list))

    msg = bot.send_message(message.chat.id, "Select one of param editing",
                           reply_markup=markup)

    bot.register_next_step_handler(msg, process_step)


@bot.message_handler(commands=['ping'])
def ping(message):
    send_message(message.chat.id, 'pong')


@bot.message_handler(commands=['st'])
def sticked(message):
    def create_sticked(message):
        bot.send_message(message.chat.id, u'Погоди ...')
        bot.send_message(message.chat.id,
                         stikked.create_paste(message.text))

    msg = bot.send_message(message.chat.id, u"Кидай текст")
    bot.register_next_step_handler(msg, create_sticked)


@bot.message_handler(commands=['st_raw'])
def sticked_raw(message):
    def create_sticked(message):
        bot.send_message(message.chat.id, u'Погоди ...')
        bot.send_message(message.chat.id,
                         stikked.create_paste(message.text, raw=True))

    msg = bot.send_message(message.chat.id, u"Кидай текст")
    bot.register_next_step_handler(msg, create_sticked)


if os.path.exists(brother_path):
    with open(brother_path) as fh:
        answers = fh.readlines()
        answers = filter(bool, map(lambda s: s.strip(), answers))


@bot.message_handler()
def all_messages(message):
    BAD_WORDS = (
        u'дура',
        u'тупой', u'олень',
        u'дибил', u'идиот',
        u'брат', u'сестра'
    )
    brother = [u'брат', u'сестра']
    yourself = u"сам "
    message_text = message.text.lower()
    if (message_text.find(u'спасиб') >= 0 or
            message_text.find(u'спсб') >= 0 or message_text.find(u'спс') >= 0):
        bot.send_message(message.chat.id, u'Незашта, брат')
        return

    for bad_word in BAD_WORDS:
        if message_text.find(bad_word) >= 0:
            if bad_word in brother:
                message_text = message_text.encode('utf-8')
                if message_text not in answers:
                    with open(brother_path, 'w') as fh:
                        answers.append(message_text)
                        fh.write('\n'.join(answers))
                        logger.debug('new word: '+message_text)
                bot.send_message(
                    message.chat.id,
                    answers[randint(0, len(answers)-1)].capitalize())
                break
            else:
                bot.send_message(message.chat.id, yourself+bad_word)


def send_message(user_id, message):
    msg = message or u'Wrong message format'
    try:
        bot.send_message(user_id, msg)
    except Exception as e:
        logger.error(unicode(user_id) + unicode(e))


if __name__ == '__main__':
    logger.info('Starting bot')
    bot.polling()
