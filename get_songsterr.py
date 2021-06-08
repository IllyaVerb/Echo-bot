import re, os, time, shutil
import requests as req

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

import HTML_To_PDF

def html_by_selenium():
	#opt = Options()
	#opt.add_argument("--disable-infobars")
	#opt.add_argument("--disable-extensions")
	#opt.add_argument("--headless")
	# Pass the argument 1 to allow and 2 to block
	#opt.add_experimental_option("prefs", { 
		#"profile.default_content_setting_values.media_stream_mic": 2, 
		#"profile.default_content_setting_values.media_stream_camera": 2,
		#"profile.default_content_setting_values.geolocation": 2, 
		#"profile.default_content_setting_values.notifications": 2 
	#})
	driver = webdriver.Chrome()#chrome_options=opt)
	driver.implicitly_wait(60)

	return driver


def browse_quit(driver):
	driver.quit()


def go_by_url(driver, url):
	driver.get(url)
	try:
		driver.find_element_by_xpath("//section[@id='tablature']")
	except NoSuchElementException:
		return ""

	last_height = int(driver.execute_script("return document.body.scrollHeight"))
	curr_height = 0
	while curr_height < last_height:
		driver.execute_script("window.scrollTo(0, {});".format(curr_height))
		time.sleep(0.1)
		curr_height += 50
	
	try:
		driver.find_element_by_xpath("(//section[@id='tablature']//*[@class='n'])[last()]//*")
	except NoSuchElementException:
		return ""

	return driver.page_source

def parse_sgstr(url):
	driver = html_by_selenium()
	page = go_by_url(driver, url)
	browse_quit(driver)

	path = 'songster_src/'
	css_path = re.findall('>\s<link href=\"\/(static.+)(\w{16}\.css)\"', page)
	path_2 = css_path[0][0]
	css_name = css_path[0][1]

	if not os.path.exists(path):
		os.makedirs(path)

	get_css = req.get('https://www.songsterr.com/' + path_2 + css_name, path + css_name).text

	for i, j in [('<section><div id=\"showroom\" .+\"Get Plus\" \/><\/a><\/div><\/div><\/section>', ''),
				 ('<section><div id=\"showroom\".+<\/div><\/div><\/section>', ''),
				 ('<div id=\"floating-controls-wrapper\" .+<\/div><\/aside><\/div><\/div>', ''),
				 ('<aside aria-controls=\"tablature\".+</aside>', ''),
				 ('<footer class=.+<\/a><\/div><\/footer>', ''),
				 ('<button id=\"favorite-toggle\".+<\/path><\/svg><\/button><\/div><h1', '</div><h1'),
				 ('<button id=\"revisions-toggle\".+<\/span><\/a>', '</div>'),
				 ('<nav id=\"tablist\" .+<\/nav>', ''),
				 ('<g vector-effect=.+<\/g>', ''),
				 ('<span aria-label="track.+<\/span>', ''),
				 ('<script defer src="\/stat.+><\/script>', ''),
				 ('<link rel="manifest" href="\/sta.+>', ''),
				 ('</h1><div .+<h2 ', '</h1> <h2 '),
				 ('>\s-\s<', '> - <'),
				 ('true\n<\/body>', '</body>'),
				 ('<link.+type="text\/css">', ''),
				 ('</svg><div class.+style=\"transform:(.+\n){14}.+</svg></div>', '</svg>'),
				 ('<section><div.+id=\"showroom\".+</div></section>', ''),
				 ('<div class=\"fc-consent-root\"(.*\n*)+$', '</body></html>'),
				 ('<\/head>', '<style>' + get_css + '</style></head>'),
				 ('content:\"Y[\w\' ]+page\";', ''),
				 ('{margin:0 \d+px 0 \d+px}@', '{}@'),
				 ('@media print', '@media nottt'),
				 ('@media screen', '@media all')]:
		page = re.sub(i, j, page)

	if len(re.findall('<section class=\"\w+\"><div class=\"\w+\">We use cookies.+<\/div><\/div><\/section>',
					  page)) > 0:
		page = re.sub('<section class=\"\w+\"><div class=\"\w+\">We use cookies.+<\/div><\/div><\/section>', '', page)

	cracked = re.findall('(:0}\.\w+:before{content:\").+(\";display:inline})', page)
	page = re.sub(':0}\.\w+:before{content:\".+\";display:inline}', cracked[0][0] + ' - ' + cracked[0][1], page)

	html_name = re.sub(r'(\\x[0-9a-f]{2})|([\\\/:\*\?\"<>\|])', '',
					   re.findall('<span aria-label=\"title\">(.+)<\/span><span aria-label=\"tab type', page)[0])
	page = re.sub('<title>.+</title>', '<title>'+html_name+'</title>', page)
	
	with open(path + html_name + '.html', 'w', encoding='utf-8') as f:
		f.write(page)

	HTML_To_PDF.HTML_To_PDF(path + html_name + '.html', html_name + '.pdf')
	
	shutil.rmtree(path)

	return html_name + '.pdf'
