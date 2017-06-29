Check_bases
================

El `check_bases` se compone de varias scripts de python y un fichero de configuración. Esto es debido
a que este check se debe realizar en varios pasos.

 1. Recogida de datos desde la sonda, mediante `SSH`.
 2. Tratamiento de los datos, es el mismo script que 1.
 3. Disposición de los datos en el agente.
 4. Realización del check

Se separan porque el paso una va comprobando periodicamente y tiene que esperar que la sonda cambie de AP
por lo que si lo haría el propio check ralentizaría toda la monitorización.

El fichero `bases.yml` contiene la información de las bases en formato `YAML`.

El fichero `get_data.py` es el encargado de conectarse a la sonda para ir cambiado de AP y recogiendo los datos.

El fichero `bases.py` es el encargado de poner los datos en el agente de **Check_MK**.

El fichero `check_bases.py` es el encargado del inventario del check y del propio check.

## Para instalar el check

Como este check es del agente y los diversos ficheros necesitan algunas dependencias se sigue esta guía para la instalación.

``` bash
apt-get install python3-yaml
mkdir -p /etc/720tec/check-bases
mkdir -p /etc/720tec/keys

# Se crea un link de la clave privada de ssh, aquí se llama sonda, sonda y sonda.pub
ln -s /home/adm720/.ssh/sonda /etc/720tec/keys/sonda

# Se crea el fichero de bases y se rellena
vi /etc/720tec/bases.yml

# Se descargan y copian los ficheros necesarios para el check. Se limpia la carpeta
git clone https://bblasco@git.720tec.cloud/bblasco/checks-monitorizacion.git && cd checks-monitorización/Python/check_bases
cp {get_data.py,check_bases.py,bases.sh} /etc/720tec/check-bases/
cd ~
rm -rf checks-monitorizacion

# Se crean links a los sitios que haga falta
ln -s /etc/720tec/check-bases/bases.sh /usr/lib/check_mk_agent/plugins/bases.sh
ln -s /etc/720tec/check-bases/check_bases.py /omd/site/<site>/share/check_mk/checks/720tec_Bases

# Se hacen todos los ficheros ejecutables
chmod +x /etc/720tec/check-bases/*

# Se añade el programa de recoleccion de datos al crontab
crontab -e
*/5 * * * * /etc/720tec/check-bases/get_data.py
```  

Para poder inventariar al momento y ver que todo va bien podemos lanzar el script `get_data.py`. `/etc/720tec/check-bases/get_data.py`.

## Fichero `bases.yml`

Contiene la configuración de la sonda, usuario y keyssh. Es opcional pero recomendable. Se utiliza la tag `configuration` y van los 3 datos anidados, `sonda`, `key` y `user`. Además, contiene la información de la base, como `nombre`, `IP`, `MAC eth`, `MAC wlan24` (MAC en la wlan de 2.4Ghz) y `MAC wlan5` (MAC para la wlan de 5GHz). Aunque, al final solo se usan el nombre y la mac de 5GHz. Esto quiere decir que se pueden añadir más campos si es necesario para otros cosas.

``` yaml
configuration:
sonda: 192.168.1.1
key: "/home/adm720/.ssh/sonda"
user: "adm720"

Base01:
ip: 192.168.1.1
mac:
eth0: "aa:bb:cc:dd:ee:ff"
wlan5: "cc:bb:dd:ff:vv:gg"
```