import json
import pickle
import re
from munch import munchify
from pymongo import MongoClient

import FAIRsoft as Fs


global webTypes
webTypes = ['rest', 'web', 'app', 'suite', 'workbench', 'db', 'soap', 'sparql']


def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

# All integration at once
def integrateInstances(setOfInstances):
    totalNames, pre_integration_dict = build_pre_integration_dict(setOfInstances)
    save_obj(pre_integration_dict, 'pre_integration_set')
    # save dict to file just in case
    final_set = create_integrated_instances(totalNames, pre_integration_dict)
    return(final_set)    


def worker_pre_integration(i_n, inst, groupInst):
    #print("Processing %s"%(name)
    print("Instance entering: %d"%(i_n), end='\r')
    name = inst.name
    inst._id = str(inst._id)
    if not inst.version:
        inst.version = 'unknown'
    if not inst.type:
        inst.type = 'unknown'

    if name in groupInst.keys():
        if inst.type in groupInst[name].keys():
            newList = groupInst[name][inst.type] + [inst]
            groupInst[name][ inst.type] = newList
        else:
            groupInst[name][inst.type]= [inst]  
    else:
        print("%s not in totalNames"%inst.name)
    
    return(groupInst)
    

def build_pre_integration_dict(setsOfInsts):
    '''
    input: setsOfInstances is a list of sets of instances
    by name and type
    '''
    totalNames = []
    names = []
    for instances in setsOfInsts:
        names.append(set([a.name for a in instances]))
        totalNames = totalNames + [ a.name for a in instances ]


    groupInst = dict()
    totalNames = set(totalNames)

    # Grouping the instances by name and type in a dictionary (groupInst)
    for name in totalNames: # iterating agent names 
        groupInst[name] = {}
    i_n = 0
    for set_ in setsOfInsts:
        for inst in set_:
            i_n+=1
            groupInst = worker_pre_integration(i_n, inst, groupInst)

    return(totalNames, groupInst)

  
def worker_integration(name, groupInst, return_dict, dbagents):
    return_dict[name] = []
    for type_ in groupInst[name].keys():
        #print(name)
        #print(len(groupInst[name][version][type_]))
        instaList = [munchify(inst) for inst in groupInst[name][type_]]
        version = [] 
        for a in instaList:
            if a.version:
                 version.append(a.version[0])
        version = list(set(version))
        
        newInst = instance(name, type_, version)

        newInst.description = [a.description[0] for a in instaList if a.description] # constructing_consensus
        if None in newInst.description:
            newInst.description.remove(None)

        newLinks = []
        for inst in instaList:
            for link in inst.links:
                if link not in newLinks and link:
                    newLinks.append(link)
        newInst.links = newLinks

        pubs = []
        for a in instaList:
            if a.publication:
                for p in a.publication:
                    pubs.append(p)
        newInst.publication =  pubs

        newInst.download = [item for sublist in instaList for item in sublist.download]  
        if None in newInst.download:
            newInst.download.remove(None)

        inst_instr = [a.inst_instr for a in instaList]
        if True in inst_instr:
            newInst.inst_instr = True #
        else:
            newInst.inst_instr = False

        tests = [a.test for a in instaList]
        if True in tests:
            newInst.test = True #
        else:
            newInst.test = False

        newSrc = []
        for a in instaList:
            if a.src:
                for s in a.src:
                    if s!=None:
                        #print(s)
                        newSrc.append(s)

        newInst.src = newSrc

        newOs = []
        for inst in instaList:
            if inst.os:
                for os in inst.os:
                    if os not in newOs:
                        newOs.append(os)

        newInst.os = newOs


        newInputs = []
        for insta in instaList:
            if insta.input:
                for Dict in insta.input:
                    if Dict not in newInputs:
                        newInputs.append(Dict)
                    else:
                        continue

        newInst.input = newInputs # list of strings/dicts
        # TODO: fix this inconsistency with input as strings or dicts in the generators

        newOutputs = []
        for insta in instaList:
            if insta.output:
                for Dict in insta.output:
                    if Dict not in newOutputs:
                        newOutputs.append(Dict)
                    else:
                        continue
            # TODO: fix this inconsistency with output as strings or dicts in the generators

        newInst.output = newOutputs # list of strings

        newDep = []
        for inst in instaList:
            if inst.dependencies:
                for dep in inst.dependencies:
                    if dep not in newDep:
                        newDep.append(dep)
        newInst.dependencies = newDep # list of strings

        newDocs = []
        for inst in instaList:
            if inst.documentation:
                for doc in inst.documentation:
                    if doc not in newDocs:
                        newDocs.append(doc)
                    else:
                        continue

        newInst.documentation = newDocs # list of lists [[type, url], [type, rul], ...]

        newLicense = []
        for a in instaList:
            if len(a.license)>0:
                if a.license[0] not in newLicense and a.license[0] != None and a.license[0] != [] and a.license[0] != False:
                    newLicense.append(a.license[0])
                else:
                    continue
        #print(newLicense)
        newInst.license = newLicense

        newInst.termsUse = False #
        newInst.contribPolicy = False

        newAuth  = []
        for l in instaList:
            if l.authors:
                for auth in l.authors:
                    try:
                        if auth != None and auth.lstrip() not in newAuth:
                            newAuth.append(auth.lstrip())
                        else:
                            continue
                    except Exception as e:
                        print(e)
                        print("Authors:")
                        print(l.authors)

        newInst.authors = newAuth # list of strings

        newRepos = []
        for t in instaList:
            if t.repository:
                for rep in t.repository:
                    if rep not in newRepos:
                        newRepos.append(rep)
        newInst.repository = newRepos

        newSource = []
        for ints in instaList:
            if inst.source:
                for s in ints.source:
                    if s not in newSource:
                        newSource.append(s)
        
        newInst.operational = False
        newInst.ssl = False
        newInst.bioschemas = False
        for a in instaList:
            if a.operational == True:
                newInst.operational = True
            if a.ssl == True:
                newInst.ssl=True
            if a.bioschemas == True:
                newInst.bioschemas = True
        
        semantics = []
        for ints in instaList:   
            semantics.append(ints.semantics) 
        newInst.semantics=semantics[0]

        newInst.source = newSource

        inst=newInst.__dict__
        return_dict[name].append(inst)
        inst['@id'] = "https://openebench.bsc.es/monitor/agent/{name}:{version}/{type}".format(name=inst['name'], version=inst['version'], type=inst['type'])
        updateResult = dbagents.update({'@id':inst['@id']}, { '$set': inst }, upsert=True, multi=True)
    
    return(return_dict)


def integrate_types(groupOfInstances):
    types = list(groupOfInstances.keys())
    not_unknown_types = [type_ for type_ in  types if type_!='unknown']
    n_not_unknown = len(not_unknown_types)
    if n_not_unknown==1:
        known_type = not_unknown_types[0]
        new_known_insts = groupOfInstances[known_type] + groupOfInstances['unknown']
        groupOfInstances[known_type] = new_known_insts
        groupOfInstances.pop('unknown', None)
    return(groupOfInstances)


def create_integrated_instances(groupInst):
    client = MongoClient(port=27017)
    db = client.OPEB
    ##### DB declaration!!!!!!!
    dbagents = db.agents
    
    return_dict = dict()
    n_i=0
    for name in groupInst.keys():
        n_i += 1
        print("Processing %d"%(n_i), end="\r")
        # TODO: find types ---> if only one type diff from uknown, then that one is considered correct
        if 'unknown' in groupInst[name].keys():
            groupInst[name] = integrate_types(groupInst[name])
        return_dict = worker_integration(name, groupInst, return_dict, dbagents)
    return(return_dict)

def generateCanonicalSet(instsctDist):
    '''
    groups instances by name into canonicals
    input: {
             name1: [instance1, instance2],
             name2: [instance3],
             ...
             }
    output: canonicalSet
    '''
    newCanonSet  = canonicalSet()
    for name in instsctDist.keys():
        instances = instsctDist[name]
        sources = list(set([item for sublist in instances for item in sublist.source]))
        types = list(set([inst.type for inst in instances if inst.type != None ]))
        newCanon = canonicalAgent(name, instances, sources, types)
        newCanonSet.addCanononical(newCanon)
    return(newCanonSet)



def loadJSON(path):
    with open(path) as fil:
        return(json.load(fil))

def prepFAIRcomp(instances):
    global stdFormats
    stdFormats= getFormats(instances)


def getFormats(instances):
    inputs = [a.input for a in instances]
    inputs_ = [a for a in inputs]
    inputsNames = []

    nonSFormats = ['txt', 'text', 'csv', 'tsv', 'tabular', 'xml', 'json', 'nucleotide', 'pdf', 'interval' ]
    for List in inputs_:
        for eachD in List:
            if 'format' in eachD.keys():
                if ' format' not in eachD['format']['term'] and eachD['format']['term'].lstrip() not in nonSFormats:
                    if '(text)' not in eachD['format']['term']:
                        if eachD['format']['term'].lstrip() not in inputsNames:
                            inputsNames.append(eachD['format']['term'].lstrip())
    return(inputsNames)
