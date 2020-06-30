import config
import telebot
import os
from flask import Flask, request

bot = telebot.TeleBot(config.token)

server = Flask(__name__)

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, message.text)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, ты написал мне /start')

@server.route('/' + config.token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route('/', methods=["GET"])
def index():
    bot.remove_webhook()
    bot.set_webhook(url='https://testbot2202.herokuapp.com/' + config.token)
    return "!", 200

if __name__ == '__main__':
    #bot.remove_webhook()
    #bot.polling()
    #server.debug = True
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
