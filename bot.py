import config
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup

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


def parse(url):
    path = 'musicscore_tmp_img_src/'
    svg_arr = []
    png_arr = []
    pdf_arr = []
    
    first_get = req.get(url)
    code = re.findall('https:\/\/musescore.com\/static\/musescore\/scoredata\/gen\/\d\/\d\/\d\/\d+\/\S{40}\/score_',
                        str(first_get.content))[0]
    name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                  cut_string(re.findall(r'title\" content=\".+\">\\n<meta property=\"og:url\"', str(first_get.content))[0], 16, -27))
    
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
    global database
    url = re.findall('https?:\/\/musescore\.com\/((\w+)|(user\/\d+))\/scores\/\d+', update.message.text)[0]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select the format you want to download.", replay_markup=markup)

    first_get = req.get(url)
    code = re.findall('https:\/\/musescore.com\/static\/musescore\/scoredata\/gen\/\d\/\d\/\d\/\d+\/\S{40}\/score_',
                        str(first_get.content))[0]
    name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                  cut_string(re.findall(r'title\" content=\".+\">\\n<meta property=\"og:url\"', str(first_get.content))[0], 16, -27))
    
    database[update.effective_chat.id] = (url, {
                                                'Musescore': ('', name + '.mscz'),
                                                'PDF': ('', name + '.pdf'),
                                                'MusicXML': (cut_string(code, 0, -1) + '.mxl', name + '.mxl'),
                                                'MIDI': (cut_string(code, 0, -1) + '.mid', name + '.mid'),
                                                'MP3': ('https://nocdn.' + cut_string(code, 8, -1) + '.mp3', name + '.mp3')
                                                })
        

def musescore_file(update, context):
    global database
    path = database[update.effective_chat.id][1][update.message.text][1]
    if database[update.effective_chat.id][1][update.message.text][0] != '':
        urllib.request.urlretrieve(database[update.effective_chat.id][1][update.message.text][0], path)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for using me.\nHere is your file" + u'\U0001F3BC' + '.')
        context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

        if os.path.exists(path):
            os.remove(path)


database = {}
buttons = ['Musescore', 'PDF', 'MusicXML', 'MIDI', 'MP3']

markup_small = ReplyKeyboardMarkup(list(map(lambda b: [b], buttons[1:])), one_time_keyboard=True, resize_keyboard=True)
markup = ReplyKeyboardMarkup(list(map(lambda b: [b], buttons)), one_time_keyboard=True, resize_keyboard=True)

updater = Updater(token=config.token, use_context=True)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.regex('https?:\/\/musescore\.com\/((\w+)|(user\/\d+))\/scores\/\d+'), musescore))
dispatcher.add_handler(MessageHandler(Filters.regex('^((Musescore)|(PDF)|(MusicXML)|(MIDI)|(MP3))$'), musescore_file))

#dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))

if DEBUG:
    updater.start_polling()
else:
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get('PORT', '8443')),
                          url_path=config.token)
    updater.bot.set_webhook("https://testbot2202.herokuapp.com/" + config.token)

updater.idle()
