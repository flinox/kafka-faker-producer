#!/bin/bash

function sintaxe {
    echo ""
    echo "Script para configuração do ambiente de trabalho"
    echo "v1 - 07/2021 - Fernando Lino Di Tomazzo Silva - https://www.linkedin.com/in/flinox"
    echo ""
    echo "Exemplo:"    
    echo ". ./environment_set.sh"
    echo ""    
 }

clear
PS3='Escolha o ambiente para trabalhar: '
options=("DEV" "HML" "PRD")
select opt in "${options[@]}"
do
    case $opt in
        "DEV")
            echo "Configurando para ambiente de DEV"
            chmod +x /app/_key/env-dev.sh
            . /app/_key/env-dev.sh
            break
            ;;
        "HML")
            echo "Configurando para ambiente de HML"
            chmod +x /app/_key/env-hml.sh
            . /app/_key/env-hml.sh
            break
            ;;
        "PRD")
            echo "Configurando para ambiente de PRD"
            chmod +x /app/_key/env-prd.sh
            . /app/_key/env-prd.sh
            break
            ;;
        *) echo "opcao inválida $REPLY";;
    esac
done