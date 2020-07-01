import config, os
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler, Filters


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def musescore(update, context):
    url = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text="Start creating pdf")

    context.bot.send_message(chat_id=update.effective_chat.id, text="Here is your notes")    


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


updater = Updater(token=config.token, use_context=True)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(RegexHandler('https?:\/\/musescore\.com\/user\/\d+\/scores\/\d+', musescore))

dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))

updater.start_webhook(listen="0.0.0.0",
                      port=int(os.environ.get('PORT', '8443')),
                      url_path=config.token)
updater.bot.set_webhook("https://testbot2202.herokuapp.com/" + config.token)
#updater.start_polling()
updater.idle()



#import telebot

#bot = telebot.TeleBot(config.token)

#@bot.message_handler(commands=['start'])
#def start_message(message):
#    bot.send_message(message.chat.id, 'Привет, ты написал мне /start')
    
#@bot.message_handler(content_types=["text"])
#def repeat_all_messages(message):
#    bot.send_message(message.chat.id, message.text)

#if __name__ == '__main__':
#    bot.remove_webhook()
#    bot.polling()
