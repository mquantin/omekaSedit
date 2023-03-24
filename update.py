#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omeka_s_tools.api import OmekaAPIClient

#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)

import os
import requests
session = requests.Session()
session.verify = False
session.trust_env = False
os.environ['CURL_CA_BUNDLE']="" # or whaever other is interfering with 

omeka = OmekaAPIClient('http://epotec.univ-nantes.fr/api', 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )



# # search items by class
# items = omeka.search_items(None, resource_class_id=omeka.get_property_id('crm:E21_Person'), )

# # search items by property value
# items = omeka.filter_items_by_property(filter_property='crm:P5_consists_of', filter_value='', filter_type='in')

items = omeka.search_items('Baccarat ')

print("nombre d'item trouvés:",items['total_results'])

moveDataFromProp = 'crm:P5_consists_of'
moveDataToProp = 'crm:P45_consists_of'

def moveDataProp(itemsToChange, fromProp, toProp, delFrom = False):
    for origItem in itemsToChange['results']:
        #print what we're talking about
        if fromProp in origItem:
            new_item = deepcopy(origItem)
            new_item[toProp] = []
            for propValue in new_item[fromProp]:
                print(propValue)
                if propValue['type'] == 'uri':
                    new_item[toProp] += {'type': 'uri', 'id': propValue['@id'], 'o:label': propValue['o:label']}
                elif propValue['type'] == 'literal':
                    new_item[toProp] += {'type': 'literal', 'value': propValue['@value']}
                else:
                    raise ValueError("property value is unclear", propValue)
            if 'o:resource_template' in new_item:
                templateId = new_item['o:resource_template']['o:id']
                newItemPayload = omeka.prepare_item_payload_using_template(new_item, templateId)
            else:
                newItemPayload = omeka.prepare_item_payload(new_item)
            print('here')
            updated_item = omeka.update_resource(newItemPayload, 'items')
            assert origItem['o:id'] == updated_item['o:id']
            if delFrom:
                del new_item[moveDataFromProp]



def updateThumbnail():
    for origItem in items['results']:
        #print what we're talking about
        print(origItem['o:title'])
        # Copy and modify the original item
        new_item = deepcopy(origItem)
        new_item['o:thumbnail'] = {
            '@id': "https://172.26.70.170/api/assets/37",
            'o:id': 37}

        print(new_item['o:thumbnail'])
        # Update the item 
        updated_item = omeka.update_resource(new_item, 'items')

        # The id of the original and upated items should be the same
        assert origItem['o:id'] == updated_item['o:id']
    
moveDataProp(items, moveDataFromProp, moveDataToProp, delFrom = False)