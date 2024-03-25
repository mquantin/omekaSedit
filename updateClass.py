#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils


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
    classF = omeka.get_resource_by_term(rules['classFrom'], resource_type='resource_classes')
    classT = omeka.get_resource_by_term(rules['classTo'], resource_type='resource_classes')
    templateT = omeka.get_template_by_label(rules['templateTo'])
    E55TypePropID = omeka.get_property_id('crm:P2_has_type')
    if rules['templateFrom']:
        templateF = omeka.get_template_by_label(rules['templateFrom'])
        print(f"      template from label: {rules['templateFrom']} \tid: {templateF['o:id']}")
    print(f"""  
        template to label: {rules['templateTo']} \tid: {templateT['o:id']}
        class from term: {classF['o:term']} \t\tid: {classF['o:id']}
        class to term: {classT['o:term']} \tid: {classT['o:id']}
        """)
    processed = []
    not_proc = []
    error = []
    for origItem in items['results']:
        origItemClass = origItem.get('o:resource_class')
        if not origItemClass:
            print("  ERROR this item has no class (skipped):", origItem['o:id'])
            error += [origItem['o:id']]
        elif origItemClass['o:id'] == classF['o:id']:
            template = origItem.get('o:resource_template')
            if not template:
                print("  ERROR this item has no template (skipped):", origItem['o:id'])
                error += [origItem['o:id']]
            elif rules['templateFrom'] and (template['o:id'] != templateF['o:id']):
                print(f"  ERROR this item uses a different template (skipped): {origItem['o:id']}; template id {template['o:id']}")
                error += [origItem['o:id']]
            else:
                #  print(f"processing item id n°{origItem['o:id']} classe: {rules['classFrom']} template: {template['o:id']}")
                new_item = deepcopy(origItem)
                new_item['o:resource_class'] = {
                    '@id': classT['@id'],
                    'o:id':classT['o:id']
                }
                new_item['o:resource_template'] = {
                    '@id': templateT['@id'],
                    'o:id':templateT['o:id']
                }
                if rules['E55TypeValue']:
                    newPropValues = [{'value': rules['E55TypeValue'].uri, 'type': 'uri', 'label': rules['E55TypeValue'].label},]
                    new_item = utils.add_to_prop(omeka, new_item, E55TypePropID, 'crm:P2_has_type', newPropValues)
                updated_item = omeka.update_resource(new_item, 'items')
                processed += [origItem['o:id']]
                assert origItem['o:id'] == updated_item['o:id']
                break # for testing : one loop for each page only. 
        else: 
            not_proc += [origItem['o:id']]
    return processed, not_proc, error
