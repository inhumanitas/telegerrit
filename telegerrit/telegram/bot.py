
import telebot
from telebot import types

from telegerrit import settings
from telegerrit.telegram.setup import settings_list

bot = telebot.TeleBot(settings.bot_father_token)


def next_step_wrapper(fn):
    def wrapped(message):
        result = fn(message)
        msg = 'Stored' if result else 'Failed to store'
        bot.send_message(message.chat.id, msg,
                         reply_markup=types.ReplyKeyboardHide(selective=True))
        return result
    return wrapped


def process_step(message):
    setting = message.text
    for setting_obj in settings_list:
        if setting == setting_obj.name:
            if setting_obj.keyboard_options:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,
                                                   selective=True)
                markup.row(*setting_obj.keyboard_options)

                msg = bot.send_message(message.chat.id,
                                       "Select one of param editing:",
                                       reply_markup=markup)
            else:
                msg = bot.send_message(message.chat.id, "Enter value:")

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


# @bot.message_handler()
# def all_messages(message):
#     bot.send_message(message.chat.id, message.text.strip('/'))

def send_message(user_id, message):
    msg = message or u'Wrong message format'
    bot.send_message(user_id, msg)


if __name__ == '__main__':
    print 'Starting bot'
    bot.polling()
