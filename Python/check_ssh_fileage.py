#!/usr/bin/env python

import argparse
from sys import exit
from time import strptime, mktime
from datetime import datetime, timedelta

def get_data(user, host, file_check):
    from subprocess import Popen, PIPE
    def parse_date(data):
        # Output: 'Modify: 2016-10-18 17:41:25.646094044 +0200\n'
        split = data.split(" ")
        hour = split[2][:-10] # Para quitar los milisegundos
        date = split[1] + " " + hour

        time_struct = strptime(date, "%Y-%m-%d %H:%M:%S")
        date = datetime.fromtimestamp(mktime(time_struct))
        return date

    # Se conecta mediante SSH Keys
    proc = Popen(['ssh', user + "@" + host,'stat ' + file_check + '| grep Modify'], stdout=PIPE, stderr=PIPE)
    output, error = proc.communicate()
    status = proc.poll()
    if status != 0:
        return status
    return parse_date(output)

def check(date_to_check, threshold):
    status = 3
    status_str = ['OK', 'WARN', 'CRIT']
    today = datetime.now()

    td_warning = timedelta(days=int(threshold[0]))
    td_critical = timedelta(days=int(threshold[1]))
    td_result = today - modify_date


    if td_result < td_warning:
        status = 0
    elif td_result > td_critical:
        status = 2
    else:
        status = 1

    if status == 0:
        print "Ultima modificacion de {0} hace {1} dias, {2}|last={1};{3};{4};;".format(args.file, td_result.days, modify_date, threshold[0], threshold[1])
    elif status == 1:
        print "Ultima modificacion de {0} hace {1} dias, {2}. ({3})last={1};{3};{4};;".format(args.file, td_result.days, modify_date, threshold[0], threshold[1])
    else:
        print "Ultima modificacion de {0} hace {1} dias, {2}. ({4})last={1};{3};{4};;".format(args.file, td_result.days, modify_date, threshold[0], threshold[1])

    return status

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check to monitoring file/folder within an SSH connection')
    parser.add_argument('-f', '--file', action='store', help='File/Folder to check', required=True)
    parser.add_argument('-H', '--host', action='store', help='Host where is the file/folder. IP address or fqdn', required=True)
    parser.add_argument('-u', '--user', action='store', help='User to log in', required=True)
    parser.add_argument('-w', '--warning', action='store', help='Number of days to set warning value')
    parser.add_argument('-c', '--critical', action='store', help='Number of days to set critical value')
    args = parser.parse_args()

    modify_date = get_data(args.user, args.host, args.file)
    if isinstance(modify_date, datetime): # Comprobar si el objecto devuelto es un status o una fecha
        status = check(modify_date, [args.warning, args.critical])
        exit(status)
    else:
        print "Fallo conexion SSH"
        exit(2)
