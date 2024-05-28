#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils

def prepareRules(omeka, rules):
    data = {}
    data['classFrom'] = omeka.get_resource_by_term(rules['classFrom'], resource_type='resource_classes')
    data['classTo'] = omeka.get_resource_by_term(rules['classTo'], resource_type='resource_classes')
    data['templateTo'] = omeka.get_template_by_label(rules['templateTo'])
    data['itemSetFrom'] = omeka.get_itemset_id(rules['itemSetFrom']) if rules['itemSetFrom'] else None
    data['templateFrom'] = omeka.get_template_by_label(rules['templateFrom']) if rules['templateFrom'] else None
    data['E55TypeProp'] = omeka.get_property_id('crm:P2_has_type')
    data['E55TypeValue'] = rules['E55TypeValue']
    for searchedThing, userInput in rules.items():
        if not data[searchedThing] and userInput:
           print(f'ERROR, missing omeka resource, no {searchedThing} found')
           return None
    return data


def updateClass(omeka, items, rules):
    """
    change class and resource template
    rules is a dict like: 
    {
        'classFrom': 'crm:E31_Document',
        'classTo': 'crm:E22_Human-Made_Object', 
        'templateTo': 'mobilier',
        'templateFrom': False,#optional, value may be False
        'E55TypeValue': E55type(uri="https://vocab.getty.edu/aat/300026685", label="Documents (AAT)"),#optional, value may be False
    }
    templateFrom is optional and restrict the provenance.
    E55TypeValue is a named tuple (uri, label). It is optional. It add or create a crm:P2_has_type to keep memory of the class that war intially assigned.
    """
    processed = []
    not_proc = []#allways empty since the class filter is don upstream
    error = []
    for origItem in items['results']:
        template = origItem.get('o:resource_template')
        if not template:
            print("  ERROR this item has no template (skipped):", origItem['o:id'])
            error += [origItem['o:id']]
        elif rules['templateFrom'] and (template['o:id'] != rules['templateFrom']['o:id']):
            print(f"  ERROR this item uses a different template (skipped): {origItem['o:id']}; template id {template['o:id']}")
            error += [origItem['o:id']]
        else:
            print(f"processing item id n°{origItem['o:id']} classe: {origItem['o:resource_class']['o:id']} template: {template['o:id']}")
            new_item = deepcopy(origItem)
            new_item['o:resource_class'] = {
                '@id': rules['classTo']['@id'],
                'o:id':rules['classTo']['o:id']
            }
            new_item['o:resource_template'] = {
                '@id': rules['templateTo']['@id'],
                'o:id':rules['templateTo']['o:id']
            }
            if rules['E55TypeValue']:
                newPropValues = [{'value': rules['E55TypeValue'].uri, 'type': 'uri', 'label': rules['E55TypeValue'].label},]
                new_item = utils.add_to_prop(omeka, new_item, rules['E55TypeProp'], 'crm:P2_has_type', newPropValues)
            updated_item = omeka.update_resource(new_item, 'items')
            processed += [origItem['o:id']]
            assert origItem['o:id'] == updated_item['o:id']
    return processed, not_proc, error
