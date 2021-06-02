import os, time

class HTML_To_PDF:
    def __init__(self, input_html, output_pdf):
        path_to_file = os.getcwd()
        name_of_file = output_pdf
        html_file = os.getcwd() + "/" + input_html  
        page_to_open = "file:///" + html_file

        command_to_run = '{0} --headless --no-sandbox --no-first-run --disable-gpu --print-to-pdf-no-header --remote-debugging-port=9222 --print-to-pdf="{1}\{2}" "{3}"'.format(os.getenv('GOOGLE_CHROME_BIN'), path_to_file, name_of_file, page_to_open)
        print('launch:'+command_to_run)

        os.system(command_to_run)
        time.sleep(3)
        
