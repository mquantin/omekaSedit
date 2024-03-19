#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils




#This avoids the undesired cases to be held manualy
#this may find a correct targetItem to be edited
def searchMatch(omeka, startItem, targetItemClassId, mapping):
    for subjProperty in startItem.get('@reverse', default={}).keys():
        subjectValues = startItem['@reverse'][subjProperty]
        subjectValuesIds = [subjectValue['id'].rsplit('/', 1)[1] for subjectValue in subjectValues]
        for subjectValueId in subjectValuesIds:
            subjectValueItem = omeka.get_resource_by_id(subjectValueId, resource_type='items')
            subjectValueItemClass = subjectValueItem.get('o:resource_class', {}).get('o:id', None)
            if subjectValueItemClass == targetItemClassId and subjProperty != mapping['linkProperty']:
                print(f'WARNING: event allready exists, but uses a wrong property ({subjProperty}). Item id: {startItem['o:id']}')
                # error.append(startItem['o:id'])
                return "error"
            elif subjectValueItemClass != targetItemClassId and subjProperty == mapping['linkProperty']:
                print(f'WARNING: event allready exists, but uses a wrong class ({subjectValueItemClass}). Item id: {startItem['o:id']}')
                return "error"
            elif subjectValueItemClass == targetItemClassId and subjProperty == mapping['linkProperty']:
                if len(subjectValues)>1 : 
                    print(f'WARNING: multiple events connected with the property {mapping['linkProperty']}. Item id: {startItem['o:id']}')
                    return "error"
                elif mapping['targetProp'] in subjectValueItem:
                    print(f'WARNING: target property {mapping['targetProp']} allready in event of class {mapping['targetItemClass']} connected with the property {mapping['linkProperty']}. Item id: {startItem['o:id']}')
                    return "error"
                else:#Item exists, is unique and looks ok. Edit it
                    return subjectValueItem
    return "NA"# when this line is reached, no match has been been found, but no error is to handle, a new event item should be created


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
        'targetTemplate': 'creation',
        'targetLabel': 'creation',
        'targetItemSet': 'CCI itemSet'
        }
    """

    targetPropId = omeka.get_property_id(mapping['targetProp'])
    targetItemClassId = omeka.get_class_id(mapping['targetItemClass'])
    targetTemplateId = omeka.get_template_id(mapping['targetTemplate'])
    itemSetId = omeka.get_itemset_id(mapping['targetItemSet'])
    processed = []
    not_proc = []
    error = []
    for startItem in items['results']:
        if mapping['triggerProp'] not in startItem:
            not_proc.append(startItem['o:id']) 
            continue
        found = searchMatch(omeka, startItem, targetItemClassId, mapping)
        if found == "error":
            error.append(startItem['o:id'])
            continue
        elif found == "NA":
            itemName = startItem['o:title'].rsplit(' - ', 1)[1]
            eventLabel = mapping['targetLabel'] + ' de ' + itemName
            print('CREATED:', eventLabel)
            terms = {
                'skos:prefLabel': [
                    {
                        'value': eventLabel
                    }
                ]
            }
            new_item = omeka.prepare_item_payload_using_template(terms, targetTemplateId)#a new item
        else: 
            new_item = deepcopy(found)# edit existing item matching the criterias of serachMatch
        newPropValue = startItem[mapping['triggerProp']]#{'value': E55Type.uri, 'type': 'uri', 'label': E55Type.label}
        new_item = utils.add_to_prop(omeka, new_item, targetPropId, 'crm:P2_has_type', newPropValue)
        updated_item = omeka.update_resource(new_item, 'items')
        processed.append(startItem)
    return processed, not_proc, error
                    

            
