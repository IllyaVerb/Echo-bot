import certifi
import config
import img2pdf
import json
import math
import os
import random as rand
import re
import requests as req
import shutil
import time
import urllib.request

import get_songsterr

from PyPDF2 import PdfFileMerger
from mutagen.mp3 import MP3
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

DEBUG = False
COUNTING = config.counting
SILENCE = config.silence


def cut_string(s, start_idx, end_idx):
    return ''.join(list(s)[start_idx:end_idx])


def parse_ms(url):
    path = 'musicscore_tmp_img_src/'
    svg_arr = []
    png_arr = []
    pdf_arr = []

    first_get = req.get(url)
    code = re.findall('https:\/\/musescore.com\/static\/musescore\/scoredata\/gen\/\d\/\d\/\d\/\d+\/\S{40}\/score_',
                      str(first_get.text))[0]
    name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                  cut_string(
                      re.findall('title\" content=\".+\">\\n<meta property=\"og:url\"', str(first_get.text))[0], 16,
                      -27))

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


def rand_lett():
    return format(math.floor((rand.random() + 1) * 65536), 'x')[1:]


def opus_to_mp3(url, name):
    urllib.request.urlretrieve(url, name[:-4] + '.opus')
    command = 'ffmpeg -i "{}" -vn -ar 48000 -ac 2 -b:a 128k "{}"' \
        .format(name[:-4] + '.opus', name)
    os.system(command)

    if os.path.exists(name[:-4] + '.opus'):
        os.remove(name[:-4] + '.opus')

    return name


def add_countin(files):
    txt_file = "file '{}'\nfile '{}'".format(*files)
    with open('concat.txt', 'w') as f:
        f.write(txt_file)

    command = 'ffmpeg -f concat -safe 0 -i "{}" -c copy "{}"' \
        .format('concat.txt', files[1][:-4] + '_counting.mp3')
    os.system(command)

    if os.path.exists('concat.txt'):
        os.remove('concat.txt')

    return files[1][:-4] + '_counting.mp3'


def repair_mp3(path):
    command = 'ffmpeg -i "{}" -vn -ar 48000 -ac 2 -b:a 128k "{}"' \
        .format(path, path[:-4] + '_repair.mp3')
    os.system(command)
    if os.path.exists(path):
        os.remove(path)
    return path[:-4] + '_repair.mp3'


def insert_counting(path):
    command = 'ffmpeg -i "{}" -af "silenceremove=start_periods=1:start_duration=1:' \
              'start_threshold=-60dB:detection=peak,aformat=dblp" "{}"' \
        .format(path, path[:-4] + '_cropped.mp3')
    os.system(command)

    audio_main = MP3(path)
    audio_crop = MP3(path[:-4] + '_cropped.mp3')
    time_diff = audio_main.info.length - audio_crop.info.length

    if int(time_diff) > 0:
        crop_silence_cmd = 'ffmpeg -ss 0 -i "{}" -t {} -c copy "{}"' \
            .format(SILENCE, int(time_diff), SILENCE[:-4] + '_cropped.mp3')
        os.system(crop_silence_cmd)

        txt_file = "file '{}'\nfile '{}'\nfile '{}'" \
            .format(SILENCE[:-4] + '_cropped.mp3', COUNTING, path[:-4] + '_cropped.mp3')
    else:
        txt_file = "file '{}'\nfile '{}'" \
            .format(COUNTING, path[:-4] + '_cropped.mp3')

    with open('concat.txt', 'w') as f:
        f.write(txt_file)

    command = 'ffmpeg -f concat -safe 0 -i "{}" -c copy "{}"' \
        .format('concat.txt', path[:-4] + '_counting.mp3')
    os.system(command)

    if os.path.exists('concat.txt'):
        os.remove('concat.txt')

    if os.path.exists(SILENCE[:-4] + '_cropped.mp3'):
        os.remove(SILENCE[:-4] + '_cropped.mp3')

    if os.path.exists(path[:-4] + '_cropped.mp3'):
        os.remove(path[:-4] + '_cropped.mp3')

    return path[:-4] + '_counting.mp3'


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi, I'm a bot musician, Aia!\n" +
                                  "I am able to get notes/music/other files from sites: "
                                  "'musescore.com' and 'songsterr.com'.\n" +
                                  "You only need to send a link to the desired song, "
                                  "or select search button and then do what I say.\n" +
                                  "Have a good day!\U0001F609",
                             reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                              one_time_keyboard=True, resize_keyboard=True))


def musescore(update, context):
    global database

    payload = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                  'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, b',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
        'cache-control': 'max-age=0',
        'cookie': 'mu_browser_bi=6964977495583636453; mu_browser_uni=hMgRpBUL; _csrf=7AWIID0CFUX8OsbCcyrpsifAIvEK7BJa;'
                  ' _pro_abVar4=SEARCH_FORMULA_2020_06_13.A; _ym_d=1593460021; _ym_uid=1586382442146494383;'
                  ' _ga=GA1.2.1307497132.1593460021; first_visit_key=1; _ms_adScoreView=8;'
                  ' _ug_pUserHash=OLqTt_9uUKNlQo0pTvdkn.1593470999; _pro_abVar=PRO_OR_BASIC_2020_07_04.A;'
                  ' _mu_dc_regular=%7B%22v%22%3A3%2C%22t%22%3A1593945490%7D; mu_has_static_cache=1593945490;'
                  ' _ym_isad=1; _gid=GA1.2.273562683.1593945492; mu_payment_instant_only=1; onboard_closed_today=1;'
                  ' _pro_saved_button_id=1; _pro_saved_screen_width=1536; _pro_saved_screen_height=864;'
                  ' _identity=%5B35579397%2C%2224jW2YYVrTUvLqL-pfQHHjiiAaI'
                  'BDKHDpgKruGsPUSCSJ2-Jh-ZGxCa_WIpKJIU2%22%2C864000%5D; _pro_saved_period=12;'
                  ' __stripe_mid=b3870a42-a151-4be2-a784-1cce6bd28bbc; _pro_saved_utm_campaign_id=688;'
                  ' _pro_buySession=73dc3924340f3630a2167b862ef719ba; _mu_landing_session=4; '
                  'mscom_new=7d0ba8fc745d978cbf2726ebfd824fb8',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-use': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    }

    url = re.match('https?:\/\/musescore\.com\/((\w+)|(user\/\d+))\/scores\/\d+', update.message.text).group()

    first_get = req.get(url, headers=payload)
    if re.findall('\d{3}', str(first_get))[0] != '200':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Page not found.\U0001F6A7",
                                 reply_markup=ReplyKeyboardRemove())
        return

    context.bot.send_message(chat_id=update.effective_chat.id, text="Select the format you want to download.",
                             reply_markup=ReplyKeyboardMarkup([['\U0001F4D6PDF', '\U0001F3A7MP3'],
                                                               ['\U0001F3B9MIDI', 'MusicXML'],
                                                               ['Musescore', 'Main menu']],
                                                              one_time_keyboard=True, resize_keyboard=True))

    code = re.findall('https:\/\/musescore.com\/static\/musescore\/scoredata\/gen\/\d\/\d\/\d\/\d+\/\S{40}\/score_',
                      str(first_get.text))[0]
    name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                  cut_string(re.findall('title\" content=\".+\">\\n<meta property=\"og:url\"',
                                        str(first_get.text))[0], 16, -27))
    links = {i: 'https://musescore.com' + re.findall('\/score\/\d+\/download\/{}\?h=\d+'.format(i),
                                                     str(first_get.text))[0]
             for i in ['mscz', 'pdf', 'mxl', 'mid', 'mp3']}

    ms_handler = MessageHandler(Filters.regex('^((Musescore)|(\U0001F4D6PDF)|(MusicXML)|'
                                              '(\U0001F3B9MIDI)|(\U0001F3A7MP3))$'), musescore_file)

    if database.get(update.effective_chat.id) is not None:
        for i in database[update.effective_chat.id][1]:
            dispatcher.remove_handler(i)
    dispatcher.remove_handler(echo_handler)
    dispatcher.add_handler(ms_handler)
    dispatcher.add_handler(echo_handler)

    mscz_link = req.get(links['mscz'], headers=payload).url
    pdf_link = req.get(links['pdf'], headers=payload).url

    # 0 - URL
    # 1 - handlers list
    # 2 - dictionary between file type and link on it
    database[update.effective_chat.id] = [url, [ms_handler], {
        'Musescore': (mscz_link if len(re.findall('signin|forbidden', mscz_link)) == 0 else '', name + '.mscz'),
        '\U0001F4D6PDF': (pdf_link if len(re.findall('signin|forbidden', pdf_link)) == 0 else '', name + '.pdf'),
        'MusicXML': (cut_string(code, 0, -1) + '.mxl', name + '.mxl'),
        '\U0001F3B9MIDI': (cut_string(code, 0, -1) + '.mid', name + '.mid'),
        '\U0001F3A7MP3': ('https://nocdn.' + cut_string(code, 8, -1) + '.mp3', name + '.mp3')
    }]


def musescore_file(update, context):
    global database

    if database.get(update.effective_chat.id) is not None:
        path = database[update.effective_chat.id][2][update.message.text][1]

        if database[update.effective_chat.id][2][update.message.text][0] != '':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Wait a minute, your file is being processed.\U000023F3")
            urllib.request.urlretrieve(database[update.effective_chat.id][2][update.message.text][0], path)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

            if os.path.exists(path):
                os.remove(path)

        elif update.message.text == '\U0001F4D6PDF':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Wait a minute, your file is being processed.\U000023F3")
            path = parse_ms(database[update.effective_chat.id][0])
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

            if os.path.exists(path):
                os.remove(path)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I cannot get this file.\U0001F614")

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Send link first, or select search button.",
                                 reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                                  one_time_keyboard=True, resize_keyboard=True))


def songsterr(update, context, url=None):
    global database

    if url is None:
        url = re.match('https?:\/\/(www\.)?songsterr\.com\/a\/wsa\/[\w\-]+', update.message.text).group()

    ask = req.get(url)
    page = ask.text

    if re.findall('\d{3}', str(ask))[0] != '200':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Page not found.\U0001F6A7",
                                 reply_markup=ReplyKeyboardRemove())
        return

    dict_instrument = {i + ' - ' + j: k for i, j, k in
                       re.findall('\"name\":\"([\-\w\s()]+)\",\"instrument\":\"([\w\s\d()]+)\",\"partId\":(\d{1,2})',
                                  page)}

    keyboard_sgstr = [[i] for i in dict_instrument.keys()]
    keyboard_sgstr.append(['Main menu'])

    context.bot.send_message(chat_id=update.effective_chat.id, text="Select preffered instrument.",
                             reply_markup=ReplyKeyboardMarkup(keyboard_sgstr,
                                                              one_time_keyboard=True, resize_keyboard=True))

    instr_handler = MessageHandler(Filters.regex('^(' + '|'.join(['(' + re.sub('\(', '\\\(',
                                                                               re.sub('\)', '\\\)',
                                                                                      re.sub('\-', '\\\-', i))) + ')'
                                                                  for i in dict_instrument.keys()]) + ')$'),
                                   songsterr_instrument)
    sgstr_handler = MessageHandler(Filters.regex(
        '^((\U0001F4D6PDF)|(\U0001F399Solo MP3)|(\U0001F3A7MP3)|(\U0001F507Muted MP3)|(\U0001F519Back))$'),
                                   songsterr_file)
    props_handler = MessageHandler(Filters.regex('^((Common)|(\U0001F941Counting)|(Metronome)|(\U0001F519Back))$'),
                                   songsterr_music_props)

    if database.get(update.effective_chat.id) is not None:
        for i in database[update.effective_chat.id][1]:
            dispatcher.remove_handler(i)

    dispatcher.remove_handler(echo_handler)
    dispatcher.add_handler(instr_handler)
    dispatcher.add_handler(echo_handler)

    # 0 - URL
    # 1 - handlers list
    # 2 - instrument dictionary
    # 3 - chosen instrument
    # 4 - MP3 type
    database[update.effective_chat.id] = [url, [instr_handler, sgstr_handler, props_handler], dict_instrument, None,
                                          None]


def songsterr_instrument(update, context):
    global database

    dispatcher.remove_handler(database[update.effective_chat.id][1][0])
    dispatcher.remove_handler(echo_handler)
    dispatcher.add_handler(database[update.effective_chat.id][1][1])
    dispatcher.add_handler(echo_handler)

    database[update.effective_chat.id][3] = database[update.effective_chat.id][2][update.message.text]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select what you want to download.",
                             reply_markup=ReplyKeyboardMarkup([['\U0001F4D6PDF', '\U0001F399Solo MP3'],
                                                               ['\U0001F3A7MP3', '\U0001F507Muted MP3'],
                                                               ['\U0001F519Back']],
                                                              one_time_keyboard=True, resize_keyboard=True))


def songsterr_file(update, context):
    global database

    if database.get(update.effective_chat.id) is not None:
        if update.message.text == '\U0001F4D6PDF':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Wait a minute, your file is being processed.\U000023F3")
        url = re.sub('t\d{1,2}$', 't' + database[update.effective_chat.id][3], database[update.effective_chat.id][0])

        if update.message.text == '\U0001F4D6PDF':
            path = get_songsterr.parse_sgstr(url)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

            if os.path.exists(path):
                os.remove(path)

        elif update.message.text in ['\U0001F399Solo MP3', '\U0001F507Muted MP3', '\U0001F3A7MP3']:
            dispatcher.remove_handler(database[update.effective_chat.id][1][1])
            dispatcher.remove_handler(echo_handler)
            dispatcher.add_handler(database[update.effective_chat.id][1][2])
            dispatcher.add_handler(echo_handler)

            database[update.effective_chat.id][4] = update.message.text

            context.bot.send_message(chat_id=update.effective_chat.id, text="Select song properties.",
                                     reply_markup=ReplyKeyboardMarkup([['Common', '\U0001F519Back'],
                                                                       ['\U0001F941Counting', 'Metronome']],
                                                                      one_time_keyboard=True, resize_keyboard=True))

        else:
            dispatcher.remove_handler(database[update.effective_chat.id][1][1])
            dispatcher.remove_handler(echo_handler)
            dispatcher.add_handler(database[update.effective_chat.id][1][0])
            dispatcher.add_handler(echo_handler)

            keyboard_back = [[i] for i in database[update.effective_chat.id][2].keys()]
            keyboard_back.append(['Main menu'])

            context.bot.send_message(chat_id=update.effective_chat.id, text="Select preffered instrument.",
                                     reply_markup=ReplyKeyboardMarkup(keyboard_back,
                                                                      one_time_keyboard=True, resize_keyboard=True))

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Send link first, or select search button.",
                                 reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                                  one_time_keyboard=True, resize_keyboard=True))


def songsterr_music_props(update, context):
    global database

    if database.get(update.effective_chat.id) is not None:
        if update.message.text != '\U0001F519Back':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Wait a minute, your file is being processed.\U000023F3")
        url = re.sub('t\d{1,2}$', 't' + database[update.effective_chat.id][3], database[update.effective_chat.id][0])

        if update.message.text == 'Common' or \
                update.message.text == '\U0001F941Counting' or \
                update.message.text == 'Metronome':
            main_page = req.get(url).text
            html_name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
                               re.findall('<span aria-label=\"title\">(.+)<\/span><span aria-label=\"tab type',
                                          main_page)[0])

            song_id = re.findall('s(\d+)t', url)[0]
            revision_id = re.findall('\"revisionId\":(\d+)', main_page)[0]
            uuid = re.findall('\"audio\":\"([\w-]+)\"', main_page)[0]
            speed = re.findall('\"speed\":(\d+)', main_page)[0]
            song_type = 'f'
            if database[update.effective_chat.id][4] == '\U0001F507Muted MP3':
                song_type = 'm'
            elif database[update.effective_chat.id][4] == '\U0001F399Solo MP3':
                song_type = 's'

            opus_url = 'https://audio2.songsterr.com/{}/{}/{}/{}/{}/{}.opus'\
                .format(song_id, revision_id, uuid, speed, song_type, database[update.effective_chat.id][3])
            path = opus_to_mp3(opus_url,
                               html_name + (
                                   '_solo' if database[update.effective_chat.id][4] == '\U0001F399Solo MP3' else '')
                               + ('_mute' if database[update.effective_chat.id][4] == '\U0001F507Muted MP3' else '')
                               + '.mp3')

            if update.message.text == '\U0001F941Counting':
                path_2 = insert_counting(path)
                if os.path.exists(path):
                    os.remove(path)
                path = path_2

            elif update.message.text == 'Metronome':
                context.bot.send_message(chat_id=update.effective_chat.id, text="Now I cannot create it.\U0001F6A7")

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Thank you for using me.\nHere is your file.\U0001F4CE")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(path, 'rb'))

            if os.path.exists(path):
                os.remove(path)

        else:
            dispatcher.remove_handler(database[update.effective_chat.id][1][2])
            dispatcher.remove_handler(echo_handler)
            dispatcher.add_handler(database[update.effective_chat.id][1][1])
            dispatcher.add_handler(echo_handler)

            context.bot.send_message(chat_id=update.effective_chat.id, text="Select what you want to download.",
                                     reply_markup=ReplyKeyboardMarkup([['\U0001F4D6PDF', '\U0001F399Solo MP3'],
                                                                       ['\U0001F3A7MP3', '\U0001F507Muted MP3'],
                                                                       ['\U0001F519Back']],
                                                                      one_time_keyboard=True, resize_keyboard=True))

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Send link first, or select search button.",
                                 reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                                  one_time_keyboard=True, resize_keyboard=True))


def songsterr_search_start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Enter your search query.",
                             reply_markup=ReplyKeyboardRemove())

    if database.get(update.effective_chat.id) is not None:
        for i in database[update.effective_chat.id][1]:
            dispatcher.remove_handler(i)

    # 0 - potential URL
    # 1 - handlers list
    # 2 - response list
    # 3 - response key
    database[update.effective_chat.id] = ['-1', [], None, None]


def songsterr_search(update, context):
    global database

    search_get = req.get('https://www.songsterr.com/api/songs', params={
        'pattern': update.message.text,
        'size': '100'
    })
    response = json.loads(search_get.text)

    if len(response) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No tabs found.",
                                 reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                                  one_time_keyboard=True, resize_keyboard=True))
    else:
        search_key_dict = {i['artist'] + ' - ' + i['title']: response.index(i) for i in response}
        search_handler = MessageHandler(
            Filters.regex('^(' + '|'.join(['(' + re.sub('\(', '\\\(',
                                                        re.sub('\)', '\\\)',
                                                               re.sub('\.', '\\\.',
                                                                      re.sub('\-', '\\\-', i)))) + ')'
                                           for i in search_key_dict.keys()]) + ')$'),
            search_to_link)

        keyboard_search_vars = [[i] for i in search_key_dict.keys()]
        keyboard_search_vars.append(['Main menu'])

        context.bot.send_message(chat_id=update.effective_chat.id, text="Select the desired song.",
                                 reply_markup=ReplyKeyboardMarkup(keyboard_search_vars,
                                                                  one_time_keyboard=True, resize_keyboard=True))

        dispatcher.remove_handler(echo_handler)
        dispatcher.add_handler(search_handler)
        dispatcher.add_handler(echo_handler)
        database[update.effective_chat.id][1].append(search_handler)
        database[update.effective_chat.id][2] = response
        database[update.effective_chat.id][3] = search_key_dict


def search_to_link(update, context):
    global database

    song_dict = database[update.effective_chat.id][2][database[update.effective_chat.id][3][update.message.text]]
    url = 'https://www.songsterr.com/a/wsa/' + song_dict['artist'].lower() +\
          '-' + re.sub('[(),.\'\-]', '', re.sub(' ', '\-', song_dict['title'].lower())) + '-tab-s' +\
          str(song_dict['songId']) + 't' + str(song_dict['defaultTrack'])
    songsterr(update, context, url=url)


def main_menu(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the start menu.",
                             reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                              one_time_keyboard=True, resize_keyboard=True))


def echo(update, context):
    global database

    if database.get(update.effective_chat.id) is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Send link first, or select search button.",
                                 reply_markup=ReplyKeyboardMarkup([['\U0001F50DSearch in songsterr.com']],
                                                                  one_time_keyboard=True, resize_keyboard=True))
    else:
        if database[update.effective_chat.id][0] == '-1':
            songsterr_search(update, context)


database = {}

updater = Updater(token=config.token, use_context=True)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))

dispatcher.add_handler(
    MessageHandler(Filters.regex('https?:\/\/musescore\.com\/((\w+)|(user\/\d+))\/scores\/\d+'), musescore))
dispatcher.add_handler(MessageHandler(Filters.regex('https?:\/\/(www\.)?songsterr\.com\/a\/wsa\/[\w\-]+'), songsterr))

dispatcher.add_handler(MessageHandler(Filters.regex('^\U0001F50DSearch in songsterr\.com$'), songsterr_search_start))
dispatcher.add_handler(MessageHandler(Filters.regex('^Main menu$'), main_menu))

echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

if DEBUG:
    updater.start_polling()
else:
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get('PORT', '8443')),
                          url_path=config.token)
    updater.bot.set_webhook("https://testbot2202.herokuapp.com/" + config.token)

updater.idle()
