import os, time, subprocess
import pdfkit

class HTML_To_PDF:    
    def __init__(self, input_html, output_pdf):
        path_to_file = os.getcwd()
        #name_of_file = output_pdf
        html_file = path_to_file + "/" + input_html  
        #page_to_open = "file:///" + html_file

        WKHTMLTOPDF_CMD = subprocess.Popen(['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf')], stdout=subprocess.PIPE).communicate()[0].strip()
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)
        
        pdfkit.from_file(html_file,  path_to_file + "/" + output_pdf, configuration=config)
        #command_to_run = '{0} \
        #                    --headless \
        #                    --no-sandbox \
        #                    --no-first-run \
        #                    --disable-gpu \
        #                    --print-to-pdf="{1}\{2}" "{3}"'\
        #                    .format(os.getenv('GOOGLE_CHROME_BIN'), path_to_file, name_of_file, page_to_open)
        #print('launch:'+command_to_run)

        #os.system(command_to_run)
        time.sleep(1)
        
