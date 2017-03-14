#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author: Borja Blasco García <bblasco@720tec.es>
# Check para comprobar el estados de las bris de un patton mediante SNMP
# El check debe estar situado en /omd/sites/<site>/local/share/check_mk/checks y el mismo ya lo reconoce al inventariar servicios.

def inventory_bris(info):
    for nic, typ, state in info:
        if typ == "63" and state == "1":
            if "BRI" in nic:
                yield nic, None

def checks_bris(item, params, info):
    for nic, typ, state in info:
        if nic == item:
            if state == "1":
                return 0, "OK - BRI is up"
            else:
                return 2, "CRITICAL - BRI is down"
    return (3, "UNK - something failed")

check_info["bri_patton"] = {
    "check_function":   checks_bris,
    "inventory_function":   inventory_bris,
    "service_description":  "%s",
    "snmp_info":    (".1.3.6.1.2.1.2.2.1", [ "2", "3", "8"])
}
