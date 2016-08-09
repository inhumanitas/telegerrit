
import telebot
from telebot import types

import settings
from bot.setup.handlers import settings_list

bot = telebot.TeleBot(settings.token)

setup_cmd = 'setup'


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
            print len(setting_obj.keyboard_options)
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


@bot.message_handler(commands=[setup_cmd])
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


if __name__ == '__main__':
    bot.polling(none_stop=True)
