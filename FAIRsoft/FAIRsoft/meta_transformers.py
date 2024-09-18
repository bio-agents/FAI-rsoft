import json
import pickle
import re
from munch import munchify
from pymongo import MongoClient

from FAIRsoft.utils import agentGenerator


global webTypes
webTypes = ['rest', 'web', 'app', 'suite', 'workbench', 'db', 'soap', 'sparql']


def extract_ids(id_):
    #extract ids from metrics @id
    fields = id_.split('/')
    if len(fields)>6:
        name = fields[5].split(':')[1]
        if len(fields[5].split(':'))>2:
            version = fields[5].split(':')[2]
        else:
            version = None
        type_ = fields[6]
    
        ids = {
            'name' : name,
            'version' : version,
            'type' : type_
        }

        return(ids)
    
    return


def cleanVersion(version):
    if version != None:
        if '.' in version:
            #print(version.split('.')[0]+'.'+ version.split('.')[1])
            return(version.split('.')[0]+'.'+ version.split('.')[1])
        else:
            return(version)
    else:
        return(version)

def get_repo_name_version_type(id_):
    fields = id_.split('/')
    name_plus = fields[5]
    name_plus_fields=name_plus.split(':')
    name=name_plus_fields[1]
    if len(name_plus_fields)>2:
        version=name_plus.split(':')[2]
    else:
        version=None 

    if len(fields)>6:
        type_=fields[6]
    else:
        type_=None
     
    return({'name':name, 'version':version, 'type':type_})


class repositoryAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'repository'):
        agentGenerator.__init__(self, agents, source)
        self.instSet = setOfInstances('repository')

        for agent in self.agents:
            # We skip generic entries
            if len(agent['@id'].split('/'))<7:
                continue
            else:
                id_data = get_repo_name_version_type(agent['@id'])
                name = clean_name(id_data['name'].lower())
                version = id_data['version']
                if version == None:
                    version = 'unknown'
                type_=id_data['type']
                if type_ == None:
                    type_ = 'unknown'

                newInst = instance(name, type_, [version])
                # there are several versions, to simplify integration, we want one instance per version
                if 'versions' in  agent['repos'][0]['res'].keys():
                    versions = agent['repos'][0]['res']['versions']
                else:
                    versions = [version]

                for v in versions:
                    newInst = instance(name, type_, versions)
                    
                    if agent['repos'][0]['res'].get('desc'):
                        newInst.description = [agent['repos'][0]['res'].get('desc')]
                    newInst.links = agent['entry_links']
                    newInst.publication =  None

                    binary_uri = agent['repos'][0]['res'].get('binary_uri')
                    source_uri = agent['repos'][0]['res'].get('source_uri')
                    download = [binary_uri, source_uri]
                    if None in download:
                        download.remove(None)
                    if source_uri or binary_uri:
                        newInst.download = download
                    else:
                        newInst.download = []  # list of lists: [[type, url], [], ...]
                    
                    newInst.inst_instr =  agent['repos'][0]['res'].get('has_tutorial')
                    newInst.test = None
                    try:
                        src = [agent['repos'][0]['res'].get('source_uri')]
                    except:
                        newInst.src = []
                    else:
                        if agent['repos'][0]['res'].get('source_uri')!=None:
                            newInst.src = src

                    if newInst.src:
                        newInst.os = ['Linux', 'Mac', 'Windows']
                    else:
                        newInst.os = None

                    newInst.input = None # list of dictionaries bioagents-like {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
                    newInst.output = None  # list of dictionaries bioagents-like {'format' : <format> , 'uri' : <uri> }
                    newInst.dependencies = None # list of strings
                    if agent['repos'][0]['res'].get('readmeFile'):
                        newInst.documentation = [['readme', agent['repos'][0]['res'].get('readmeFile')]] # list of lists [[type, url], [type, rul], ...]
                    if agent['repos'][0]['res'].get('source_license'):
                        newInst.license = [agent['repos'][0]['res'].get('source_license')] 
                        newInst.termsUse = [agent['repos'][0]['res'].get('source_license')] 
                    newInst.contribPolicy = None

                    auths = []
                    authors_l = agent['repos'][0]['res'].get('agent_developers')
                    if authors_l:
                        for author in authors_l:
                            auths.append('username')
                    newInst.authors = auths

                    newInst.repository = agent['entry_links']
                    newInst.source = [agent['repos'][0]['kind']] #string
                    newInst.bioschemas = None
                    newInst.https = None
                    newInst.operational = None
                    newInst.ssl = None
            
                    self.instSet.instances.append(newInst)


def clean_name(name):
    #TODO: clean emboss:  and emboss__ too
    name=name.lower()
    print(name)
    bioconductor=re.search("^bioconductor-", name)
    if bioconductor:
        name=name[bioconductor.end():]
    emboss_dots=re.search("^emboss: ", name)
    if emboss_dots:
        name=name[emboss_dots.end():]
    emboss_unders=re.search("^emboss__", name)
    if emboss_unders:
        name=name[emboss_unders.end():]
    return(name)

def set_type_bioconda(id_):
    if 'bioconductor' in id_:
        return('lib')
    else:
        return('cmd')


class biocondaRecipesAgentsGenerator(agentGenerator):
    def __init__(self, agents, source="bioconda_recipes"):
        agentGenerator.__init__(self, agents, source)
        self.instSet = setOfInstances('bioconda_recipes')

        for agent in self.agents:
            name = clean_name(agent['name'])
            
            version = agent['@id'].split('/')[5].split(':')[2]
            type_ = agent['@id'].split('/')[6]
            if type_ == None:
                type_ =  set_type_bioconda(agent['@id'])

            if version == None:
                version = 'unknown'
            if type_ == None:
                type_ = 'unknown'
            
            newInst = instance(name, type_, [version])
            try:
                description = agent['about']['description']
            except:
                newInst.description = []
            else:
                if description:
                    newInst.description = [description] # string
            
            links = []
            if 'about' in agent.keys() and agent['about']:
                if 'home' in agent['about'].keys() and agent['about']['home']:
                    if agent['about']['home']:
                        links.append(agent['about']['home'])
        
            src = []
            if 'source' in agent.keys() and agent['source']:
                if 'url' in agent['source'] and agent['source']['url']:
                    
                    src = agent['source']['url']
                    if type(agent['source']['url'])==list:
                        for l in agent['source']['url']:
                            links.append(l)

                    else:
                        links.append(agent['source']['url'])


            
            try:
                doc_url = agent['about']['doc_url']
            except:
                pass
            else:
                if doc_url:
                    for d in doc_url:
                        links.append(d)

            newInst.links = links
            newInst.publication =  None # number of related publications [by now, for simplicity]
            if src:
                if type(src) != list:
                    src = [src]
                
                newInst.download = src
                
            newInst.inst_instr = True # boolean // FUTURE: u'ri or text
            newInst.test = None
            if 'test' in agent.keys():
                if agent['test']:
                    if 'commands' in agent['test'].keys():
                        newInst.test = True
            newInst.src = src # string
            newInst.os = ['Linux', 'Mac', 'Windows'] # list of strings
            newInst.input = [] # list of dictionaries bioagents-like {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
            newInst.output = [] # list of dictionaries bioagents-like {'format' : <format> , 'uri' : <uri> }
            deps = [] 
            if 'requirements' in agent.keys() and agent['requirements']:
                for req_k in agent['requirements'].keys():
                    if agent['requirements'][req_k]:
                        for dep in agent['requirements'][req_k]:
                            deps.append(dep)

            newInst.dependencies = deps # list of strings
            documentation = []
            try:
                doc = ['documentation',agent['about']['docs']]
                documentation.append(doc)
            except:
                pass

            try:
                doc = ['documentation', agent['about']['doc_url']]
                documentation.append(doc)
            except:
                pass

            newInst.documentation = documentation # list of lists [[type, url], [type, rul], ...]
            if 'about' in agent.keys():
                if agent['about'].get('license'):
                    newInst.license = [agent['about'].get('license')] 
                    newInst.termsUse = [agent['about'].get('license')] #
            newInst.contribPolicy = False
            credit = []
            try:
                auth=agent['about']['author']
            except:
                pass
            else:
                credit.append(auth)
            try:
                mantainers = agent['about']['mantainers']
            except:
                mantainers = None
            else:
                for m in mantainers:
                    credit.append(m)

            newInst.authors = credit # list of strings
            repository = []
            for l in links:
                if l:
                    if 'github' in l:
                        repository.append(l)
                    elif 'bitbucket' in l:
                        repository.append(l)
                    elif 'sourceforge' in l:
                        repository.append(l)

            newInst.repository = repository
            newInst.source = ['bioconda_recipes'] #string
            newInst.bioschemas = None
            newInst.https = None
            newInst.operational = None
            newInst.ssl = None

            self.instSet.instances.append(newInst)

class bioconda_conda_AgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'bioconda_conda'):
        agentGenerator.__init__(self, agents, source)
        self.instSet = setOfInstances('bioconda_conda')

        for agent in self.agents:
            id_info = extract_ids(agent['@id'])
            name = clean_name(id_info['name'])
            version = id_info['version']
            if version == None:
                version = 'unknown'
    
            type_ = set_type_bioconda(agent['@id'])
            if type_ == None:
                type_ = 'cmd'
            elif type_ == 'unknown':
                type_ = 'cmd'

            newInst = instance(name, type_, [version])

            newInst.description = None # string
            newInst.version = [version]
            newInst.type = type_
            newInst.links =[agent['url']]
            newInst.publication =  None # number of related publications [by now, for simplicity]
            newInst.download = [agent['url']]  # list of lists: [[type, url], [], ...]
            newInst.inst_instr = True # boolean // FUTURE: uri or text
            newInst.test = None # boolean // FUTURE: uri or text
            newInst.src = [] # string
            newInst.os = ['Linux', 'Mac', 'Windows'] # list of strings
            newInst.input = [] # list of dictionaries bioagents-like {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
            newInst.output = [] # list of dictionaries bioagents-like {'format' : <format> , 'uri' : <uri> }
            newInst.dependencies = agent['dependencies'] # list of strings
            newInst.documentation = [] # list of lists [[type, url], [type, rul], ...]
            if 'license' in agent.keys():
                newInst.license = [agent['license']] # string
            newInst.termsUse = None #
            newInst.contribPolicy = None
            newInst.authors = [] # list of strings
            newInst.repository = []
            newInst.source = ['bioconda_conda'] #string
            newInst.bioschemas = None
            newInst.https = None
            newInst.operational = None
            newInst.ssl = None

            self.instSet.instances.append(newInst)




class biocondaAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'bioconda'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('bioconda')

        #names = [a['name'].lower() for a in self.agents]
        #print('diferent names in bioconda agents: ' + str(len(set(names))))

        for agent in self.agents:
            name = clean_name(agent['@label'])
            
            version = cleanVersion(agent['@version'])
            if version == None:
                version = 'unknown'
            type_ = 'cmd' # all biocondas are cmd

            newInst = instance(name, type_, [version])
            if 'description' in agent.keys():
                newInst.description = [agent['description']] # string
            if agent['web']['homepage']:
                newInst.links = [agent['web']['homepage']] #list
            else:
                newInst.links = []
            newInst.publication =  agent['publications'] 

            download = []
            for k in agent['distributions'].keys():
                for link in agent['distributions'][k]:
                    download.append(link)

            newInst.download = download

            newSrc = []
            for down in agent['distributions'].keys():
                if 'source' in down:
                    if len(agent['distributions'][down])>0:
                        for u in agent['distributions'][down]:
                            newSrc.append(u)
            newInst.src = newSrc 

            if 'license' in agent.keys() and agent['license']!='':
                newInst.license = [agent['license']] # string
            newInst.repository = agent['repositories']
            newInst.source = ['bioconda']
            newInst.links.append(agent['web']['homepage'])
            if agent['repositories']:
                for a in agent['repositories']:
                    newInst.links.append(a)

            self.instSet.instances.append(newInst)



class bioconductorAgentsGenerator(agentGenerator):
    def __init__(self, agents, source='bioconductor'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('bioconductor')

        for agent in self.agents:
            type_= 'lib'
            version = cleanVersion(agent['Version'])
            if version == None:
                version = 'unknown'
            name = clean_name(agent['name'])
            newInst = instance(name, type_, [version])
            newInst.description = [agent['description']] # string
            if agent['URL']:
                newInst.links = [agent['URL']]
            else:
                newInst.links = []
            newInst.publication =  [agent['publication']] 
            download = []
            for a in ["Windows Binary", "Source Package", "Mac OS X 10 10.11 (El Capitan)"]:
                if a in agent.keys() and agent[a]:
                    download.append(agent['Package Short Url'] + agent[a])

            newInst.download = download
            newInst.inst_instr = agent['Installation instructions'] #
            newInst.src = [ a for a in newInst.download if a[0] == "Source Package"[0] ]# string
            newInst.os = ['Linux', 'Mac', 'Windows'] # list of strings
            if agent['Depends']:
                deps = agent['Depends']
            else:
                deps = []
            if agent['Imports']:
                impo = agent['Imports'].split(',')
            else:
                impo = []

            newInst.dependencies = [item for sublist in [deps+impo] for item in sublist] # list of strings

            newInst.documentation = [[ a, a[0] ] for a in agent['documentation']] # list of lists [[type, url], [type, rul], ...]
            if agent['License']!='':
                newInst.license = [agent['License']] # string
            else:
                newInst.license = False
            newInst.authors = [a.lstrip() for a in agent['authors']] # list of strings
            newInst.repository = [agent['Source Repository'].split('gitclone')[1]]
            newInst.description = [agent['description']]
            newInst.source = ['bioconductor'] #string

            self.instSet.instances.append(newInst)


def constrFormatsConfig(formatList):
    '''
    From an input that is a str to a bioagents kind of format
    '''
    notFormats = ['data']
    newFormats = []
    seenForms = []
    for formt in formatList:
        if formt not in seenForms:
            if ',' in formt:
                formats = formt.split(',')
                for f in formats:
                    if f not in notFormats:
                        newFormats.append({ 'format' : {'term' : f , 'uri' :  None }})
                        seenForms.append(formt)
            else:
                if formt not in notFormats:
                    newFormats.append({ 'format' :  {'term' : formt , 'uri' :  None }})
                    seenForms.append(formt)
        else:
            continue
    return(newFormats)


class bioagentsOPEBAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'bioagentsOPEB'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('bioagentsOPEB')

        for agent in self.agents:
            if agent['@label']:
                name = clean_name(agent['@label'])
                type_ = agent['@type']
                version = cleanVersion(agent['@version'])
                if version == None:
                    version = 'unknown'
                if type_ == None:
                    type_ = 'unknown'

                newInst = instance(name, type_, [version])

                newInst.description = [agent['description']] # string
                newInst.publication = agent['publications']
                newInst.test = False
                if 'license' in agent.keys():
                    newInst.license = [agent['license']]
                newInst.input = []
                newInst.output = []
                if 'documentation' in agent.keys():
                    if 'general' in agent['documentation'].keys():
                        newInst.documentation = [['general', agent['documentation']['general']]]
                newInst.source = ['bioagents']
                os = []
                if 'os' in agent.keys():
                    for o in agent['os']:
                        os.append(o)
                    newInst.os = os
                newInst.repository = agent['repositories']

                newInst.links.append(agent['web']['homepage'])
                if agent['repositories']:
                    for a in agent['repositories']:
                        newInst.links.append(a)

                if agent['semantics']:
                    if agent['semantics']['inputs']:
                        newInst.input = agent['semantics']['inputs']
                    if agent['semantics']['outputs']:
                        newInst.output = agent['semantics']['outputs']
                newInst.semantics = agent['semantics']

                newAuth = []
                for dic in agent['credits']:
                    if dic.get('name'):
                        if dic['name'] not in newAuth and dic['name']!=None:
                            newAuth.append(dic['name'])
                newInst.authors = newAuth

                self.instSet.instances.append(newInst)



class sourceforgeAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'sourceforge'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('sourceforge')

        for agent in self.agents:
            name = agent['@source_url'].split('/')[-1]
            
            name = name.lower()
            type_ = 'unknown'
            version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.source = ['sourceforge']
            os = []
            if 'operating_system' in agent.keys():
                for o in agent['operating_system']:
                    os.append(o)
                newInst.os = os
            newInst.repository = [agent['repository']]
            newInst.download = [agent['@source_url']]
            newInst.repository = [agent['@source_url']]
            newInst.links.append(agent['homepage'])

            self.instSet.instances.append(newInst)



class galaxyOPEBAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'galaxyOPEB'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('galaxyOPEB')

        for agent in self.agents:
        
            name = clean_name(agent['name'].lower())
            name=name.replace(' ','_') #so it is coherent with opeb metrics nameszz

            type_ = 'web'
            version = agent['@version']
            if version == None:
                version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.description = [agent['description']] # string
            newInst.source = ['galaxy']
            newInst.os = ['Mac', 'Linux']
            newInst.repository = agent['repositories']
            if 'license' in agent.keys():
                newInst.license = [agent['license']]
            newInst.publication = agent['publications']

            self.instSet.instances.append(newInst)


class metricsOPEBAgentsGenerator(agentGenerator):
    # TODO: obtain citations
    def __init__(self, agents, source = 'opeb_metrics'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('opeb_metrics')
        for agent in self.agents:
            ids = extract_ids(agent['@id'])
            if ids:
                version = ids['version']
                type_ = ids['type']
                # type needs to be corrected for galaxy agents from workflow to web
                if ids['type'] == 'workflow' and 'galaxy' in agent['@id']:
                    type_='web'
                if version == None:
                    version = 'unknown'
                if type_ == None:
                    type_ = 'unknown'
                name = clean_name(ids['name'].lower())
                newInst = instance(name, type_, [version])
                newInst.source = ['opeb_metrics']
                if agent['project'].get('website'):
                    newInst.bioschemas = agent['project']['website'].get('bioschemas')
                    newInst.https = agent['project']['website'].get('https')
                    newInst.ssl = agent['project']['website'].get('ssl')
                    if agent['project']['website'].get('operational') == 200:
                        newInst.operational = True
                    else:
                        newInst.operational = False
                if agent['project'].get('publications'):
                    newInst.publication = agent['project']['publications']
                    
                
                self.instSet.instances.append(newInst)


class galaxyShedAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'galaxyShed'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('agentshed')

        for agent in self.agents:
            name = clean_name(agent['name'].lower())
            type_ = 'cmd'
            if 'version' in agent.keys():
                version = cleanVersion(agent['version'])
            else:
                version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.description = [agent['description']] # string
            newInst.inst_instr = True # Since this is installable through AgentShed
            if len(agent['tests'])>0:
                newInst.test = True # boolean
            else:
                newInst.test = False

            newInst.dependencies = [a['name'] for a in agent['requirements']] # list of strings
            newInst.repository = [] ### FILL!!!!!!!!!!!
            newInst.links = [] ### FILL!!!!!!!!!!!!
            newInst.source = ['agentshed']#string
            newInst.os = ['Linux', 'Mac']

            self.instSet.instances.append(newInst)


class galaxyMetadataGenerator(agentGenerator):
    def __init__(self, agents, source = 'galaxy_metadata'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('galaxy_metadata')

        for agent in self.agents:
            name = clean_name(agent['name'].lower())
            type_ = 'cmd'
            if 'version' in agent.keys():
                version = cleanVersion(agent['version'])
            else:
                version = 'unknown'

            newInst = instance(name, type_, [version])

            newInst.dependencies = agent['dependencies'] # list of strings
            newInst.source = ['galaxy_metadata']

            self.instSet.instances.append(newInst)


class galaxyConfigAgentsGenerator(agentGenerator):
    def __init__(self, agents, source = 'agentshed'):
        agentGenerator.__init__(self, agents, source)

        self.instSet = setOfInstances('agentshed')

        for agent in self.agents:
            if agent['name']:
                name = clean_name(agent['name'].lower())

                type_ = 'cmd'

                version = cleanVersion(agent['version'])
                if version == None:
                    version = 'unknown'

                newInst = instance(name, type_, [version])

                if agent['description']:
                    newInst.description = [agent['description']] # string

                if agent['citation']:
                    newInst.publication =  [agent['citation']] 

                newInst.test = agent['tests'] # boolean

                if len(agent['dataFormats']['inputs'])>0:
                    newInst.input = constrFormatsConfig(agent['dataFormats']['inputs']) # list of strings

                if len(agent['dataFormats']['outputs'])>0:
                    newInst.output = constrFormatsConfig(agent['dataFormats']['outputs']) # list of strings

                docu = []
                if agent['readme'] == True:
                    docu.append(['readme', None])
                if agent['help']:
                    docu.append(['help', agent['help'].lstrip()])

                newInst.documentation = docu # list of lists [[type, url], [type, url], ...]

                newInst.source = ['agentshed'] #string

                self.instSet.instances.append(newInst)



def lowerInputs(listInputs):
    newList = []
    if len(listInputs)>0:
        for format in listInputs:
            newFormat = {}
            for a in format.keys():
                newInner = {}
                if format[a] != []:
                    #print(format[a])
                    if type(format[a]) == list:
                        for eachdict in format[a]:
                            for e in eachdict.keys():
                                newInner[e] = eachdict[e].lower()
                            newFormat[a] = newInner
                    else:
                        for e in format[a].keys():
                            newInner[e] = format[a][e].lower()
                        newFormat[a] = newInner
        newList.append(newFormat)
    else:
        return([])
    return(newList)


# TODO" refactor this
class bioagentsAgentsGenerator(agentGenerator):

    def __init__(self, agents, source = 'bioagents'):

        agentGenerator.__init__(self, agents, source)

        self.splitInstances()


    def splitInstances(self):
        '''
        newInst.splitInstances returns the set of instances
        '''
        self.instSet = setOfInstances('bioagents')
        names = [a['bioagentsID'].lower for a in self.agents]
        #print('diferent names in bioagents agents: ' + str(len(set(names))))
        #print('diferent insatances in bioagents agents: ' + len(names))
        for agent in self.agents:
            if len(agent['agentType']) > 0:
                for type_ in agent['agentType']:
                    vers = []
                    if len(agent['version']) > 0:
                        for version in agent['version']:

                            name = agent['@label'].lower()

                            newInst = instance(name, type_, [cleanVersion(version)])

                            newInst.description = agent['description']

                            newInst.homepage = agent['homepage']

                            newInst.publication = len(agent['publication'])
                            

                            newInst.download = [ [tol['type'], tol['url']] for tol in agent['download'] ]

                            src = []
                            for down in [a for a in agent['download'] if a['type'] == 'Source package']:
                                src.append(down['url'])
                            newInst.src =src

                            newInst.os = agent['operatingSystem']

                            inputs = []
                            if len(agent['function'])>0:
                                inputs = [f['input'] for f in agent['function']]
                                newInst.input = lowerInputs(inputs[0])
                            else:
                                newInst.input = []

                            outputs = []
                            if len(agent['function'])>0:
                                outputs = [f['input'] for f in agent['function']]
                                newInst.output = lowerInputs(outputs[0])
                            else:
                                newInst.output = []



                            newInst.documentation = [ [doc['type'], doc['url']] for doc in agent['documentation']]

                            if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                                newInst.inst_instr = True

                            newInst.license = agent['license']

                            newAuth = []
                            for dic in agent['credit']:
                                if dic['name'] not in newAuth and dic['name']!=None:
                                    newAuth.append(dic['name'])
                            newInst.authors = newAuth

                            repos = []
                            for link in agent['link']:
                                if link['type'] == "Repository":
                                    repos.append(link['url'])
                            newInst.repository = repos

                            newInst.description = agent['description']

                            newInst.source = ['bioagents']

                            self.instSet.instances.append(newInst)


                    else:
                        version = None
                        name = agent['bioagentsID'].lower()
                        newInst = instance(name, type_, [cleanVersion(version)])

                        newInst.description = agent['description']

                        newInst.homepage = agent['homepage']

                        newInst.publication = len(agent['publication'])

                        newInst.download = [ [tol['type'], tol['url']] for tol in agent['download'] ]

                        src = []
                        for down in [a for a in agent['download'] if a['type'] == 'Source package']:
                            src.append(down['url'])
                        newInst.src =src

                        newInst.os = agent['operatingSystem']

                        inputs = []
                        inputs = [f['input'] for f in agent['function']]
                        if len(agent['function'])>0:
                            inputs = [f['input'] for f in agent['function']]
                            newInst.input = lowerInputs(inputs[0])
                        else:
                            newInst.input = []

                        outputs = []
                        if len(agent['function'])>0:
                            outputs = [f['input'] for f in agent['function']]
                            newInst.output = lowerInputs(outputs[0])
                        else:
                            newInst.output = []

                        newInst.documentation = [ [doc['type'], doc['url']] for doc in agent['documentation']]

                        if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                            newInst.inst_instr = True

                        newInst.license = agent['license']

                        newAuth = []
                        for dic in agent['credit']:
                            if dic['name'] not in newAuth and dic['name']!=None:
                                newAuth.append(dic['name'])
                        newInst.authors = newAuth

                        repos = []
                        for link in agent['link']:
                            if link['type'] == "Repository":
                                repos.append(link['url'])
                        newInst.repository = repos

                        newInst.description = agent['description']

                        newInst.source = ['bioagents']

                        self.instSet.instances.append(newInst)

            else:
                type_ = None
                if len(agent['version']) > 0:
                    for version in agent['version']:

                        name = agent['bioagentsID'].lower()
                        newInst = instance(name, type_, [cleanVersion(version)])

                        newInst.description = agent['description']

                        newInst.homepage = agent['homepage']

                        newInst.publication = len(agent['publication'])

                        newInst.download = [ [tol['type'], tol['url']] for tol in agent['download'] ]

                        src = []
                        for down in [a for a in agent['download'] if a['type'] == 'Source package']:
                            src.append(down['url'])
                        newInst.src =src

                        newInst.os = agent['operatingSystem']

                        inputs = []
                        if len(agent['function'])>0:
                            inputs = [f['input'] for f in agent['function']]
                            newInst.input = lowerInputs(inputs[0])
                        else:
                            newInst.input = []

                        outputs = []
                        if len(agent['function'])>0:
                            outputs = [f['input'] for f in agent['function']]
                            newInst.output = lowerInputs(outputs[0])
                        else:
                            newInst.output = []

                        newInst.documentation = [ [doc['type'], doc['url']] for doc in agent['documentation']]

                        if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                            newInst.inst_instr = True

                        newInst.license = agent['license']

                        newAuth = []
                        for dic in agent['credit']:
                            if dic['name'] not in newAuth and dic['name']!=None:
                                newAuth.append(dic['name'])
                        newInst.authors = newAuth

                        repos = []
                        for link in agent['link']:
                            if link['type'] == "Repository":
                                repos.append(link['url'])
                        newInst.repository = repos

                        newInst.source = ['bioagents']

                        self.instSet.instances.append(newInst)

                else:
                    version = None
                    name = agent['bioagentsID'].lower()
                    newInst = instance(name, type_, [cleanVersion(version)])

                    newInst.description = agent['description']

                    newInst.homepage = agent['homepage']

                    newInst.publication = len(agent['publication'])

                    newInst.download = [ [tol['type'], tol['url']] for tol in agent['download'] ]

                    src = []
                    for down in [a for a in agent['download'] if a['type'] == 'Source package']:
                        src.append(down['url'])

                    newInst.src =src

                    newInst.os = agent['operatingSystem']

                    inputs = []
                    if len(agent['function'])>0:
                        inputs = [f['input'] for f in agent['function']]
                        newInst.input = lowerInputs(inputs[0])
                    else:
                        newInst.input = []

                    outputs = []
                    if len(agent['function'])>0:
                        outputs = [f['input'] for f in agent['function']]
                        newInst.output = lowerInputs(outputs[0])
                    else:
                        newInst.output = []

                    newInst.documentation = [ [doc['type'], doc['url']] for doc in agent['documentation']]

                    if 'Manual' in [ doc[0] for doc in newInst.documentation ]:
                        newInst.inst_instr = True

                    newInst.license = agent['license']

                    newAuth = []
                    for dic in agent['credit']:
                        if dic['name'] not in newAuth and dic['name']!=None:
                            newAuth.append(dic['name'])
                    newInst.authors = newAuth

                    repos = []
                    for link in agent['link']:
                        if link['type'] == "Repository":
                            repos.append(link['url'])
                    newInst.repository = repos

                    newInst.source = ['bioagents']

                    self.instSet.instances.append(newInst)


agent_generators = {
        'bioconductor' : bioconductorAgentsGenerator,
        'bioagents' : bioagentsOPEBAgentsGenerator,
        'bioconda' : biocondaAgentsGenerator,
        'agentshed' : galaxyConfigAgentsGenerator,
        'galaxy_metadata' : galaxyMetadataGenerator,
        'sourceforge' : sourceforgeAgentsGenerator,
        'galaxy' : galaxyOPEBAgentsGenerator,
        'opeb_metrics' : metricsOPEBAgentsGenerator,
        'bioconda_recipes': biocondaRecipesAgentsGenerator,
        'bioconda_conda': bioconda_conda_AgentsGenerator,
        'repository': repositoryAgentsGenerator,
}


