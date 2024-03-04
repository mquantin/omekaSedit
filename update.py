#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omekastoolsFork import OmekaAPIClient
from collections import namedtuple

#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)


omeka = OmekaAPIClient(apiKey['APIurl'], 
                       key_identity=apiKey['identity'], 
                       key_credential=apiKey['credential']
                       )



def getItemsinPage(pageNum=1):
    # basic search
    # APIitems = omeka.search_items('', page=6)

    # # search items by class
    # APIitems = omeka.search_items(None, resource_class_id=omeka.get_property_id('crm:E21_Person'), )

    # # search items by property value
    # APIitems = omeka.filter_items_by_property(filter_property='crm:P5_consists_of', filter_value='', filter_type='in')

    # # search items by property exists
    # APIitems = omeka.filter_items_by_property(filter_property='crm:P2_has_type', filter_type='ex', item_set_id = itemSetId, page=pageNum)

    itemSets = omeka.get_resources('item_sets', search='CCI itemSet')
    if len(itemSets['results']) > 1 : 
        print('item set search query unclear, multiple results:')
        for itemSet in itemSets['results']:
            print(f"id: {itemSet['o:id']}, title: {itemSet['o:title']}")
        return
    if len(itemSets['results']) == 0 : 
        print('aucun item set trouvé')
        return
    itemSetId = itemSets['results'][0]['o:id']
    APIitems = omeka.search_items('', item_set_id = itemSetId, page=pageNum)
    if APIitems['results']:
        # a améliorer car la dernière page fausse la valeur de pageQ
        pagesQ = int(APIitems['total_results']/len(APIitems['results']))+1
        print(f"\n\nnombre d'item total: {APIitems['total_results']}, page: {pageNum}/{pagesQ}")
    else:
        print(f"pas d'autres items")
    return APIitems


def add_to_prop(item, propID, propTerm, newValue):
    """
     newValue is  {'value': uri or literal content, 'type': 'uri' ou 'literal', 'label': only for uri}
     propID and propTerm are input so they are queried outside the loop (calling this function). 
    """
    #creating the prop key if not exists
    propValues = item.setdefault(propTerm, [])#the key of the propTo is only usefull to get existing content, useless to create new one
    # managing existing values in target prop: avoid writing twice the same content. 
    # No  matter if this is an uri, resource or litteral. Only the content is checked
    # creates a list of all contents
    existingValuesContent = []
    existingValuesContent += [value['@id'] for value in propValues if '@id' in value]#all the uri / internal omeka resources
    existingValuesContent += [value['@value'].strip() for value in propValues if '@value' in value]#all the litterals
    # get the content of the value to be added
    new_valueContent = newValue['value'].strip()
    if new_valueContent in existingValuesContent:
        print('skiped ', new_valueContent, ' because it would have written twice the same content (duplicate)' )
        return item
    formatted_newProp = omeka.prepare_property_value(newValue, propID)
    propValues += [formatted_newProp,]
    return item



def moveDataProp(items, propFrom, propTo, delFrom = False):
    """
    propFrom and propTo are string like  'crm:P5_consists_of' and 'crm:P45_consists_of'
    """
    propTo_id = omeka.get_property_id(propTo)
    processed = []
    not_proc = []
    error = []
    for origItem in items['results']:
        if propFrom in origItem:
            print('processing item id n°',origItem['o:id'])
            new_item = deepcopy(origItem)
            #catches the content to be copied for each occurence in the propFrom of the item (maybe several values for the same prop)
            for origPropValue in new_item[propFrom]:
                origPropValueContent = None
                if origPropValue['type'] == 'uri':
                    origPropValueContent = origPropValue['@id']
                    newPropvalue = {'value': origPropValueContent, 'type': 'uri', 'label': origPropValue['o:label']}
                elif origPropValue['type'] == 'literal':
                    origPropValueContent = origPropValue['@value']
                    newPropvalue = {'value': origPropValueContent, 'type': 'literal'}
                else:
                    error.append(origItem['o:id']) 
                    raise ValueError("property value is unclear, nor uri, nor litteral", origPropValue)
                new_item = add_to_prop(new_item, propTo_id, propTo, newPropvalue)
            processed.append(origItem['o:id']) 
            if delFrom:
                del new_item[propFrom]
                print('deleteing values of ', propFrom )
            updated_item = omeka.update_resource(new_item, 'items')
            assert origItem['o:id'] == updated_item['o:id']
        else: 
            not_proc.append(origItem['o:id']) 
    return processed, not_proc, error


def checkProperty(items):
    NoDesc = 0
    OneDesc = 0
    MoreDesc = 0
    for item in items['results']:
        match len(item.get('dcterms:description', [])):
            case 0:
                NoDesc += 1
            case 1:
                OneDesc += 1
            case _:
                MoreDesc += 1
                #print(item['o:id'])
    print(f"  0 descirption: {NoDesc} items\n  1 description: {OneDesc} items\n >1 descriptions: {MoreDesc} items" )


def checkClasses(items):
    allclasses = {}
    for item in items['results']:
        itemClass = item.get('o:resource_class')
        if itemClass:
            itemClassID = itemClass['o:id']
        else:
            itemClassID = 'noClass'
        allclasses.setdefault(itemClassID,[]).append(item['o:id'])
    return allclasses

def updateThumbnail(items):
    for origItem in items['results']:
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

def updateClass(items, classFrom, classTo, templateTo, templateFrom = None, E55Type = False):
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
                    newPropValue = {'value': E55Type.uri, 'type': 'uri', 'label': E55Type.label}
                    new_item = add_to_prop(new_item, E55TypePropID, 'crm:P2_has_type', newPropValue)
                updated_item = omeka.update_resource(new_item, 'items')
                processed += [origItem['o:id']]
                assert origItem['o:id'] == updated_item['o:id']
                break # for testing : one loop for each page only. 
        else: 
            not_proc += [origItem['o:id']]
    return processed, not_proc, error


pageNum=0
search = True
processedItemsId = []
not_procItemsId = []
errorItemsId = []
allClasses = {}
E55type = namedtuple('E55type', 'uri label')
while search:
    pageNum+=1
    APIitems = getItemsinPage(pageNum)
    search = len(APIitems['results'])#0 quand il n'y a plus rien 
    if search:
        seenClasses = checkClasses(APIitems)
        for key, values in seenClasses.items():
            allClasses.setdefault(key, []).extend(values)
        #processed, not_proc, error = updateClass(APIitems, 'crm:E31_Document', 'crm:E22_Human-Made_Object', templateTo = 'mobilier', E55Type = E55type(uri="https://vocab.getty.edu/aat/300026685", label="Documents (AAT)"))
        processed, not_proc, error = moveDataProp(APIitems, "dcterms:type", propTo = 'crm:P2_has_type', delFrom = True)
        processedItemsId += processed
        not_procItemsId += not_proc
        errorItemsId += error



print("\n\n###################### Classes")
for classID, itemsID in allClasses.items():
    classTerm = omeka.get_resource_by_id(classID, resource_type='resource_classes')['o:term']
    print(f"class id: {classID}\nclass term: {classTerm}\nconcerned item count: {len(itemsID)}")
    print("id of concerned items :", itemsID)
    print("\n")

print("\n\n###################### Mutations")
print(f"processed: {len(processedItemsId)} \tskipped (error): {len(errorItemsId)} \tnot processed: {len(not_procItemsId)}")
print(f"processed items ids: {processedItemsId}")
if errorItemsId:
    print(f"error (skiped) items ids: {errorItemsId}")
#print(f"not processed items ids: {not_procItemsId}")