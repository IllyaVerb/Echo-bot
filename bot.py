import config
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler, Filters

import requests as req
import os, shutil, re
import urllib.request

from svglib.svglib import svg2rlg
import img2pdf
from reportlab.graphics import renderPDF
from PyPDF2 import PdfFileMerger

DEBUG = False


def cut_string(s, start, end):
	return ''.join(list(s)[start:end])


def parse(url, context, chat_id):
    path = 'musicscore_tmp_img_src/'
    svg_arr = []
    png_arr = []
    pdf_arr = []
    
    first_get = req.get(url)
    code = re.findall('https:\/\/musescore.com\/static\/musescore\/scoredata\/gen\/\d\/\d\/\d\/\d+\/\S{40}\/score_',
                        str(first_get.content))[0]
    name = cut_string(re.findall('title\" content=\".+\">\n<meta', str(first_get.content))[0], 16, -8)
    if not os.path.exists(path):
        os.makedirs(path)
    for i in range(50):        
        if re.findall('\d{3}', str(req.get(code + str(i) + '.svg')))[0] == '200':
            svg_arr.append(str(i))
        if re.findall('\d{3}', str(req.get(code + str(i) + '.png')))[0] == '200':
            png_arr.append(str(i))

    if len(svg_arr) > len(png_arr):
        for i in svg_arr:
            urllib.request.urlretrieve(code + i + '.svg', path + i + '_img.svg')
            drawing = svg2rlg(path + i + '_img.svg')
            renderPDF.drawToFile(drawing, path + i + "_pdf.pdf")
            pdf_arr.append(path + i + "_pdf.pdf")
    else:
        for i in png_arr:
            urllib.request.urlretrieve(code + i + '.png', path + i + '_img.png')
            with open(path + i + "_pdf.pdf", "wb") as f:
                f.write(img2pdf.convert(path + i + '_img.png'))
            pdf_arr.append(path + i + "_pdf.pdf")

    merger = PdfFileMerger()

    for pdf in pdf_arr:
        merger.append(pdf)
    
    merger.write(name + ".pdf")
    merger.close()

    shutil.rmtree(path)
    return name + ".pdf"


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi, I'm a bot and my name is Aia!\nI can make PDF file with notes, from 'musescore.com'. Just send me link on it.\nHave a nice day!")


def musescore(update, context):
    url = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text="Start creating pdf. Wait a minute.")

    path = parse(url, context, update.effective_chat.id)

    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for using me.\nHere is your notes" + u'\U0001F3BC' + '.')
    context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

    if os.path.exists(path):
        os.remove(path)
    

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


updater = Updater(token=config.token, use_context=True)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(RegexHandler('https?:\/\/musescore\.com\/user\/\d+\/scores\/\d+', musescore))

#dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))

if DEBUG:
    updater.start_polling()
else:
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get('PORT', '8443')),
                          url_path=config.token)
    updater.bot.set_webhook("https://testbot2202.herokuapp.com/" + config.token)

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
