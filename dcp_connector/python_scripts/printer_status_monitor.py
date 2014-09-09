import os
import sys
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)
from common import *
from django.core.mail import send_mail
from django.conf import settings

from time import sleep, strftime
import subprocess

def monitorPrinterStatus():
    params = {
        'printerid': PRINTER_ID,
        'extra_fields': 'connectionStatus'
    }
    while True:
        status = callAPI('printer', params)['printers'][0]['connectionStatus']
        if status != 'ONLINE':
            print "The printer is offline " + strftime("%Y-%m-%d %H:%M:%S")
            # send_mail('Duke Cloud Print is no longer online', 'The current status is ' + status,
            #           settings.EMAIL_HOST_USER,
            #           ['jixin.liao@gmail.com'])
            subprocess.call(['killall', 'connector'])
            subprocess.call(['screen', '-S', 'dcp', '-p', '0', '-X', 'stuff', './connector\n'])
            while callAPI('printer', params)['printers'][0]['connectionStatus'] != 'ONLINE':
                sleep(15)
            print "The printer is online " + strftime("%Y-%m-%d %H:%M:%S")
            # send_mail('Duke Cloud Print is back online', 'The current status is ' + status,
            #           settings.EMAIL_HOST_USER,
            #           ['jixin.liao@gmail.com'])
        sleep(15)


monitorPrinterStatus();