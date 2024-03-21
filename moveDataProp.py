#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils

def moveDataProp(omeka, items, propFrom, propTo, delFrom = False):
    """
    propFrom and propTo are string like  'crm:P5_consists_of' and 'crm:P45_consists_of'
    """
    propTo_id = omeka.get_property_id(propTo)
    processed = []
    not_proc = []
    error = []
    for origItem in items['results']:
        if propFrom not in origItem:
            not_proc.append(origItem['o:id']) 
            continue
        print('processing item id n°',origItem['o:id'])
        new_item = deepcopy(origItem)
        #catches the content to be copied for each occurence in the propFrom of the item (maybe several values for the same prop)
        newPropvalues = []
        for origPropValue in new_item[propFrom]:
            origPropValueContent = None
            if origPropValue['type'] == 'uri':
                origPropValueContent = origPropValue['@id']
                newPropvalues += {'value': origPropValueContent, 'type': 'uri', 'label': origPropValue['o:label']}
            elif origPropValue['type'] == 'literal':
                origPropValueContent = origPropValue['@value']
                newPropvalues += {'value': origPropValueContent, 'type': 'literal'}
            else:
                error.append(origItem['o:id']) 
                raise ValueError("property value is unclear, nor uri, nor litteral", origPropValue)
        new_item = utils.add_to_prop(omeka, new_item, propTo_id, propTo, newPropvalues)
        processed.append(origItem['o:id']) 
        if delFrom:
            del new_item[propFrom]
            print('deleteing values of ', propFrom )
        updated_item = omeka.update_resource(new_item, 'items')
        assert origItem['o:id'] == updated_item['o:id']            
    return processed, not_proc, error
