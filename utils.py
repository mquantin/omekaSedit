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



def add_to_prop(omeka, item, propID, propTerm, newValue):
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
