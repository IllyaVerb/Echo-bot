#import config
import telebot

bot = telebot.TeleBot('663214217:AAErqvYgKbeE1EYLBwh5b4Pds59d1jqltPY')#config.token)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, ты написал мне /start')

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, message.text)

#if __name__ == '__main__':

bot.polling()
