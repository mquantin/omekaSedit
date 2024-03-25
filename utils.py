#!python3
# -*- coding: utf-8 -*-

def getItemsinPage(omeka, pageNum=1, itemSetName=None):
    # basic search
    # APIitems = omeka.search_items('', page=6)

    # # search items by class
    # APIitems = omeka.search_items(None, resource_class_id=omeka.get_property_id('crm:E21_Person'), )

    # # search items by property value
    # APIitems = omeka.filter_items_by_property(filter_property='crm:P5_consists_of', filter_value='', filter_type='in')

    # # search items by property exists
    # APIitems = omeka.filter_items_by_property(filter_property='crm:P2_has_type', filter_type='ex', item_set_id = itemSetId, page=pageNum)

    itemSets = omeka.get_resources('item_sets', search=itemSetName)
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

def hideValue(itemValue):
    if 'is_public' in itemValue:
        itemValue['is_public'] == 'false'
    return itemValue

def hideValues(item, propTerm): 
    if propTerm not in item:
        return item
    for value in item[propTerm]:
        value = hideValue(value)
    return item

def removeValues(item, propTerm):
    if propTerm not in item:
        return item
    del(item[propTerm])        
    return item

def printMutation(mutationWord, processedItemsId, not_procItemsId, errorItemsId):
    print("\n\n###################### ", mutationWord)
    print(f"processed: {len(processedItemsId)} \tskipped (error): {len(errorItemsId)} \tnot processed: {len(not_procItemsId)}")
    print(f"processed items ids: {processedItemsId}")
    if errorItemsId:
        print(f"error (skiped) items ids: {errorItemsId}")
    #print(f"not processed items ids: {not_procItemsId}")
        
        

def printskip(new_valueContent, item):
    print(f"skiped {new_valueContent} in item {item['o:id']} because it would have written twice the same content (duplicate)")

def add_to_prop(omeka, item, propID, propTerm, newValues):
    """
     newValues is  a list of dict {'value': uri or literal content, 'type': 'uri' ou 'literal', 'label': only for uri}
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
    #format the contents and roughly checks if no duplicated 
    formatted_newValues = [omeka.prepare_property_value(newValue, propID)  if (newValue['value'] not in existingValuesContent) else printskip(item,newValue['value']) for newValue in newValues]
    propValues += formatted_newValues
    return item


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
