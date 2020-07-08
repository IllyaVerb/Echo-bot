import config
import os, shutil, re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

import requests as req
import urllib.request
import random as rand
import math

from svglib.svglib import svg2rlg
import img2pdf
from reportlab.graphics import renderPDF
from PyPDF2 import PdfFileMerger

DEBUG = False


def cut_string(s, start, end):
	return ''.join(list(s)[start:end])


def parse_ms(url):
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


def parse_sgstr(url):
    def s4():
        return format(math.floor((rand.random()+1)*65536), 'x')[1:]

    page = req.get(url).text

    path = 'songster_src/'
    css_path = re.findall('>\s<link href=\"\/(static.+)(\w{16}\.css)\"', page)
    path_2 = css_path[0][0]
    css_name = css_path[0][1]

    if not os.path.exists(path):
        os.makedirs(path)
        
    get_css = req.get('https://www.songsterr.com/' + path_2 + css_name, path + css_name).text
    get_css = re.sub('@media print', '@media nottt', get_css)
    get_css = re.sub('@media screen', '@media all', get_css)

    for i, j in [('<section><div id=\"showroom\" .+\"Get Plus\" \/><\/a><\/div><\/div><\/section>', ''),
                 ('<section><div id=\"showroom\".+<\/div><\/div><\/section>', ''), 
                 ('<div id=\"floating-controls-wrapper\" .+<\/div><\/aside><\/div><\/div>', ''), 
                 ('<footer class=.+<\/a><\/div><\/footer>', ''),
                 ('<button id=\"favorite-toggle\".+<\/path><\/svg><\/button><\/div><h1', '</div><h1'),
                 ('<button id=\"revisions-toggle\".+<\/span><\/a>', '</div>'),
                 ('<nav id=\"tablist\" .+<\/nav>', ''),
                 ('<g vector-effect=.+<\/g>', ''),
                 ('<span aria-label="track.+<\/span>', ''),
                 ('<script defer src="\/stat.+><\/script>', ''),
                 ('<link rel="manifest" href="\/sta.+>', ''), 
                 ('>\s-\s<', '> - <'),
                 ('true\n<\/body>', '</body>'), 
                 ('<link.+type="text\/css">', ''),
                 ('<\/head>', '<style>' + get_css + '</style></head>')]:
        page = re.sub(i, j, page)

    if len(re.findall('<section class=\"\w+\"><div class=\"\w+\">We use cookies.+<\/div><\/div><\/section>', page)) > 0:
        page = re.sub('<section class=\"\w+\"><div class=\"\w+\">We use cookies.+<\/div><\/div><\/section>', '', page)

    cracked = re.findall('(:0}\.\w+:before{content:\").+(\";display:inline})', page)
    page = re.sub(':0}\.\w+:before{content:\".+\";display:inline}', cracked[0][0]+' - '+cracked[0][1], page)

    html_name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                       re.findall('<span aria-label=\"title\">(.+)<\/span><span aria-label=\"tab type', page)[0])
    with open(path + html_name + '.html', 'w', encoding='utf-8') as f:
        f.write(page)

    html_to_pdf = req.Session()

    get_token = html_to_pdf.get('https://deftpdf.com/html-to-pdf')

    token = re.findall('<input type="hidden" id="editor_csrf" value="(\w{40})">', get_token.text)[0]
    uuid = s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4()

    files = {
        'file': (path + html_name + '.html', page, 'text/html'),
        'UUID':(None, uuid),
        'path':(None, 'html-to-pdf'),
        '_token': (None, token),
        'pdf_password': (None, 'false')
    }
    upload_file = html_to_pdf.post('https://deftpdf.com/tool/upload', files=files)

    payload = {
        '_token': token, 
        'UUID': uuid, 
        'pageSize': 'a4', 
        'pageMargin': '', 
        'pageMarginUnits': 'px', 
        'pageOrientation': 'portrait', 
        'viewportWidth': '', 
        'pdf_password': 'false'
    }
    get_file_back = html_to_pdf.post('https://deftpdf.com/tool/html-to-pdf', data=payload)

    pdf_filename = re.findall('\"filename\":\"(\w+\.pdf)\"', get_file_back.text)[0]

    urllib.request.urlretrieve('https://deftpdf.com/storage/uploads/html-to-pdf/{}/{}'.format(uuid, pdf_filename), html_name + '.pdf')
    #shutil.rmtree(path)

    return (html_name + '.pdf', path + html_name + '.html')


def opus_to_mp3(url, num, name):
    opus_id = ''.join([rand.choice(list('0123456789abcdef')) for i in range(12)])
    files = {
        'file': (None, url), 
        'filelocation': (None, 'online'), 
        'target': (None, 'MP3'), 
        'bitrate': (None, '128k'),
        'frequency': (None, '0'), 
        'channel': (None, '0'),
        'type_converter': (None, 'audio')
    }
    opus_post = req.post('https://s1.fconvert.com/fconvert.php', files=files).text
    file_id = re.findall(r'\"id\":\"(\w+)\"', opus_post)[0]
    
    urllib.request.urlretrieve('https://s1.fconvert.com/upload/{}/'.format(file_id), name)
    return name


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi, I'm a bot musician, Aia!\n" +
                             "I am able to get notes/music/other files from sites: 'musescore.com' and 'songsterr.com'.\n" +
                             "You only need to send a link to the desired song and choose what is required.\n" +
                             "Have a good day!\U0001F609", reply_markup=ReplyKeyboardRemove())


def musescore(update, context):
    global database

    payload = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 
        'accept-encoding': 'gzip, deflate, br', 
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6', 
        'cache-control': 'max-age=0',
        'cookie': 'mu_browser_bi=6964977495583636453; mu_browser_uni=hMgRpBUL; _csrf=7AWIID0CFUX8OsbCcyrpsifAIvEK7BJa; _pro_abVar4=SEARCH_FORMULA_2020_06_13.A; _ym_d=1593460021; _ym_uid=1586382442146494383; _ga=GA1.2.1307497132.1593460021; first_visit_key=1; _ms_adScoreView=8; _ug_pUserHash=OLqTt_9uUKNlQo0pTvdkn.1593470999; _pro_abVar=PRO_OR_BASIC_2020_07_04.A; _mu_dc_regular=%7B%22v%22%3A3%2C%22t%22%3A1593945490%7D; mu_has_static_cache=1593945490; _ym_isad=1; _gid=GA1.2.273562683.1593945492; mu_payment_instant_only=1; onboard_closed_today=1; _pro_saved_button_id=1; _pro_saved_screen_width=1536; _pro_saved_screen_height=864; _identity=%5B35579397%2C%2224jW2YYVrTUvLqL-pfQHHjiiAaIBDKHDpgKruGsPUSCSJ2-Jh-ZGxCa_WIpKJIU2%22%2C864000%5D; _pro_saved_period=12; __stripe_mid=b3870a42-a151-4be2-a784-1cce6bd28bbc; _pro_saved_utm_campaign_id=688; _pro_buySession=73dc3924340f3630a2167b862ef719ba; _mu_landing_session=4; mscom_new=7d0ba8fc745d978cbf2726ebfd824fb8', 
        'sec-fetch-dest': 'document', 
        'sec-fetch-mode': 'navigate', 
        'sec-fetch-site': 'same-origin', 
        'sec-fetch-user': '?1', 
        'upgrade-insecure-requests': '1', 
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    }
    
    url = re.match('https?:\/\/musescore\.com\/((\w+)|(user\/\d+))\/scores\/\d+', update.message.text).group()
    
    first_get = req.get(url, headers=payload)
    if re.findall('\d{3}', str(first_get))[0] != '200':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Page not found.\U0001F6A7", reply_markup=ReplyKeyboardRemove())
        return
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select the format you want to download.",
                             reply_markup=ReplyKeyboardMarkup([['\U0001F4D6PDF', '\U0001F3A7MP3'], ['\U0001F3B9MIDI'], ['Musescore', 'MusicXML']],
                                                               one_time_keyboard=True, resize_keyboard=True))
        
    code = re.findall('https:\/\/musescore.com\/static\/musescore\/scoredata\/gen\/\d\/\d\/\d\/\d+\/\S{40}\/score_',
                        str(first_get.content))[0]
    name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                  cut_string(re.findall(r'title\" content=\".+\">\\n<meta property=\"og:url\"', str(first_get.content))[0], 16, -27))
    links = {i: 'https://musescore.com' + re.findall('\/score\/\d+\/download\/{}\?h=\d+'.format(i), str(first_get.content))[0]\
             for i in ['mscz', 'pdf', 'mxl', 'mid', 'mp3']}
    
    ms_handler = MessageHandler(Filters.regex('^((Musescore)|(\U0001F4D6PDF)|(MusicXML)|(\U0001F3B9MIDI)|(\U0001F3A7MP3))$'), musescore_file)
    
    if database.get(update.effective_chat.id) != None:
        dispatcher.remove_handler(database[update.effective_chat.id][1])
    dispatcher.add_handler(ms_handler)

    mscz_link = req.get(links['mscz'], headers=payload).url
    pdf_link= req.get(links['pdf'], headers=payload).url

    database[update.effective_chat.id] = [url, (ms_handler), {
                                                'Musescore': (mscz_link if len(re.findall('signin|forbidden', mscz_link)) == 0 else '', name + '.mscz'),
                                                '\U0001F4D6PDF': (pdf_link if len(re.findall('signin|forbidden', pdf_link)) == 0 else '', name + '.pdf'),
                                                'MusicXML': (cut_string(code, 0, -1) + '.mxl', name + '.mxl'),
                                                '\U0001F3B9MIDI': (cut_string(code, 0, -1) + '.mid', name + '.mid'),
                                                '\U0001F3A7MP3': ('https://nocdn.' + cut_string(code, 8, -1) + '.mp3', name + '.mp3')
    }]
        

def musescore_file(update, context):
    global database

    if database.get(update.effective_chat.id) != None:
        path = database[update.effective_chat.id][1][update.message.text][1]
        
        if database[update.effective_chat.id][1][update.message.text][0] != '':
            context.bot.send_message(chat_id=update.effective_chat.id, text="Wait a minute, your file is being processed.\U000023F3")
            urllib.request.urlretrieve(database[update.effective_chat.id][1][update.message.text][0], path)
            context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

            if os.path.exists(path):
                os.remove(path)
                
        elif update.message.text == '\U0001F4D6PDF':
            context.bot.send_message(chat_id=update.effective_chat.id, text="Wait a minute, your file is being processed.\U000023F3")
            path = parse_ms(database[update.effective_chat.id][0])
            context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

            if os.path.exists(path):
                os.remove(path)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I cannot get this file.\U0001F614")
            
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Send link first.", reply_markup=ReplyKeyboardRemove())


def songsterr(update, context):
    global database

    url = re.match('https?:\/\/(www\.)?songsterr\.com\/a\/wsa\/[\w\-]+', update.message.text).group()
    ask = req.get(url)
    page = ask.text

    if re.findall('\d{3}', str(ask))[0] != '200':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Page not found.\U0001F6A7", reply_markup=ReplyKeyboardRemove())
        return

    dict_instrument = {i+' - '+j: k for i, j, k in re.findall('\"name\":\"([\-\w\s()]+)\",\"instrument\":\"([\w\s\d()]+)\",\"partId\":(\d{1,2})', page)}
    
    keyboard_sgstr = [[i] for i in dict_instrument.keys()]
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select preffered instrument.",
                             reply_markup=ReplyKeyboardMarkup(keyboard_sgstr, one_time_keyboard=True, resize_keyboard=True))

    instr_handler = MessageHandler(Filters.regex('^(' + '|'.join(['('+re.sub('\(', '\\\(',
                                                                    re.sub('\)', '\\\)',
                                                                    re.sub('\-', '\\\-', i)))+')'
                                                                for i in dict_instrument.keys()]) + ')$'), songsterr_instrument)
    sgstr_handler = MessageHandler(Filters.regex('^((\U0001F4D6PDF)|(\U0001F399Slolo MP3)|(\U0001F3A7MP3)|(\U0001F519Back))$'), songsterr_file)
    
    if database.get(update.effective_chat.id) != None:
        for i in database[update.effective_chat.id][1]:
            dispatcher.remove_handler(i)
        
    dispatcher.add_handler(instr_handler)    
    dispatcher.add_handler(sgstr_handler)

    database[update.effective_chat.id] = [url, (instr_handler, sgstr_handler), dict_instrument, None]


def songsterr_instrument(update, context):
    global database

    database[update.effective_chat.id][3] = database[update.effective_chat.id][2][update.message.text]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select what you want to download.",
                             reply_markup=ReplyKeyboardMarkup([['\U0001F4D6PDF', '\U0001F399Slolo MP3'], ['\U0001F3A7MP3', '\U0001F519Back']],
                                                              one_time_keyboard=True, resize_keyboard=True))

def songsterr_file(update, context):
    global database

    if database.get(update.effective_chat.id) != None:
        if update.message.text != '\U0001F519Back':
            context.bot.send_message(chat_id=update.effective_chat.id, text="Wait a minute, your file is being processed.\U000023F3")
        url = re.sub('t\d{1,2}$', 't'+database[update.effective_chat.id][3], database[update.effective_chat.id][0])

        if update.message.text == '\U0001F4D6PDF':
            path = parse_sgstr(url)
            context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path[0], 'rb'))
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path[1], 'rb'))
            
            if os.path.exists(path[0]):
                os.remove(path[0])

        elif update.message.text == '\U0001F399Slolo MP3' or update.message.text == '\U0001F3A7MP3':
            main_page = req.get(url).text
            html_name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                               re.findall('<span aria-label=\"title\">(.+)<\/span><span aria-label=\"tab type', main_page)[0])
            
            song_id = re.findall('s(\d+)t', url)[0]
            revisionId = re.findall('\"revisionId\":(\d+)', main_page)[0]
            uuid = re.findall('\"audio\":\"([\w-]+)\"', main_page)[0]
            speed = re.findall('\"speed\":(\d+)', main_page)[0]
            song_type = 'f' if update.message.text == '\U0001F3A7MP3' else 's'
            
            opus_url = 'https://audio2.songsterr.com/{}/{}/{}/{}/{}/{}.opus'.format(song_id, revisionId, uuid, speed, song_type,
                                                                                    database[update.effective_chat.id][3])
            path = opus_to_mp3(opus_url, database[update.effective_chat.id][3],
                        html_name + ('_solo' if update.message.text == '\U0001F399Slolo MP3' else '') + '.mp3')
            
            context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))
            
            if os.path.exists(path):
                os.remove(path)

        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Select preffered instrument.",
                             reply_markup=ReplyKeyboardMarkup([[i] for i in database[update.effective_chat.id][2].keys()],
                                                              one_time_keyboard=True, resize_keyboard=True))
            
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Send link first.", reply_markup=ReplyKeyboardRemove())


database = {}

updater = Updater(token=config.token, use_context=True)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))

dispatcher.add_handler(MessageHandler(Filters.regex('https?:\/\/musescore\.com\/((\w+)|(user\/\d+))\/scores\/\d+'), musescore))

dispatcher.add_handler(MessageHandler(Filters.regex('https?:\/\/(www\.)?songsterr\.com\/a\/wsa\/[\w\-]+'), songsterr))

#dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))

if DEBUG:
    updater.start_polling()
else:
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get('PORT', '8443')),
                          url_path=config.token)
    updater.bot.set_webhook("https://testbot2202.herokuapp.com/" + config.token)

updater.idle()
