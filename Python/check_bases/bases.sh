#!/bin/bash

echo "<<<bases_720tec>>>"
cat /tmp/bases.txt 2> /dev/null

# Esto es para que el check controle correctamente este caso de no leer nada o no fichero no existe
if [ $? -ne 0 ]; then
    echo "Nofile!"
fi

