import sys
import time
import pickle

import json
from bs4 import BeautifulSoup
from pymongo import MongoClient
from munch import munchify

import FAIRsoft.integration as iu


def collect_preagents_instances():
    sources = {
        'bioconductor',
        'bioconda',
        'bioagents',
        'agentshed',
        'galaxy_metadata',
        'sourceforge',
        'galaxy',
        'opeb_metrics',
        'bioconda_recipes',
        'bioconda_conda',
        'github',
        'bitbucket'
    }

    allInsts = []
    N_instances = 0
    for source in sources:
        insts_iter = preagents.find({"source":[source]})
        insts = [munchify(inst) for inst in insts_iter]
        allInsts.append(insts)

        names=set([inst.name for inst in insts])
        N_instances += len(insts)
        print("Entries from %s: %d"%(source, len(insts)))
        print("Generic agents from %s: %d"%(source, len(names)))

    print("Total instances: %d"%(N_instances))    
    return(allInsts)

def open_pickle(filename):
    with open(filename, 'rb') as f:
        x = pickle.load(f)
        return(x)

if __name__ == '__main__':

    # connecting to DB
    client = MongoClient(port=27017)
    db = client.OPEB
    preagents = db.preagents

    ######----------- Data restructuring and integration ------------------------------------##########

    # Collecting instances from preagents
  
    allInsts = collect_preagents_instances()
    start = time.time()
    
    totalNames, pre_integration_dict = iu.build_pre_integration_dict(allInsts)

    with open('pre_integration_dict.json', 'w') as fp:
        json.dump(pre_integration_dict.copy(), fp)

    with open('totalNames.txt', 'w') as outfile:
        for name in totalNames:
            outfile.write("%s\n"%(name))

    ## Integration of "agent" instances of same ID (name, type)
    start = time.time()
    with open('pre_integration_dict.json', 'r') as outfile:
        pre_integration_dict = json.load(outfile)

    n = []
    for k in pre_integration_dict.keys():
        for kk in pre_integration_dict[k].keys():
            n.append(len(pre_integration_dict[k][kk]))
    
    import collections
    print(collections.Counter(n))
   
    start = time.time()
    inst_name_dict = iu.create_integrated_instances(pre_integration_dict)
    with open('inst_name_dict_2.json', 'w') as fp:
        json.dump(inst_name_dict, fp)
    
    end = time.time()
    print("\n")
    print("Total time: %d"%(end - start))
    



    
