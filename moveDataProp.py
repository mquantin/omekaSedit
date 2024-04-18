#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils

def moveDataPropOfitem(omeka, item, propFrom, propTo, propTo_id, delFrom):
    if propFrom not in item:
        return False
    new_item = deepcopy(item)
    #catches the content to be copied for each occurence in the propFrom of the item (maybe several values for the same prop)
    newPropvalues = utils.harvestExistingValues(new_item[propFrom])
    new_item = utils.add_to_prop(omeka, new_item, propTo_id, propTo, newPropvalues)
    if delFrom:
        del new_item[propFrom]
    return new_item


def moveDataProp(omeka, items, propFrom, propTo, delFrom = False):
    """
    propFrom and propTo are string like  'crm:P5_consists_of' and 'crm:P45_consists_of'
    """
    propTo_id = omeka.get_property_id(propTo)
    processed, not_proc, error = [], [], []
    for origItem in items['results']:
        print('processing item id n°',origItem['o:id'])
        new_item = moveDataPropOfitem(omeka, origItem, propFrom, propTo, propTo_id, delFrom)
        processed.append(origItem['o:id']) if new_item else error.append(origItem['o:id']) 
        updated_item = omeka.update_resource(new_item, 'items')
        assert origItem['o:id'] == updated_item['o:id']            
    return processed, not_proc, error
