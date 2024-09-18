import json
import multiprocessing
import pickle
import re
from munch import munchify
from pymongo import MongoClient

global webTypes
webTypes = ['rest', 'web', 'app', 'suite', 'workbench', 'db', 'soap', 'sparql']

class instance(object):

    def __init__(self, name, type_, version):

        # TODO: restrict the format of properties

        self.name : str = name
        self.version : List(str) = version
        self.type : str = type_
        self.links : List(str) = []
        self.publication : List() =  []
        self.download : List(str) = []
        self.inst_instr : bool = False
        self.test : bool = False
        self.src : List(str) = []
        self.os : List(str) = []
        self.input : List(dict) = [] #  {'format' : <format> , 'uri' : <uri> , 'data' : <data> , 'uri': <uri>}
        self.output : List(dict) = [] #  {'format' : <format> , 'uri' : <uri> }
        self.dependencies : List(str) = []
        self.documentation : List(list) = [] # [[type, url], [type, rul], ...]
        self.license : List(str) = []
        self.termsUse : List(str) = []
        self.contribPolicy = False
        self.authors : List(str) = []
        self.repository : List(str) = []
        self.description : List(str) = []
        self.source : List(str) = []
        self.bioschemas : bool  = False
        self.https : bool = False
        self.operational : bool = False
        self.ssl : bool = False
        self.semantics : dict = {}

    def set_super_type(self):
        if self.type in webTypes:
            self.super_type='web'
        else:
            self.super_type='no_web'


    ##============ Findability metrics computation functions ================

    def compF1_2(self):
        '''
        Identifiability of version:
        Whether there is a scheme to uniquely and properly identify the software version.
        A version of the form X.X is considered acceptable: True. Anything else is False
        '''
        if self.version != None:
            vers_veredicts = []
            for v in self.version:
                if len(v.split('.'))==2:
                    vers_veredicts.append(True)
                else:
                    vers_veredicts.append(False)
            # for now, a single True is enough, can be changed in the future, not allowing any False
            if True in vers_veredicts:
                return(True)
        return(False)

    global struct_meta
    # TODO this list must depend on the analyzed sources. Take from config.yaml
    struct_meta = ['bioagents', 'bioconda', 'github', 'bitbucket', 'galaxy', 'agentshed', 'opeb_metrics']
    def compF2_1(self):
        '''
        Structured Metadata
        Metadata is adjusted to specific metdata formats
        The sources in struct_meta are structured. If these sources are among self.source: True. Otherwise: False
        '''
        if True in [a in struct_meta for a in self.source]:
            return(True)
        else:
            return(False)

    def compF2_2(self):
        '''
        Ontologies or controlled vocabularies used
        '''
        # look for EDAM terms
        if self.semantics:
            for k in self.semantics.keys():
                if self.semantics[k]:
                    return(True)
        return(False)


    global softReg
    softReg = ['bioagents', 'bioconda', 'bioconductor']
    def compF3_1(self):
        '''
        Searchability in registries
        Whether software is included in the main software registries.
        If the source is among the software registries: True. Otherwise: Falsecource
        '''
        if True in [a in softReg for a in self.source]:
            return(True)
        else:
            return(False)

    def compF3_2(self):
        '''
        Searchabiliy in software repositories
        Whether software can be found in any of the major software repositories e.g. GitHub, GitLab, SourceForge, 
        If the instance has an associated repository uri: True. Otherwise: False
        '''
        if len(self.repository)>0:
            return(True)
        else:
            return(False)

    def compF3_3(self):
        '''
        Searchability in literature.
        Whether software can be found in specialized literatue services e.g. EuropePMC, PubMed, Journals Site, bioArxiv.
        If the instance at least one associated publication: True. Otherwise: False
        '''
        if len(self.publication)>0:
            return(True)
        else:
            return(False)

    ##============== Accessibility metrics computation functions ================

    def compA1_1(self):
        '''
        WEB
        Existance of API or web 
        Whether it is possible to access a working version of the agent through and API or web. 
        A 200 status when accessing the links provided is consired acceptable.
        '''
        return(self.operational)

    def compA1_2(self):
        '''
        NO WEB
        Existence of downloadable and buildable software working version
        If there is a download link: True ## we do not check if it is available. 
        '''
        if self.super_type == 'no_web':
            if len(self.download)>0:
                return(True)
            else:
                return(False)
        else:
            return(False)

    def compA1_3(self):
        '''
        NO WEB
        Existence of installation instructions
        Whether there is a set of instructions and other necessary information the user can follow to build the software
        We check self.inst_instructions (already a boolean)
        '''
        #print('A1_3', end='\r')
        if self.super_type == 'no_web':
            return(self.inst_instr)
        else:
            return(False)

    def compA1_4(self):
        '''
        Existence of test data
        Whether test data is available
        We check self.test (already a boolean)
        '''
        return(self.test)

    def compA1_5(self):
        '''
        NO WEB
        Existence of software source code
        Whether software source code is available 
        '''
        if self.super_type == 'no_web':
            if len(self.src)>0:
                return(True)
            else:
                return(False)
        else:
            return(False)
    
    def compA3_1(self):
        '''
        WEB
        Registration not compulsory
        Whether homepage can be accessed without registration
        '''
        if self.super_type == 'web':
            return(self.operational)
        else:
            return(True)


    def compA3_2(self):
        '''
        NO WEB
        Availability of version for free OS
        Whether the software can be used in a free operative system
        '''
        if self.super_type == 'no_web':
            if 'Linux' in self.os:
                return(True)
            else:
                return(False)
        else:
            return(True)

    def compA3_3(self):
        '''
        No WEB
        Availability for several OS
        Whether there are versions of the software for several operative systems
        '''
        if self.super_type == 'no_web':
            if len(self.os)>1:
                return(True)
            else:
                return(False)
        else:
            return(False)

    def compA3_4(self):
        '''
        NO WEB
        Availability on free e-Infrastructures
        Whether the software can be used in a free e-infrastructure
        We are only considering galaxy servers and vre
        '''
        if self.super_type == 'no_web':
            eInfra = ['vre.multiscalegenomics.eu', 'galaxy.', 'usegalaxy.']
            for url in self.links:
                for e in eInfra:
                    if e in url:
                        return(True)
                else:
                    return(False)
            return(False)
        else:
            return(False)


    def compA3_5(self):
        '''
        NO WEB
        Availability on several e-Infrastructures
        Whether the software can be used in several e-infrastructure
        '''
        if self.super_type == 'no_web':
            count = 0
            eInfra = ['vre.multiscalegenomics.eu', 'galaxy.', 'usegalaxy.']
            for url in self.links:
                for e in eInfra:
                    if e in url:
                        count += 1
            if count>1:
                return(True)

            return(False)
        else:
            return(False)

    ##============== Interoperability metrics computation functions ================
    def compI1_1(self):
        '''
        Usage of standard data formats
        Whether the input and output datatypes are formally specified and related to accepted ontologies
        '''
        for i in self.input:
            if 'format' in i.keys():
                if i['format']['term'] in stdFormats:
                    return(True)

        for i in self.output:
            if 'format' in i.keys():
                if i['format']['term'] in stdFormats:
                    return(True)

        return(False)

    def compI1_3(self):
        '''
        Verificability of data formats
        Whether input/output data are specified using verifiable schemas (e.g. XDS, Json schema, ...)
        '''
        if self.compI1_1() == True:
            return(True)

        verifiable_formats = ['json', 'xml', 'rdf', 'xds']
        formats = self.input + self.output
        terms = set()
        for i in formats:
            if 'format' in i.keys():
                terms.add(i['format']['term'])
        
        for term in terms:
            if term in verifiable_formats:
                return(True)

        return(False)


        return(False)


    def compI1_4(self):
        '''
        Flexibility of data format supported
        Whether the software allows to choose among various input/output data formats, or provide the necessary agents to convert other common formats into the supported ones.
        '''
        ins = []
        formats = self.input + self.output
        for i in formats:
            if 'format' in i.keys():
                ins.append(i['format']['term'])

        if len(ins)>1:
            return(True)
        else:
            return(False)

    def compI2_1(self):
        '''
        Existence of API/library version 
        Whether the software has API /library versions to be included in users' pipelines
        '''
        interTypes = ['Library', 'Web API']
        for t in self.type:
            if t in interTypes:
                return(True)
        else:
            return(False)


    def compI2_2(self):
        '''
        E-infrastructure compatibility
        '''
        if 'galaxy' in self.source:
            return(True)
        elif 'agentshed' in self.source:
            return(True)
        else:
            return(False)

    def compI3_1(self):
        '''
        Dependencies statement
        Whether the software includes details about dependencies
        '''
        if len(self.dependencies)>0:
            return(True)
        else:
            return(False)

    def compI3_2(self):
        '''
        Dependencies are provided
        Whether the software includes its dependencies or mechanisms to access them
        '''
        # checking source
        if 'galaxyShed' in self.source:
            return(True)
        elif 'bioconda' in self.source:
            return(True)
        elif 'bioconductor' in self.source:
            return(True)
        
        #checking links
        sources_with_dependencies = ['bioconda', 'bioconductor', 'galaxy.']
        for url in self.links:
            if True in  [a in url for a in sources_with_dependencies]:
                return(True)
        
        return(False)

    # ===================== Reusability ==============================================================
    def compR1_1(self):
        '''
        Existence of usage guides
        Whether software user guides are provided
        '''
        noGuide = ['license', 'terms of use', 'news']
        for doc in self.documentation:
            for string in noGuide:
                if string not in doc[0].lower(): # doc[0] is the type of document
                    return(True)

        return(False)


    def compR2_1(self):
        '''
        Existence of license
        Whether license is stated
        '''
        for doc in self.documentation:
            if 'license' in doc[0].lower():
                return(True)
        if self.license:
            if len(self.license)>0:
                return(True)
        return(False)
        
    
    def compR2_2(self):
        '''
        Technical conditions of use
        '''
        for doc in self.documentation:
            if 'conditions of use' in doc[0].lower():
                return(True)
            elif 'terms of use' in doc[0].lower():
                return(True)
        if self.license:
            if len(self.license)>0:
                return(True)

        return(False)
        
    

    #def compR3_1(self):
    def compR3_2(self):
        '''
        Existence of credit
        Whether credit for contributions is provided
        '''
        if len(self.authors)>0:
            return(True)
        else:
            return(False)


    def compR4_1(self):
        '''
        Usage of version control
        Whether the software follows a version-control system
        '''
        for repo in self.repository:
            if 'github' in repo or 'mercurial-scm' in repo:
                return(True)
        return(False)



    def FAIRscores(self):
        self.scores = FAIRscores()
        # ===================== Findability =========================
        # F1
        self.scores.F1 = (0.8*self.metrics.F1_1 
                        + 0.2*self.metrics.F1_2)
        # F2
        self.scores.F2 = 0.6*self.metrics.F2_1 + 0.4*self.metrics.F2_2
        # F3
        acc = [self.metrics.F3_1, self.metrics.F3_2, self.metrics.F3_3].count(True)
        if acc == 1:
            self.scores.F3 = 0.7
        elif acc == 2:
            self.scores.F3 = 0.85
        elif acc == 3:
            self.scores.F3 = 1
        # F
        self.scores.F = (0.4*self.scores.F1
                       + 0.2*self.scores.F2
                       + 0.4*self.scores.F3)
        # ===================== Accessibility =======================
        if self.super_type == 'web':
            # A1
            self.scores.A1 = (0.6*self.metrics.A1_1 
                            + 0.4*self.metrics.A1_4)
            # A3
            self.scores.A3 = 1.0*self.metrics.A3_1 
        else:
            # A1
            self.scores.A1 = (0.5*self.metrics.A1_2 
                            + 0.2*self.metrics.A1_3 
                            + 0.1*self.metrics.A1_4 
                            + 0.2*self.metrics.A1_5)
            # A3
            self.scores.A3 = (1/4)*(self.metrics.A3_2
                                  + self.metrics.A3_3
                                  + self.metrics.A3_4
                                  + self.metrics.A3_5)
        # A
        self.scores.A = (0.7*self.scores.A1
                       + 0.3*self.scores.A3)
        #  A_2 not computable bc we do not have the appropriate metrics.
        #  self.A += (self.metrics.A2_1*(1/3)+self.metrics.A2_2*(2/3))*0.15
        
        # ===================== Interoperability =====================

        # I1
        self.scores.I1 = (0.5*self.metrics.I1_1
                        + 0.3*self.metrics.I1_2
                        + 0.3*self.metrics.I1_3
                        + 0.2*self.metrics.I1_4)
        # I2
        self.scores.I2 = (0.5*self.metrics.I2_1
                        + 0.5*self.metrics.I2_2)
        # I3
        self.scores.I3 = (1/3)*(self.metrics.I3_1
                              + self.metrics.I3_2
                              + self.metrics.I3_3)
        # I
        self.scores.I = (0.6*self.scores.I1
                       + 0.1*self.scores.I2
                       + 0.3*self.scores.I3)
        # ===================== Reusability ===========================

        # R1
        self.scores.R1 = 1.0*self.metrics.R1_1
        # R2
        if self.metrics.R2_1:
            self.scores.R2 = 1.0
        elif self.metrics.R2_2:
            self.scores.R2 = 1.0
        else:
            self.scores.R2 = 0.0
        # R3
        self.scores.R3 = 1.0*self.metrics.R3_2
        # R4
        self.scores.R4 = 1.0*self.metrics.R4_1

        #R
        self.scores.R = (0.3*self.scores.R1
                       + 0.3*self.scores.R2
                       + 0.2*self.scores.R3
                       + 0.2*self.scores.R4)

    def generateFAIRMetrics(self):
        # FINDABILITY
        self.metrics = FAIRmetrics()

        self.metrics.F1_1 = True # all have a name
        self.metrics.F1_2 = self.compF1_2() #
        self.metrics.F2_1 = self.compF2_1()
        self.metrics.F2_2 = self.compF2_2() 

        self.metrics.F3_1 = self.compF3_1()
        self.metrics.F3_2 = self.compF3_2()
        self.metrics.F3_3 = self.compF3_3()
        # ACCESIBILITY
        self.metrics.A1_1 = self.compA1_1() # Existance of API or web 
        self.metrics.A1_2 = self.compA1_2() # Existance of downloadable and buildable software working version
        self.metrics.A1_3 = self.compA1_3() # Existance of installation instructions
        self.metrics.A1_4 = self.compA1_4() # Existance of test data
        self.metrics.A1_5 = self.compA1_5() # Existance of software source code

        self.metrics.A2_1 = False # Metadata of previous versions at software repositories
        self.metrics.A2_2 = False # Existence of accesible previous versions of the software

        self.metrics.A3_1 = self.compA3_1() # Registration compulsory
        self.metrics.A3_2 = self.compA3_2() # Availability of version for free OS
        self.metrics.A3_3 = self.compA3_3() # Availability for several OS
        self.metrics.A3_4 = self.compA3_4() # Availability on free e-Infrastructures
        self.metrics.A3_5 = self.compA3_4() # Availability on several e-Infrastructures

        self.metrics.I1_1 = self.compI1_1()  # Usage of standard data formats
        self.metrics.I1_2 = False # NOT FOR NOW # Usage of standard API framework
        self.metrics.I1_3 = self.compI1_3() # Verificability of data formats
        self.metrics.I1_4 = self.compI1_4() # Flexibility of data format supported
        self.metrics.I1_5 = False # NOT FOR NOW # Generation of provenance information

        self.metrics.I2_1 = self.compI2_1() # Existance of API/library version 
        self.metrics.I2_2 = self.compI2_2() # E-infrastructure compatibility

        self.metrics.I3_1 = self.compI3_1()
        self.metrics.I3_2 = self.compI3_2()
        self.metrics.I3_3 = self.compI3_2() # Same as befor, BY NOW

        self.metrics.R1_1 = self.compR1_1()
        self.metrics.R1_2 = False #NOT FOR NOW

        self.metrics.R2_1 = self.compR2_1()
        self.metrics.R2_2 = self.compR2_2()

        self.metrics.R3_1 = False # Not for now
        self.metrics.R3_2 = self.compR3_2()

        self.metrics.R4_1 = self.compR4_1()
        self.metrics.R4_2 = False # By now
        self.metrics.R4_3 = False # By now


class FAIRscores():
    def __init__(self):
        
        self.F = 0.0 
        self.F1 = 0.0
        self.F2 = 0.0
        self.F3 = 0.0

        self.A = 0.0
        self.A1 = 0.0
        self.A2 = 0.0
        self.A3 = 0.0

        self.I = 0.0
        self.I1 = 0.0
        self.I2 = 0.0
        self.I3 = 0.0

        self.R = 0.0
        self.R1 = 0.0
        self.R2= 0.0
        self.R3 = 0.0
        self.R4 = 0.0


class FAIRmetrics(object):

    def __init__(self):
        self.F1_1 = False # uniqueness of name
        self.F1_2 = False # idenfibiability of version

        self.F2_1 = False # structured metadata
        self.F2_2 = False # standarized metadata

        self.F3_1 = False # searchability in registries
        self.F3_2 = False # searchability in software repositories
        self.F3_3 = False # searchability in literature

        self.A1_1 = False
        self.A1_2 = False
        self.A1_3 = False
        self.A1_4 = False
        self.A1_5 = False

        self.A2_1 = False
        self.A2_2 = False

        self.A3_1 = False
        self.A3_2 = False
        self.A3_3 = False
        self.A3_4 = False
        self.A3_5 = False

        self.I1_1 = False
        self.I1_2 = False
        self.I1_3 = False
        self.I1_4 = False
        self.I1_5 = False

        self.I2_1 = False
        self.I2_2 = False

        self.I3_1 = False
        self.I3_2 = False
        self.I3_3 = False

        self.R1_1 = False
        self.R1_2 = False

        self.R2_1 = False
        self.R2_2 = False

        self.R3_1 = False
        self.R3_2 = False

        self.R4_1 = False
        self.R4_2 = False
        self.R4_3 = False


class canonicalSet(object):

    def __init__(self):
        self.canonicals = []

    def addCanononical(self, canon):
        self.canonicals.append(canon)


class canonicalAgent(object):

    def __init__(self, name, instances, sources, types):
        self.name = name
        self.instances = instances
        self.sources = sources
        self.types = types

    def computeFAIRmetrics(self):
        self.F = max([ins.F for ins in self.instances])
        self.A = max([ins.A for ins in self.instances])
        self.I = max([ins.I for ins in self.instances])
        self.R = max([ins.R for ins in self.instances])



class setOfInstances(object):

    def __init__(self, source):
        self.source = source
        self.instances = []

class agentGenerator(object):
    def __init__(self, agents, source):
        self.agents = agents
        self.source = source

