#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from yaml import load
import subprocess
from time import sleep

SONDA_IP = "192.168.1.5"
KEY = "/home/adm720/.ssh/sonda"
USER = "adm720"

# Wrapper para la gestión del SSH
def ssh_conn(command):
    conn = subprocess.Popen(["ssh", "-i", KEY, "{}@{}".format(USER,SONDA_IP), command], shell=False, stdout=subprocess.PIPE)
    return conn.stdout.readlines()

# Función para obtener los datos de la señal
def parse_signal(data):
    # signal-strength=-42dBm@6Mbps
    # tx-signal-strength=-33dBm
    data = data.split('=')[1].split('@')[0]
    # Se quita dBm de detrás
    return int(data[:-3])

yml = None # Bases
# conf =
# {
#   sonda: 192.168.1.1,
#   key: "/home/adm720/.ssh",
#   user: "adm720"
# }
# bases = 
# {
#  "Base1": {
#    "ip": "xxx", 
#    "mac": {
#       "eth0": "xx:xx:xx:xx:xx:xx",
#       "wlan24": "xx:xx:xx:xx:xx:xx",
#       "wlan5": "xx:xx:xx:xx:xx:xx"
#       }
#   },
#   "Base2": {....}
# }

# Leer el fichero de configuración
with open("/etc/check_mk/checks/720tec_bases/bases.yml") as conf:
    yml = load(conf)

    # Cargar configuración o cargar por defecto
    try:
        SONDA_IP = yml['configuration']['sonda']
        KEY = yml['configuration']['key']
        USER = yml['configuration']['user']
    except:
        pass # Meh, ya esta todo asignado, solo evitar el error

# Datos
data = []

# Realizar la primera conexión SSH para activar la wifi de la sonda
ssh_conn("/interface wireless enable wlan1")

for base in yml:
    # Esta en el nodo de configuración, peta el diccionario por key error
    if base == "configuration":
        continue

    # Agregar la base a la connect list
    ssh_conn("/interface wireless connect-list set numbers=0 mac-address={}".format(yml[base]["mac"]["wlan5"]))
    
    sleep(20) # Duerme 20 secs. Se puede bajar un poco pero si hay bases lejos puede que no aparezca

    print("Recaba datos")

    # ssh -i /root/.ssh/id_dsa 10.20.0.10 -l admin "/interface wireless registration-table print stats" | grep signal-strength= | awk '{print $2}' | head -n1 > /tmp/b1-m1-ed    #(rx-signal)
    out = ssh_conn("/interface wireless registration-table print stats")
    # out es una lista de cada línea generada por el ssh
    
    # Trata datos, 0 valor por defecto.
    rx = 0
    tx = 0
    for opt in out:
        str_opt = opt.decode('utf-8')
        for i in str_opt.split(" "):
            if "tx-signal-strength=" in i:
                tx = parse_signal(i) # tx-signal-strength=-33dBm
            elif "signal-strength=" in i:
                rx = parse_signal(i) # signal-strength=-42dBm@6Mbps
    
    # Guarda los datos
    data.append((base, rx, tx))

# Fichero destino de donde leerá el check
# Esta al final para evitar que un check lo pille a mitad de lectura y no tenga todas las bases o este vacio.
with open("/tmp/bases.txt", 'w') as dest:
    for i in data:
        dest.write("{}:{},{}\n".format(i[0], i[1], i[2]))
    dest.close()