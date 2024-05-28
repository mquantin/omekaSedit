#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils
import moveDataProp

def contentsAsSetOfTuples(itemPropValues):
    valuesInItem = [tuple(valuedict.values()) for valuedict in utils.harvestExistingValues(itemPropValues)]
    return set(valuesInItem)

def offerUpdateFoundEvent(subjectValueItem, startItem, triggerProp, targetProp):
    #check if values differs
    valuesInStartItem = contentsAsSetOfTuples(startItem[triggerProp])#utils.harvestExistingValues(startItem[triggerProp])
    valuesInTargetItem = contentsAsSetOfTuples(subjectValueItem[targetProp])#utils.harvestExistingValues(subjectValueItem[targetProp])
    symDiff =  valuesInStartItem ^ valuesInTargetItem
    if symDiff:
        print("\tvalue in object item: ", valuesInStartItem)
        print("\tvalue in event item: ", valuesInTargetItem)
        if valuesInTargetItem.issubset(valuesInStartItem):#there are new values, but nothing removed
            print("-> Only new values")
            return input("Do you want to update the value of the event (u) OR skip this item (s), please type (u/s): ")
        elif valuesInTargetItem.isdisjoint(valuesInStartItem):#
            print("-> Disjoint values")
            return input("Do you want to add the value ti the event (a) OR skip this item (s), please type (a/s): ")
        elif valuesInTargetItem.issuperset(valuesInStartItem):#there are removed values, but nothing new
            print("-> Only removed values")
            return input("Do you want:\nto update the value of the event (u) OR skip this item (s), please type (u/s): ")
        else:#there are existing, new and deleted values mixed
            print("-> Existing, Deleted and New values mixed")
            return input("Do you want:\nto update the value of the event (u) OR skip this item (s), please type (u/s): ")
    return ''


#This avoids the undesired cases to be held manualy
#this may find a correct targetItem to be edited
def searchMatch(omeka, startItem, targetItemClassId, rules):
    for subjProperty in startItem.get('@reverse', {}).keys():
        subjectValues = startItem['@reverse'][subjProperty]
        subjectValuesIds = [subjectValue['@id'].rsplit('/', 1)[1] for subjectValue in subjectValues]
        for subjectValueId in subjectValuesIds:
            subjectValueItem = omeka.get_resource_by_id(subjectValueId, resource_type='items')
            subjectValueItemClass = subjectValueItem.get('o:resource_class', {}).get('o:id', None)
            if subjectValueItemClass == targetItemClassId and subjProperty != rules['linkProp']:
                print(f"WARNING: event allready exists, but uses a wrong property ({subjProperty}). Item id: {startItem['o:id']} skipped.")
                # error.append(startItem['o:id'])
                return "error"
            elif subjectValueItemClass != targetItemClassId and subjProperty == rules['linkProp']:
                print(f"WARNING: event allready exists, but uses a wrong class ({subjectValueItemClass}). Item id: {startItem['o:id']} skipped")
                return "error"
            elif subjectValueItemClass == targetItemClassId and subjProperty == rules['linkProp']:
                if len(subjectValues)>1 : 
                    print(f"WARNING: cannot choose. Multiple events connected with the property {rules['linkProp']}. Item id: {startItem['o:id']} skipped")
                    return "error"
                elif rules['targetProp'] in subjectValueItem:
                    print(f"WARNING: target property {rules['targetProp']} allready in event of class {rules['targetItemClass']} connected with the property {rules['linkProp']}. Item id: {startItem['o:id']}")
                    response = offerUpdateFoundEvent(subjectValueItem, startItem, rules['triggerProp'], rules['targetProp'])
                    if response == 'a':
                        return subjectValueItem
                    elif response == 'u':
                        confirm = input("you're about to delete data, are you sure y/n")
                        if confirm == "y":
                            del(subjectValueItem[rules['targetProp']])#remove it, so it will be updated as if it was empty
                            return subjectValueItem
                        else: return "skip"
                    else: 
                        return "skip"
                else:#Item exists, is unique and looks ok. Edit it
                    return subjectValueItem
    return "NA"# when this line is reached, no match has been been found, but no error is to handle, a new event item should be created


def prepareRules(omeka, rules):
    data = {}
    data['itemSetFrom'] = omeka.get_itemset_id(rules['itemSetFrom']) if rules['itemSetFrom'] else None
    data['classFrom'] = omeka.get_resource_by_term(rules['classFrom'], resource_type='resource_classes')
    targetPropId = omeka.get_property_id(rules['targetProp'])
    targetItemClassId = omeka.get_class_id(rules['targetItemClass'])
    targetTemplateId = omeka.get_template_id(rules['targetTemplate'])
    itemSetId = omeka.get_itemset_id(rules['targetItemSet'])
    linkPropId = omeka.get_property_id(rules['linkProp'])
    data['targetLabel'] = rules['targetLabel']
    for searchedThing, userInput in rules.items():
        if not data[searchedThing] and userInput:
           print(f'ERROR, missing omeka resource, no {searchedThing} found')
           return None
    return data

def createEvents(omeka, items, rules):
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

    rules is a dict as follow (example):
        {
        'triggerProp': 'dcterms:date',
        'targetProp': 'crm:P4_has_time-span', 
        'targetItemClass': 'crm:E65_Creation',
        'linkProp': 'crms:p1_has_conceived',
        'action': 'hide' or 'delete' or '',
        'targetTemplate': 'conception',
        'targetLabel': 'creation',
        'targetItemSet': 'CCI itemSet'
        }
    """

    targetPropId = omeka.get_property_id(rules['targetProp'])
    targetItemClassId = omeka.get_class_id(rules['targetItemClass'])
    targetTemplateId = omeka.get_template_id(rules['targetTemplate'])
    itemSetId = omeka.get_itemset_id(rules['targetItemSet'])
    linkPropId = omeka.get_property_id(rules['linkProp'])
    if not (targetPropId and targetItemClassId and targetTemplateId and itemSetId and linkPropId) : 
        print("ERROR missing data in rules or missing omeka resource (template, itemSet, etc.)")
        return [], [], []
    processed = []
    not_proc = []
    error = []
    for startItem in items['results']:
        if rules['triggerProp'] not in startItem:
            not_proc.append(startItem['o:id']) 
            continue
        found = searchMatch(omeka, startItem, targetItemClassId, rules)
        if found == "error":
            error.append(startItem['o:id'])
            continue
        elif found == "skip":
            not_proc.append(startItem['o:id']) 
            continue
        elif found == "NA":#no event found, create a new event item
            itemName = startItem['o:title'].split(' - ', 1)[0]
            eventLabel = rules['targetLabel'] + ' de ' + itemName
            print('CREATED:', eventLabel)
            terms = {
                'skos:prefLabel': [
                    {
                        'value': eventLabel
                    }
                ],
                rules['linkProp'] : [
                    {
                        'value': startItem['o:id'],
                        'type': 'resource:item',
                    },
                ]
            }
            new_item = omeka.prepare_item_payload_using_template(terms, targetTemplateId)#a new item
        else: #edit existing event 
            print('FOUND item n°', found['o:id'])
            new_item = deepcopy(found)# edit existing item matching the criterias of serachMatch
        # newPropValues = [{'value': value.get(''), 'type': 'uri', 'label': E55Type.label} for value in startItem[mapping['triggerProp']]]
        # newPropValues = [
        #     {
        #         'value': value['@value'].strip(), 
        #         'type': 'uri', 
        #         'label': value['@value'].strip()
        #     } for value in startItem[mapping['triggerProp']] if '@id' in value]#all the uri / internal omeka resources
        # newPropValues += [value['@value'].strip() for value in propValues if '@value' in value]#all the litterals

        # new_item = utils.add_to_prop(omeka, new_item, targetPropId, mapping['targetProp'], newPropValue)
        
        # just copies the content of trigger prop into the target prop
        new_itempropValues = new_item.setdefault(rules['triggerProp'], [])
        new_itempropValues += [value for value in startItem[rules['triggerProp']]]
        #then move the content to the targetprop if targetProp != triggerProp
        if rules['triggerProp'] != rules['targetProp']:
            new_item = moveDataProp.moveDataPropOfitem(omeka, new_item, rules['triggerProp'], rules['targetProp'], targetPropId, delFrom = True)
        #update or create depending on the case
        if found == "NA": omeka.add_item(new_item, template_id = targetTemplateId, class_id = targetItemClassId, item_set_id = itemSetId)
        else : omeka.update_resource(new_item, 'items')
        
        ##################################
        # actions on startIitem properties
        update_startItem = deepcopy(startItem)
        if rules['action'] == 'hide':
            update_startItem = utils.hideValues(update_startItem, rules['triggerProp'])
        elif rules['action'] == 'delete':
            update_startItem = utils.removeValues(update_startItem, rules['triggerProp'])
        omeka.update_resource(update_startItem, 'items')
        processed.append(startItem['o:id'])
    return processed, not_proc, error
                    

            
