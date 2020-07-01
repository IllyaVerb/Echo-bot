import requests as req
import os, shutil, re
import urllib.request

from svglib.svglib import svg2rlg
import img2pdf
from reportlab.graphics import renderPDF
from PyPDF2 import PdfFileMerger


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
    name = cut_string(re.findall('title\" content=\"[\w\s()]+\"', str(first_get.content))[0], 16, -1)
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



#parse('https://musescore.com/user/19587416/scores/4294486')
#parse('https://musescore.com/user/1809056/scores/1019991')
#parse('https://musescore.com/user/1995176/scores/6229568')
#parse('https://musescore.com/user/110540/scores/130329')
