#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Nivel que se pone de limite para Critacal o OK
LEVEL = -87

# Funcion que realiza el inventario de los servicios, habrá un servicio por base.
def inventory_720tec_bases(info):
    # base;señalrx,señaltx
    for line in info:
        if line[0] == "Nofile!":
            # No hace inventario y para
            break

        # Consigue el nombre de la base y itera para que se cree un servicio por base
        base = line[0].split(':')[0]
        # DISCLAIMER: Hay que devolver una tupla, no se que coño significa o que puede implicar el None. No lo veo por ninguna parte de la documentación
        yield "Base_{}".format(base), None

# Funcion que realiza la comprobación e indica el estado del check.
# @return <status_code>, <mensaje>, <perf>
# perf es una lista de elementos de perf. <nombre>, <valor>, <nivelW>, <nivelC>, <min> <max>
def check_720tec_bases(item, params, info):
    for line in info:
        # Es para quitar este prefijo, no se si pasa o no
        if "Base_" in item:
            item = item[5:]

        if line[0] == "Nofile!":
            return 3, "File for data not found!"

        if line[0].split(':')[0] == item:
            # Estamos en la linea que tenenemos los datos para esta base
            rx, tx = line[0].split(':')[1].split(',')
            
            # Enteros para las comprobaciones
            rx = int(rx)
            tx = int(tx)

            # El perf, "" es vacio
            perf = [ ("rx", rx, "", LEVEL, -120, 120), ("tx", tx, "", LEVEL, -120, 120)]

            # No tiene señal UNK
            if rx == 0 or tx == 0:
                return 1, "No se recibe senyal - rx: {}dBm tx: {}dBm".format(rx, tx), perf
            # Niveles inferiores al LEVEL OK
            if rx > LEVEL and tx > LEVEL:
                return 0, "Senyal OK - rx: {}dBm tx: {}dBm".format(rx, tx), perf
            # Niveles superiores a LEVEL, this got serious CRIT
            if rx < LEVEL and tx < LEVEL:
                return 2, "Senyal CRIT - rx: {}dBm tx: {}dBm".format(rx,tx), perf
            # Uno de los dos niveles esta por encima del umbral WARN
            else:
                return 1, "Senyal WARN - rx: {}dBm tx: {}dBm".format(rx,tx), perf

    # No debería llegar aquí... algo fallo, revisa.
    return 3, "Algo fallo, {}".format(item)

# Características de este check basado en agente
check_info["720tec_bases"] = {
    'check_function': check_720tec_bases,
    'inventory_function': inventory_720tec_bases,
    'has_perfdata': True,
    'service_description': 'Senyal '
}
