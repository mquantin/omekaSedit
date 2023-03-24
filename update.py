#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omeka_s_tools.api import OmekaAPIClient

#### no SSL script
import warnings
import contextlib

import requests
from urllib3.exceptions import InsecureRequestWarning

old_merge_environment_settings = requests.Session.merge_environment_settings

@contextlib.contextmanager
def no_ssl_verification():
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False

        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings

        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass
####


#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)


omeka = OmekaAPIClient('https://172.26.70.170/api', 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )



# # search items by class
# items = omeka.search_items(None, resource_class_id=omeka.get_property_id('crm:E21_Person'), )

# # search items by property value
# items = omeka.filter_items_by_property(filter_property='crm:P5_consists_of', filter_value='', filter_type='in')
with no_ssl_verification():
    items = omeka.search_items('')

print("nombre d'item trouvés:",items['total_results'])

moveDataFromProp = 'crm:P5_consists_of'
moveDataToProp = 'crm:P45_consists_of'

def moveDataProp(itemsToChange, fromProp, toProp, delFrom = False):
    for origItem in itemsToChange['results']:
        #print what we're talking about
        if fromProp in origItem:
            print('processing item n°',origItem['o:id'])
            new_item = deepcopy(origItem)
            # managing existing values in target prop
            toPropValues = new_item.setdefault(toProp, [])#the key of the toProp is totally abitrary, useless
            existingIds = []
            existingIds += [value['@id'] for value in toPropValues if '@id' in value]
            existingIds += [value['@value'] for value in toPropValues if '@value' in value]
            toProp_id = omeka.get_property_id(toProp)
            for origPropValue in new_item[fromProp]:
                if origPropValue['type'] == 'uri':
                    checking = '@id'
                    newPropvalue = {'value': origPropValue['@id'], 'type': 'uri', 'label': origPropValue['o:label']}
                elif origPropValue['type'] == 'literal':
                    checking = '@value'
                    newPropvalue = {'value': origPropValue['@value'], 'type': 'literal'}
                else:
                    raise ValueError("property value is unclear", propValue)
                if origPropValue[checking] in existingIds:
                    print('skiped ', origPropValue[checking], ' to avoid duplicate' )
                    continue
                formatted_newProp = omeka.prepare_property_value(newPropvalue, toProp_id)
                toPropValues += [formatted_newProp,]
            # if new_item['o:resource_template']:
            #     templateId = new_item['o:resource_template']['o:id']
            #     newItemPayload = omeka.prepare_item_payload_using_template(new_item, templateId)
            # else:
            #     newItemPayload = omeka.prepare_item_payload(new_item)
            if delFrom:
                del new_item[moveDataFromProp]
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

with no_ssl_verification():
    moveDataProp(items, moveDataFromProp, moveDataToProp, delFrom = True)