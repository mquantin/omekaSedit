#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils


def updateClass(omeka, items, classFrom, classTo, templateTo, templateFrom = None, E55Type = False):
    """
    change class and resource template
    classFrom and classTo are string like  crm:E36_Visual_Item
    templateTo and templateFom are label of template like 'mobilier'
    templateFrom is optional and restrict the provenance.
    E55Type is a named tuple (uri, label). It is optional. It add or create a crm:P2_has_type to keep memory of the class that war intially assigned.
    """
    classF = omeka.get_resource_by_term(classFrom, resource_type='resource_classes')
    classT = omeka.get_resource_by_term(classTo, resource_type='resource_classes')
    templateT = omeka.get_template_by_label(templateTo)
    E55TypePropID = omeka.get_property_id('crm:P2_has_type')
    if templateFrom:
        templateF = omeka.get_template_by_label(templateFrom)
        print(f"      template from label: {templateFrom} \tid: {templateF['o:id']}")
    print(f"""  
        template to label: {templateTo} \tid: {templateT['o:id']}
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
            elif templateFrom and (template['o:id'] != templateF['o:id']):
                print(f"  ERROR this item uses a different template (skipped): {origItem['o:id']}; template id {template['o:id']}")
                error += [origItem['o:id']]
            else:
                #  print(f"processing item id n°{origItem['o:id']} classe: {classFrom} template: {template['o:id']}")
                new_item = deepcopy(origItem)
                new_item['o:resource_class'] = {
                    '@id': classT['@id'],
                    'o:id':classT['o:id']
                }
                new_item['o:resource_template'] = {
                    '@id': templateT['@id'],
                    'o:id':templateT['o:id']
                }
                if E55Type:
                    newPropValues = [{'value': E55Type.uri, 'type': 'uri', 'label': E55Type.label},]
                    new_item = utils.add_to_prop(omeka, new_item, E55TypePropID, 'crm:P2_has_type', newPropValues)
                updated_item = omeka.update_resource(new_item, 'items')
                processed += [origItem['o:id']]
                assert origItem['o:id'] == updated_item['o:id']
                break # for testing : one loop for each page only. 
        else: 
            not_proc += [origItem['o:id']]
    return processed, not_proc, error
