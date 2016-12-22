#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Author: Borja Blasco García <bblasco@720tec.es>
# Check para comprobar las snapshots de las VMs en un vCenter

STATUS = 0
STATUS_STR = ['OK', 'WARN', 'CRIT', 'UNK']
MSG = None
PERF_FORMAT = '|number={num_snaps};{w_snap};{c_snap};; days={days};{w_days};{c_days};;'
NSNAP = None
AGE = None

def connect_host(host, port, user, pw):
    import ssl
    import atexit
    import requests
    from pyVmomi import vim
    from pyVim import connect
    from pyVim.connect import SmartConnect, Disconnect

    global STATUS, MSG

    si = None
    context = ssl._create_unverified_context()
    try:
        si = connect.Connect(host, int(port), user, pw, sslContext=context)
        atexit.register(Disconnect, si) # Para la desconexion
    except vim.fault.InvalidLogin:
        # Login erroneo
        STATUS = 2
        MSG = 'Invalid credentials for {}'.format(host)
        return 2
    except vim.fault.HostConnectFault:
        # Host no es vcenter
        STATUS = 2
        MSG = 'Cannot connect to {}'.format(host)
        return 2
    except:
        # Por si acaso
        STATUS = 3
        MSG = 'Unknown error when connecting to {}'.format(host)
        return 3
    return si

def check_modules():
    return 0

def get_data(si):
    from pyVmomi import vim

    def walk_snapshots(snap, lista):
        _nsnap = 0
        if len(snap.childSnapshotList) == 0:
            lista.append(snap)
            _nsnap += 1 # Añadir la propia
            return _nsnap
        else:
            for ch_snap in snap.childSnapshotList:
                _nsnap += walk_snapshots(ch_snap, lista)
            lista.append(snap)
            _nsnap += 1 # La snapshot propia
            return _nsnap


    content = si.RetrieveContent()

    # Obtener la lista de VMs
    container_vms = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    # ver las snapshots container.view[x].snapshot
    # {vm: nombre, snapshots: numero, snapshots_names: nombres, date: fecha}
    vms = []

    for vm in container_vms.view:
        if vm.snapshot is not None:
            vm_datos = {'vm': vm.name, 'snapshots': 0, 'snapshots_list': []}
            for snap in vm.snapshot.rootSnapshotList:
                vm_datos['snapshots'] += walk_snapshots(snap, vm_datos['snapshots_list'])
            vms.append(vm_datos)

    return vms

def check(data, nsnap, ndays, verbose):
    import datetime

    global NSNAP, STATUS, AGE

    status = 3
    today = datetime.datetime.now()

    if data is not None:
        vms_names = []
        vms_snapshots = []
        nsnap_vm = [] # El indice es la VM
        days_vm = [] # El indice es la VM
        number_snap = 0 # Número de snapshots
        vm_oldest_snap = None
        vm_newest_snap = None
        oldest_snap = None # La snapshot mas vieja
        newest_snap = None
        td_old = None
        td_recent = None
        # td_old = today - data[0]['snapshots'][0].createTime.replace(tzinfo=None) # timedelta, dias atras que se hizo
        for vm in data: # Recorrer vms
            vms_names.append(vm['vm'])
            number_snap += vm['snapshots']
            oldest_snap_vm = vm['snapshots_list'][0] #Inicializada
            for snap in vm['snapshots_list']: # Recorrer las snapshots
                if oldest_snap is None:
                    oldest_snap = snap
                    vm_oldest_snap = vm
                    # Comprobar fecha, se cambia el tz para poder hacer la operacion si no falla
                    td_old = today - snap.createTime.replace(tzinfo=None)
                else:
                    if oldest_snap.createTime > snap.createTime:
                        oldest_snap = snap
                        vm_oldest_snap = vm
                        # Comprobar fecha, se cambia el tz para poder hacer la operacion si no falla
                        td_old = today - snap.createTime.replace(tzinfo=None)

                # Comprobar snapshot mas vieja de la VM
                if oldest_snap_vm.createTime > snap.createTime:
                    oldest_snap_vm = snap

                if newest_snap is None:
                    newest_snap = snap
                    vm_newest_snap = vm
                    td_recent = today - snap.createTime.replace(tzinfo=None)
                else:
                    if newest_snap.createTime < snap.createTime:
                        newest_snap = snap
                        vm_newest_snap = vm
                        # Comprobar fecha, se cambia el tz para poder hacer la operacion si no falla
                        td_recent = today - snap.createTime.replace(tzinfo=None)
            # AÑADIDO
            # tupla_vms_snap.append('{}({})'.format(vm['vm'], vm['snapshots']))
            nsnap_vm.append(number_snap)
            if oldest_snap_vm is not None:
                days_vm.append((today - oldest_snap_vm.createTime.replace(tzinfo=None)).days)

        # PREPARAR OUTPUT
        NSNAP = number_snap
        AGE = td_old.days
        # There are <number> in <host>. <excla>
        number_format = 'There are {} snapshots, {}.{}'
        # The oldest snapshot has <days> days. <excla>
        age_str = 'The oldest snapshot has {} days old ({})'.format(td_old.days, vm_oldest_snap['vm'])
        newest_snap_str = 'The newest snapshot has {} days ({}).'.format(td_recent.days, vm_newest_snap['vm'])

        # Comprobar THRESHOLD Numero
        status_n = 0
        if nsnap != (None, None):
            # Comprobar numero de snapshots
            # i sera 0 o 1. el 0 sera el warn y el 1 crit. Por lo que el estado sera i+1 si es mayor al valor obtenido
            for i, threshold in enumerate(nsnap):
                if threshold is not None and int(threshold) <= number_snap:
                    status_n = i + 1

        # Comprobar THRESHOLD Edad
        status_d = 0
        if ndays != (None, None):
            # Comprobar la edad de la snap mas vieja
            # i sera 0 o 1. el 0 sera el warn y el 1 crit. Por lo que el estado sera i+1 si es mayor al valor obtenido
            for i, threshold in enumerate(ndays):
                if threshold is not None:
                    td = datetime.timedelta(days=int(threshold))
                    if td <= td_old:
                        status_d = i + 1

        # OUTPUT NUMERO
        if number_snap != 1: # Plural
            lista_vms_stats = ', '.join('{}({}, {}d)'.format(vms_names[i], nsnap_vm[i], days_vm[i]) for i in range(len(vms_names)))
            number_str = number_format.format(number_snap, lista_vms_stats, '('+'!'*(status_n)+')' if status_n != 0 else '')
        else: # Singular
            number_str = 'There is an snapshot, {}.{}'.format(', '.join('{}({},{}d)'.format(vms_names[0], nsnap_vm[0], days_vm[0])),'('+'!'*(status_n)+')' if status_n != 0 else '')

        # STATUS a global para el perf
        if status_n == 0 and status_d == 0:
            STATUS = 0
        elif status_n == 2 or status_d == 2:
            STATUS = 2
        else:
            STATUS = 1

        # PRINT OUTPUT CHECK
        if verbose:
            str_output = '{} - {}\n{}\n{}'.format(STATUS_STR[STATUS], number_str, age_str, newest_snap_str)
        else:
            str_output = '{} - {}'.format(STATUS_STR[STATUS], number_str)

    else: # data is None no hay snapshots en el sistema
        STATUS = 0
        str_output = '{} - There are not snapshots in {}'.format(STATUS_STR[status], display_name)
    return str_output

if __name__ == '__main__':
    from sys import exit
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Check for monitoring the snapshots inside a vCenter or ESXi')
    parser.add_argument('-H', '--host', action='store', help='', required=True)
    parser.add_argument('-P', '--port', action='store', help='', required=True)
    parser.add_argument('-u', '--user', action='store', help='', required=True)
    parser.add_argument('-p', '--password', action='store', help='', required=True)
    parser.add_argument('-wS', '--warning-snapshots', action='store', help='', type=int)
    parser.add_argument('-cS', '--critical-snapshots', action='store', help='', type=int)
    parser.add_argument('-wD', '--warning-days', action='store', help='', type=int)
    parser.add_argument('-cD', '--critical-days', action='store', help='', type=int)
    parser.add_argument('-v', '--verbose', action='store_true', help='Multiline with more data')

    args = parser.parse_args()

    perf_empty = PERF_FORMAT.format_map({'num_snaps': '"U"', 'w_snap': args.warning_snapshots, 'c_snap': args.critical_snapshots, 'days': '"U"', 'w_days': args.warning_days, 'c_days': args.critical_days})

    if check_modules() != 0:
        print('UNK -', MSG + perf_empty)
        exit(STATUS)

    si = connect_host(host=args.host, port=args.port, user=args.user, pw=args.password)
    if STATUS != 0:
        print('{} -'.format(STATUS_STR[STATUS]),MSG + perf_empty)
        exit(STATUS)
    str_output = check(get_data(si), (args.warning_snapshots, args.critical_snapshots), (args.warning_days, args.critical_days), args.verbose)

    str_output = '{}{}'.format(str_output, PERF_FORMAT.format_map({'num_snaps': NSNAP, 'w_snap': args.warning_snapshots if args.warning_snapshots else '', 'c_snap': args.critical_snapshots if args.critical_snapshots else '', 'days': AGE, 'w_days': args.warning_days if args.warning_days else '', 'c_days': args.critical_days if args.critical_days else ''}))

    # Imprimir salida
    print(str_output)
    exit(STATUS)
