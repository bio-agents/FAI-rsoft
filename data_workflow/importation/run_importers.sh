#!bin/bash

bash ./importations.sh >> importations.log 2> importations.error
bash mongoexport -d OPEB -c alambique > alambique.json
