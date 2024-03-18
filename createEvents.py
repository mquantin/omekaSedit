#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils




def createEvents(omeka, items, mapping):
    """
    WARNING: items have to be smartly filtered to avoid side effects!
    For each startItem with property triggerProp 
    if startItem is already linked with linkProperty from a targetItem of targetItemClass:
        if targetItem has no property targetProp:
        move the value content of triggerProp to targetProp in the existing targetItem
        else:
        warn
    else if startItem is already linked with any other property from a targetItem of targetItemClass:
        warn
    else if is already linked with linkProperty from a targetItem of any class:
        warn
    else if
        create a new targetItem with targetItemClass as class
        move the value content of triggerProp to targetProp in that targetItem
        create a linkProperty in that targetItem, pointing to our startItem

    Mapping is a dict as follow (example):
        {
        'triggerProp': 'dcterms:date',
        'targetProp': 'crm:P4_has_time-span', 
        'targetItemClass': 'crm:E65_Creation',
        'linkProperty': 'crms:p1_has_conceived',
        'action': 'hide' or 'delete',
        }
    """

    propTo_id = omeka.get_property_id(mapping['targetProp'])
    targetItemClassId = omeka.get_class_id(mapping['targetItemClass'])
    processed = []
    not_proc = []
    error = []
    for startItem in items['results']:
        if mapping['triggerProp'] not in startItem:
            not_proc.append(startItem['o:id']) 
            continue
        eventFound = None
        #This avoids the undesired cases to be held manualy
        for subjProperty in startItem.get('@reverse', default={}).keys():
            subjectValues = startItem['@reverse'][subjProperty]
            subjectValuesIds = [subjectValue['id'].rsplit('/', 1)[1] for subjectValue in subjectValues]
            for subjectValueId in subjectValuesIds:
                subjectValueItem = omeka.get_resource_by_id(subjectValueId, resource_type='items')
                subjectValueItemClass = subjectValueItem.get('o:resource_class', {}).get('o:id', None)
                if subjectValueItemClass == targetItemClassId and subjProperty != mapping['linkProperty']:
                    print(f'WARNING: event allready exists, but uses a wrong property ({subjProperty}). Item id: {startItem['o:id']}')
                    error.append(startItem['o:id'])
                elif subjectValueItemClass != targetItemClassId and subjProperty == mapping['linkProperty']:
                    print(f'WARNING: event allready exists, but uses a wrong class ({subjectValueItemClass}). Item id: {startItem['o:id']}')
                    error.append(startItem['o:id']) 
                elif subjectValueItemClass == targetItemClassId and subjProperty == mapping['linkProperty']:
                    if len(subjectValues)>1 : 
                        print(f'WARNING: multiple events connected with the property {mapping['linkProperty']}. Item id: {startItem['o:id']}')
                        error.append(startItem['o:id']) 
                    else:#Item exists, is unique and looks ok. Edit it
                        eventFound = subjectValueItem
        if eventFound:#Edit existing item
            if mapping['targetProp'] in eventFound:
                print(f'WARNING: target property {mapping['targetProp']} allready in event of class {mapping['targetItemClass']} connected with the property {mapping['linkProperty']}. Item id: {startItem['o:id']}')
                error.append(startItem['o:id']) 
            else:
                
        else:#event should be created
            
                    

            
