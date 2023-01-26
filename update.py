#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omeka_s_tools.api import OmekaAPIClient

with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)

omeka = OmekaAPIClient('https://epotec.univ-nantes.fr/api', 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )


data = omeka.search_items(None, resource_class_id=162, )

print(data['total_results'])
for origItem in data['results']:
    #print what we're talking about
    print(origItem['o:title'])
    print(origItem['o:thumbnail'])
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

