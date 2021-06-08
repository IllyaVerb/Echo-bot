import os, time, platform

class HTML_To_PDF:	
	def __init__(self, input_html, output_pdf):
		path_to_file = os.getcwd()

		if platform.system() == 'Windows':
			exec_file = 'start chrome'
		else:
			exec_file = os.getenv('GOOGLE_CHROME_BIN', 'google-chrome-stable')
			
		command_to_run = '{3} \
				--headless \
				--no-sandbox \
				--no-first-run \
				--disable-gpu \
				--print-to-pdf-no-header \
				--print-to-pdf="{0}/{1}" "{0}/{2}"'\
				.format(path_to_file, output_pdf, input_html, exec_file)
							
		#print('launch: ' + command_to_run)

		os.system(command_to_run)

		counter = 0
		while counter < 120:
			if os.path.exists("{}/{}".format(path_to_file, output_pdf)):
				break
			time.sleep(0.5)		
