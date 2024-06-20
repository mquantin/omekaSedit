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
def searchMatch(omeka, startItem, dataRules):
    for subjProperty in startItem.get('@reverse', {}).keys():
        subjectValues = startItem['@reverse'][subjProperty]
        subjectValuesIds = [subjectValue['@id'].rsplit('/', 1)[1] for subjectValue in subjectValues]
        for subjectValueId in subjectValuesIds:
            subjectValueItem = omeka.get_resource_by_id(subjectValueId, resource_type='items')
            subjectValueItemClass = subjectValueItem.get('o:resource_class', {}).get('o:id', None)
            if subjectValueItemClass == dataRules['targetItemClass']['o:id'] and subjProperty != dataRules['linkProp']['o:term']:
                print(f"WARNING: event allready exists, but uses a wrong property ({subjProperty}). Item id: {startItem['o:id']} skipped.")
                # error.append(startItem['o:id'])
                return "error"
            elif subjectValueItemClass != dataRules['targetItemClass']['o:id'] and subjProperty == dataRules['linkProp']['o:term']:
                print(f"WARNING: event allready exists, but uses a wrong class ({subjectValueItemClass}). Item id: {startItem['o:id']} skipped")
                return "error"
            elif subjectValueItemClass == dataRules['targetItemClass']['o:id'] and subjProperty == dataRules['linkProp']['o:term']:
                if len(subjectValues)>1 : 
                    print(f"WARNING: cannot choose. Multiple events connected with the property {dataRules['linkProp']['o:term']}. Item id: {startItem['o:id']} skipped")
                    return "error"
                elif dataRules['targetProp']['o:term'] in subjectValueItem:
                    print(f"WARNING: target property {dataRules['targetProp']['o:term']} allready in event of class {dataRules['targetItemClass']['o:term']} connected with the property {dataRules['linkProp']['o:term']}. Item id: {startItem['o:id']}")
                    response = offerUpdateFoundEvent(subjectValueItem, 
                                                     startItem, 
                                                     dataRules['triggerProp']['o:term'], 
                                                     dataRules['targetProp']['o:term'])
                    if response == 'a':
                        return subjectValueItem
                    elif response == 'u':
                        confirm = input("you're about to delete data, are you sure y/n")
                        if confirm == "y":
                            del(subjectValueItem[dataRules['targetProp']['o:term']])#remove it, so it will be updated as if it was empty
                            return subjectValueItem
                        else: return "skip"
                    else: 
                        return "skip"
                else:#Item exists, is unique and looks ok. Edit it
                    return subjectValueItem
    return "NA"# when this line is reached, no match has been been found, but no error is to handle, a new event item should be created


def prepareRules(omeka, rules):
        # rules = {
        # 'classFrom': 'crm:E22_Human-Made_Object',#optional, filters the resources, value may be None
        # 'itemSetFrom': 'CCI itemSet',#optional, filters the resources, value may be None
        # 'triggerProp': 'crm:P32_used_general_technique',
        # 'targetProp': 'crm:P32_used_general_technique', 
        # 'targetItemClass': 'crm:E12_Production',
        # 'linkProp': 'crm:P108_has_produced',
        # 'action': 'hide',
        # 'targetTemplate': 'production',
        # 'targetLabel': 'production',
        # 'targetItemSet': 'CCI itemSet'
        # }
    data = {}
    data['itemSetFrom'] = omeka.get_itemset_id(rules['itemSetFrom']) if rules['itemSetFrom'] else None
    data['classFrom'] = omeka.get_resource_by_term(rules['classFrom'], resource_type='resource_classes')
    data['triggerProp'] = omeka.get_resource_by_term(rules['triggerProp'], resource_type='properties')
    data['targetProp'] = omeka.get_resource_by_term(rules['targetProp'], resource_type='properties')
    # data['targetItemClass'] = omeka.get_class_id(rules['targetItemClass'])
    data['targetItemClass'] = omeka.get_resource_by_term(rules['targetItemClass'], resource_type='resource_classes')
    data['targetTemplate'] = omeka.get_template_id(rules['targetTemplate']) if rules['targetTemplate'] else None
    data['targetItemSet'] = omeka.get_itemset_id(rules['targetItemSet'])
    data['linkProp'] =  omeka.get_resource_by_term(rules['linkProp'], resource_type='properties')
    data['targetLabel'] = rules['targetLabel']
    data['action'] = rules['action']
    data['team'] = rules['team']
    for searchedThing, userInput in rules.items():
        if not data[searchedThing] and userInput:
           print(f'ERROR, missing omeka resource, no {searchedThing} found')
           return None
    return data

def createEvents(omeka, items, dataRules):
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

    """
    processed = []
    not_proc = []
    error = []
    for startItem in items['results']:
        if dataRules['triggerProp']['o:term'] not in startItem:
            not_proc.append(startItem['o:id']) 
            continue
        found = searchMatch(omeka, startItem, dataRules)
        if found == "error":
            error.append(startItem['o:id'])
            continue
        elif found == "skip":
            not_proc.append(startItem['o:id']) 
            continue
        elif found == "NA":#no event found, create a new event item
            itemName = startItem['o:title'].split(' - ', 1)[0]
            eventLabel = dataRules['targetLabel'] + ' de ' + itemName
            print('CREATED:', eventLabel)
            terms = {
                'skos:prefLabel': [
                    {
                        'value': eventLabel
                    }
                ],
                dataRules['linkProp']['o:term'] : [
                    {
                        'value': startItem['o:id'],
                        'type': 'resource:item',
                    },
                ],
            }
            if dataRules['team']:
                terms['team'] = dataRules['team']
            if dataRules['targetTemplate']:
                new_item = omeka.prepare_item_payload_using_template(terms, dataRules['targetTemplate'])#a new item with template compliance check
            else:
                new_item = omeka.prepare_item_payload(terms)#a new item
        else: #edit existing event 
            print('FOUND item n°', found['o:id'])
            new_item = deepcopy(found)# edit existing item matching the criterias of serachMatch

        # just copies the content of trigger prop into the target prop
        new_itempropValues = new_item.setdefault(dataRules['triggerProp']['o:term'], [])
        new_itempropValues += [value for value in startItem[dataRules['triggerProp']['o:term']]]
        #then move the content to the targetprop if targetProp != triggerProp
        if dataRules['triggerProp']['o:term'] != dataRules['targetProp']['o:term']:
            new_item = moveDataProp.moveDataPropOfitem(omeka, 
                                                       new_item, 
                                                       dataRules['triggerProp']['o:term'], 
                                                       dataRules['targetProp']['o:term'], 
                                                       dataRules['targetProp']['o:id'], 
                                                       delFrom = True)
        #update or create depending on the case
        if found == "NA": omeka.add_item(new_item, template_id = dataRules['targetTemplate'], class_id = dataRules['targetItemClass']['o:id'], item_set_id = dataRules['targetItemSet'])
        else : omeka.update_resource(new_item, 'items')
        
        ##################################
        # actions on startIitem properties
        update_startItem = deepcopy(startItem)
        if dataRules['action'] == 'hide':
            update_startItem = utils.hideValues(update_startItem, dataRules['triggerProp']['o:term'])
        elif dataRules['action'] == 'delete':
            update_startItem = utils.removeValues(update_startItem, dataRules['triggerProp']['o:term'])
        omeka.update_resource(update_startItem, 'items')
        processed.append(startItem['o:id'])
    return processed, not_proc, error
                    

            
