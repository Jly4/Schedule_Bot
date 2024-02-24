#!/bin/bash
############-YOU SCRIPT-##############


cd /home/nc_admin/Schedule_Bot/
cp _Instal_scripts/Montserrat/*.ttf /usr/share/fonts/ 
fc-cache -f -v

pip install poetry
poetry env use python3.11
poetry install
poetry run python main.py
