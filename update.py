#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omeka_s_tools.api import OmekaAPIClient

#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)

omeka = OmekaAPIClient('https://epotec.univ-nantes.fr/api', 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )



# # search items by class
# items = omeka.search_items(None, resource_class_id=omeka.get_property_id('crm:E21_Person'), )

# # search items by property value
# items = omeka.filter_items_by_property(filter_property='crm:P5_consists_of', filter_value='', filter_type='in')

items = omeka.search_items('Baccarat ')

print(items['total_results'])


def moveProp():
    for origItem in items['results']:
        #print what we're talking about
        if 'crm:P5_consists_of' in origItem:
            new_item = deepcopy(origItem)
            print(new_item['crm:P5_consists_of'])
            new_item['crm:P45_consists_of'] = []
            prepare_property_value(value, property_id)
            for index, material in enumerate(new_item['crm:P5_consists_of']):
                print(material)
                new_item['crm:P45_consists_of'] += {'type': 'uri', '@id': material['@id'], 'o:label': material['o:label']}
            #del new_item['crm:P5_consists_of']
            updated_item = omeka.update_resource(new_item, 'items')
            assert origItem['o:id'] == updated_item['o:id']


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
    
moveProp()