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
pageNum=0
search = True
processedItemsId = []
not_procItemsId = []
errorItemsId = []
allClasses = {}
E55type = namedtuple('E55type', 'uri label')
mapping = {
        'triggerProp': 'dcterms:date',
        'targetProp': 'crm:P4_has_time-span', 
        'targetItemClass': 'crm:E65_Creation',
        'linkProperty': 'crms:p1_has_conceived',
        'action': 'hide',
        'targetTemplate': 'creation',
        'targetLabel': 'creation',
        'targetItemSet': 'CCI itemSet'
        }



while search:
    pageNum+=1
    APIitems = utils.getItemsinPage(omeka, pageNum, itemSetName='CCI itemSet')
    search = len(APIitems['results'])#0 quand il n'y a plus rien 
    if search:
        seenClasses = utils.checkClasses(APIitems)
        for key, values in seenClasses.items():
            allClasses.setdefault(key, []).extend(values)
        #processed, not_proc, error = updateClass(APIitems, 'crm:E31_Document', 'crm:E22_Human-Made_Object', templateTo = 'mobilier', E55Type = E55type(uri="https://vocab.getty.edu/aat/300026685", label="Documents (AAT)"))
        #processed, not_proc, error = moveDataProp(omeka, APIitems, "dcterms:type", propTo = 'crm:P2_has_type', delFrom = True)
        processed, not_proc, error = createEvents(omeka, APIitems, mapping)
        processedItemsId += processed
        not_procItemsId += not_proc
        errorItemsId += error



print("\n\n###################### Classes")
for classID, itemsID in allClasses.items():
    classTerm = omeka.get_resource_by_id(classID, resource_type='resource_classes')['o:term']
    print(f"class id: {classID}\nclass term: {classTerm}\nconcerned item count: {len(itemsID)}")
    print("id of concerned items :", itemsID)
    print("\n")

print("\n\n###################### Mutations")
print(f"processed: {len(processedItemsId)} \tskipped (error): {len(errorItemsId)} \tnot processed: {len(not_procItemsId)}")
print(f"processed items ids: {processedItemsId}")
if errorItemsId:
    print(f"error (skiped) items ids: {errorItemsId}")
#print(f"not processed items ids: {not_procItemsId}")