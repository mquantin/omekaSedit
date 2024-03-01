#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omeka_s_tools.api import OmekaAPIClient


#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)


omeka = OmekaAPIClient(apiKey['url'], 
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



def moveDataProp(items, propFrom, propTo, delFrom = False):
    """
    propFrom and propTo are string like  'crm:P5_consists_of' and 'crm:P45_consists_of'
    """
    print(len(items['results']))
    for origItem in items['results']:
        #print what we're talking about
        if propFrom in origItem:
            print('processing item id n°',origItem['o:id'])
            new_item = deepcopy(origItem)
            # managing existing values in target prop
            propToValues = new_item.setdefault(propTo, [])#the key of the propTo is totally abitrary, useless
            existingIds = []
            existingIds += [value['@id'] for value in propToValues if '@id' in value]
            existingIds += [value['@value'] for value in propToValues if '@value' in value]
            propTo_id = omeka.get_property_id(propTo)
            processedValuesCount = 0
            for origPropValue in new_item[propFrom]:
                if origPropValue['type'] == 'uri':
                    processedValuesCount += 1
                    checking = '@id'
                    newPropvalue = {'value': origPropValue['@id'], 'type': 'uri', 'label': origPropValue['o:label']}
                elif origPropValue['type'] == 'literal':
                    processedValuesCount += 1
                    checking = '@value'
                    newPropvalue = {'value': origPropValue['@value'], 'type': 'literal'}
                else:
                    raise ValueError("property value is unclear, nor uri, nor litteral", origPropValue)
                if origPropValue[checking] in existingIds:
                    print('skiped ', origPropValue[checking], ' to avoid duplicate' )
                    continue
                formatted_newProp = omeka.prepare_property_value(newPropvalue, propTo_id)
                propToValues += [formatted_newProp,]
            print('processed ', processedValuesCount, ' values')
            if delFrom:
                del new_item[propFrom]
                print('deleteing values of ', propFrom )
            updated_item = omeka.update_resource(new_item, 'items')
            assert origItem['o:id'] == updated_item['o:id']

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
        #print what we're talking about
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

def updateClass(items, classFrom, classTo, templateTo, templateFrom = None, addType = False):
    """
    change class and resource template
    classFrom and classTo are string like  crm:E36_Visual_Item
    templateTo and templateFom are label of template like 'mobilier'
    templateFrom is optional and restrict the provenance.
    addType is optional. It add or create a crm:P2_has_type to keep memory of the class that war intially assigned.
    """
    classF = omeka.get_resource_by_term(classFrom, resource_type='resource_classes')
    classT = omeka.get_resource_by_term(classTo, resource_type='resource_classes')
    templateT = omeka.get_template_by_label(templateTo)
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
            elif templateFrom and template['o:id'] != templateF['o:id']:
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
                newTypeProp = {'value': uriValue, 'type': 'uri', 'label': uriValue}
                formatted_newTypeProp = omeka.prepare_property_value(newTypeProp, propTo_id)

                #updated_item = omeka.update_resource(new_item, 'items')
                processed += [origItem['o:id']]
                #assert origItem['o:id'] == updated_item['o:id']
                # break
        else: 
            not_proc += [origItem['o:id']]
    return processed, not_proc, error


pageNum=0
search = True
processedItemsId = []
not_procItemsId = []
errorItemsId = []
allClasses = {}
while search:
    pageNum+=1
    APIitems = getItemsinPage(pageNum)
    search = len(APIitems['results'])#0 quand il n'y a plus rien 
    if search:
        seenClasses = checkClasses(APIitems)
        for key, values in seenClasses.items():
            allClasses.setdefault(key, []).extend(values)
        processed, not_proc, error = updateClass(APIitems, 'crm:E36_Visual_Item', 'crm:E22_Human-Made_Object', 'mobilier')
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