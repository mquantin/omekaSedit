#!python3
# -*- coding: utf-8 -*-

import yaml
from collections import namedtuple
###local imports
from omekastoolsFork import OmekaAPIClient
import utils
from moveDataProp import moveDataProp
import updateClass
from updateThumbnail import updateThumbnail
import createEvents



#read credential API as a yaml file
with open("APIkey.yaml", 'r') as stream:
    apiKey = yaml.safe_load(stream)

omeka = OmekaAPIClient(apiKey['APIurl'], 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )
search = True


def listClasses():
    itemSetId = omeka.get_itemset_id('CCI itemSet')
    pageNum=0
    allClasses = {}
    search = True
    while search:
        pageNum+=1
        APIitems = omeka.search_items('',  item_set_id = itemSetId, page = pageNum)
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
        'classFrom': 'crm:E22_Human-Made_Object',#optional, filters the resources, value may be None
        'itemSetFrom': 'CCI itemSet',#optional, filters the resources, value may be None
        'triggerProp': 'crm:P32_used_general_technique',
        'targetProp': 'crm:P32_used_general_technique', 
        'targetItemClass': 'crm:E12_Production',
        'linkProp': 'crm:P108_has_produced',
        'action': 'hide',
        'targetTemplate': None,#'production',
        'targetLabel': 'production',
        'targetItemSet': 'CCI itemSet',
        'team': [1,]
        }
    # rules = {
    #     'classFrom': 'crm:E22_Human-Made_Object',
    #     'itemSetFrom': 'CCI itemSet',
    #     'triggerProp': 'dcterms:date',
    #     'targetProp': 'crm:P4_has_time-span', 
    #     'targetItemClass': 'crm:E65_Creation',
    #     'linkProp': 'crms:P1_has_conceived',
    #     'action': 'hide',#'delete',
    #     'targetTemplate': None,#'conception',
    #     'targetLabel': 'creation',
    #     'targetItemSet': 'CCI itemSet',
    #     'team': [1,]
    #     }
    # rules = {
    #     'classFrom': 'crm:E22_Human-Made_Object',
    #     'itemSetFrom': 'CCI itemSet',
    #     'triggerProp': 'dcterms:creator',
    #     'targetProp': 'crm:P14_carried_out_by', 
    #     'targetItemClass': 'crm:E65_Creation',
    #     'linkProp': 'crms:P1_has_conceived',
    #     'action': 'hide',
    #     'targetTemplate': None,#'conception',
    #     'targetLabel': 'creation',
    #     'targetItemSet': 'CCI itemSet',
    #     'team': [1,]
    #     }
    dataRules = createEvents.prepareRules(omeka, rules)
    if not dataRules:#some rules has not been found
        return
    pageNum=0
    processedItemsId, not_procItemsId, errorItemsId = [], [], []
    search = True
    while search:
        pageNum+=1
        APIitems = omeka.search_items('', 
                                      item_set_id = dataRules['itemSetFrom'], 
                                      resource_class_id = dataRules['classFrom']['o:id'], 
                                      page=pageNum)
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            processed, not_proc, error = createEvents.createEvents(omeka, APIitems, dataRules)
            processedItemsId += processed
            not_procItemsId += not_proc
            errorItemsId += error
    utils.printMutation("CREATE EVENTS", processedItemsId, not_procItemsId, errorItemsId)


def callUpdateClass():
    E55type = namedtuple('E55type', 'uri label')
    # rules = {
    #     'itemSetFrom': 'CCI itemSet',
    #     'classFrom': 'crm:E36_Visual_Item',
    #     'classTo': 'crm:E22_Human-Made_Object', 
    #     'templateTo': 'mobilier',
    #     'templateFrom': None,#optional, value may be None
    #     'E55TypeValue': E55type(uri="https://vocab.getty.edu/aat/300191086", label="Visual Works (AAT)"),#optional, value may be None
    #     }
    rules = {
        'itemSetFrom': 'CCI itemSet',
        'classFrom': 'crm:E31_Document',
        'classTo': 'crm:E22_Human-Made_Object', 
        'templateTo': 'mobilier',
        'templateFrom': None,#optional, value may be None
        'E55TypeValue': E55type(uri="https://vocab.getty.edu/aat/300026685", label="Documents (AAT)"),#optional, value may be None
        }
    dataRules = updateClass.prepareRules(omeka, rules)
    if not dataRules:#some rules has not been found
        return
    print(f"#### UPDATE CLASSES ####")
    print(f"""
    item set from\n\tlabel: {rules['itemSetFrom']} \n\tid: {dataRules['itemSetFrom']}
    template to\n\tlabel: {rules['templateTo']} \n\tid: {dataRules['templateTo']['o:id']}
    class from\n\tterm: {dataRules['classFrom']['o:term']} \n\tid: {dataRules['classFrom']['o:id']}
    class to\n\tterm: {dataRules['classTo']['o:term']} \n\tid: {dataRules['classTo']['o:id']}
    """)
    pageNum=0
    processedItemsId, not_procItemsId, errorItemsId = [], [], []
    search = True
    while search:
        pageNum+=1
        #APIitems = utils.getItemsinPage(omeka, pageNum, itemSetId=dataRules['itemSetFrom'], resourceClassId=dataRules['classFrom']['o:id'])
        APIitems = omeka.search_items('', 
                                      item_set_id = dataRules['itemSetFrom'], 
                                      resource_class_id = dataRules['classFrom']['o:id'], 
                                      page=pageNum)
        if pageNum == 1:#on first loop only
            totalResults, pagesQ = utils.getQuantities(APIitems)
            print(f"nombre d'item total: {totalResults}")
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            print(f"\npage: {pageNum}/{pagesQ}")
            processed, not_proc, error = updateClass.updateClass(omeka, APIitems, dataRules)
            processedItemsId += processed
            not_procItemsId += not_proc
            errorItemsId += error
        else: 
            print(f"no more items")
    utils.printMutation("CLASS UPDATE", processedItemsId, not_procItemsId, errorItemsId)


def callMoveDataProp():
    rules = {
        'itemSetFrom': 'CCI itemSet',
        'propFrom': 'dcterms:identifier',
        'propTo': 'crm:P48_has_preferred_identifier', 
        'delFrom': 'True',
        }
    # rules = {
    #     'itemSetFrom': 'CCI itemSet',
    #     'propFrom': 'dcterms:type',
    #     'propTo': 'crm:P2_has_type', 
    #     'delFrom': 'True',
    #     }
    # rules = {
    #     'itemSetFrom': 'CCI itemSet',
    #     'propFrom': 'crm:P5_consists_of',
    #     'propTo': 'crm:P45_consists_of', 
    #     'delFrom': 'True',
    #     }
    itemSetID = omeka.get_itemset_id(rules['itemSetFrom'])
    pageNum=0
    processedItemsId, not_procItemsId, errorItemsId = [], [], []
    search = True
    print(f"#### MOVING PROP VALUE ####")
    print(f"""
    item set from\n\tlabel: {rules['itemSetFrom']} \n\tid: {itemSetID}
    property from\n\tlabel: {rules['propFrom']} \n\tid: 
    property to\n\tterm: {rules['propTo']} \n\tid: 
    delete source prop : {rules['delFrom']}
    """)
    while search:
        pageNum+=1
        # APIitems = utils.getItemsinPage(omeka, pageNum, itemSetId=itemSetId)
        APIitems = omeka.filter_items_by_property(
            filter_property=rules['propFrom'], 
            filter_type='ex', 
            item_set_id = itemSetID, 
            page=pageNum)
        if pageNum == 1:#on first loop only
            totalResults, pagesQ = utils.getQuantities(APIitems)
            print(f"nombre d'item total: {totalResults}")
        search = len(APIitems['results'])#0 quand il n'y a plus rien 
        if search:
            print(f"\npage: {pageNum}/{pagesQ}")
            processed, not_proc, error = moveDataProp(omeka, APIitems, rules)
            processedItemsId += processed
            not_procItemsId += not_proc
            errorItemsId += error
    utils.printMutation("MOVED DATA PROP", processedItemsId, not_procItemsId, errorItemsId)

# listClasses()
# callUpdateClass()
callCreateEvents()
# callMoveDataProp()