#!python3
# -*- coding: utf-8 -*-

import yaml
from collections import namedtuple
###local imports
from omekastoolsFork import OmekaAPIClient
import utils
from moveDataProp import moveDataProp
from updateClass import updateClass
from updateThumbnail import updateThumbnail
from createEvents import createEvents



#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)

omeka = OmekaAPIClient(apiKey['APIurl'], 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )
search = True


def listClasses():
    pageNum=0
    allClasses = {}
    search = True
    while search:
        pageNum+=1
        APIitems = utils.getItemsinPage(omeka, pageNum, itemSetName='CCI itemSet')
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            seenClasses = utils.checkClasses(APIitems)
            for key, values in seenClasses.items():
                allClasses.setdefault(key, []).extend(values)
    print("\n\n###################### Classes")
    for classID, itemsID in allClasses.items():
        classTerm = omeka.get_resource_by_id(classID, resource_type='resource_classes')['o:term']
        print(f"class id: {classID}\nclass term: {classTerm}\nconcerned item count: {len(itemsID)}")
        print("id of concerned items :", itemsID)
        print("\n")


def callCreateEvents():
    rules = {
        'triggerProp': 'dcterms:date',
        'targetProp': 'crm:P4_has_time-span', 
        'targetItemClass': 'crm:E65_Creation',
        'linkProp': 'crms:P1_has_conceived',
        'action': 'hide',
        'targetTemplate': 'conception',
        'targetLabel': 'creation',
        'targetItemSet': 'CCI itemSet'
        }
    pageNum=0
    processedItemsId, not_procItemsId, errorItemsId = [], [], []
    search = True
    while search:
        pageNum+=1
        APIitems = utils.getItemsinPage(omeka, pageNum, itemSetName='CCI itemSet')
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            processed, not_proc, error = createEvents(omeka, APIitems, rules)
            processedItemsId += processed
            not_procItemsId += not_proc
            errorItemsId += error
        break#only one page
    utils.printMutation("CREATE EVENTS", processedItemsId, not_procItemsId, errorItemsId)

def callUpdateClass():
    E55type = namedtuple('E55type', 'uri label')
    rules = {
        'classFrom': 'crm:E31_Document',
        'classTo': 'crm:E22_Human-Made_Object', 
        'templateTo': 'mobilier',
        'templateFrom': False,#optional, value may be False
        'E55TypeValue': E55type(uri="https://vocab.getty.edu/aat/300026685", label="Documents (AAT)"),#optional, value may be False
        }
    pageNum=0
    processedItemsId, not_procItemsId, errorItemsId = [], [], []
    search = True
    while search:
        pageNum+=1
        APIitems = utils.getItemsinPage(omeka, pageNum, itemSetName='CCI itemSet')
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            processed, not_proc, error = updateClass(omeka, APIitems, rules)
            processedItemsId += processed
            not_procItemsId += not_proc
            errorItemsId += error
    utils.printMutation("CLASS UPDATE", processedItemsId, not_procItemsId, errorItemsId)

def callMoveDataProp():
    pageNum=0
    processedItemsId, not_procItemsId, errorItemsId = [], [], []
    search = True
    while search:
        pageNum+=1
        APIitems = utils.getItemsinPage(omeka, pageNum, itemSetName='CCI itemSet')
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            processed, not_proc, error = moveDataProp(omeka, APIitems, "dcterms:type", propTo = 'crm:P2_has_type', delFrom = True)
            processedItemsId += processed
            not_procItemsId += not_proc
            errorItemsId += error
    utils.printMutation("MOVED DATA PROP", processedItemsId, not_procItemsId, errorItemsId)

callCreateEvents()