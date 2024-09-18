#!/bin/bash

## PUT THIS INTO PYTHON SCRIPT TO USE MODULE
importers_base_path=""

#bioconductor
bioc_importer=$importers_base_path"/bioconductor/importer.py"
echo "Bioconductor importation starting ..."
python3 $bioc_importer
echo "Finished"

#bioagents-bioconda
echo "OPEB bioagents and bioconda importation stating ..."
bioagents_bioconda_importer=$importers_base_path"/bioconda_bioagents/importer.py"
#python3 $bioagents_bioconda_importer
echo "Finished"

#galaxy
echo "Galaxy importation starting ..."
galaxy_importer=$importers_base_path"/galaxy/importer.py"
#python3 $galaxy_importer
echo "Finished"

#agentshed
echo "Galaxy Agentshed importation starting ..."
agentshed_importer=$importers_base_path"/agentshed/importer.py"
#python3 $agentshed_importer
echo "Finished"

#repositories
echo "Repos importation starting ..."
repositories_importer=$importers_base_path"/repositories/importer.py"
#python3 $repositories_importer
echo "Finished"

#metrics
echo "OPEB metrics starting ..."
metrics_importer=$importers_base_path"/opeb_metrics/importer.py"
#python3 $metrics_importer
echo "Finished"


