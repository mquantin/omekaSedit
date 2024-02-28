#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
import yaml
from omeka_s_tools.api import OmekaAPIClient


#read credential API as a yaml file
with open("APIkey.key", 'r') as stream:
    apiKey = yaml.safe_load(stream)


omeka = OmekaAPIClient('https://epotec.univ-nantes.fr/api', 
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
    # APIitems = omeka.filter_items_by_property(filter_property='crm:P5_consists_of', filter_type='ex')

    APIitems = omeka.search_items('', item_set_id = '210', page=pageNum)
    if APIitems['results']:
        # a améliorer car la dernière page fausse la valeur de pageQ
        pagesQ = int(APIitems['total_results']/len(APIitems['results']))+1
        print(f"nombre d'item total: {APIitems['total_results']}, page: {pageNum}/{pagesQ}")
    else:
        print(f"pas d'autres items")
    return APIitems



moveDataFromProp = 'crm:P5_consists_of'
moveDataToProp = 'crm:P45_consists_of'

def moveDataProp(items, fromProp, toProp, delFrom = False):
    print(len(items['results']))
    for origItem in items['results']:
        #print what we're talking about
        if fromProp in origItem:
            print('processing item n°',origItem['o:id'])
            new_item = deepcopy(origItem)
            # managing existing values in target prop
            toPropValues = new_item.setdefault(toProp, [])#the key of the toProp is totally abitrary, useless
            existingIds = []
            existingIds += [value['@id'] for value in toPropValues if '@id' in value]
            existingIds += [value['@value'] for value in toPropValues if '@value' in value]
            toProp_id = omeka.get_property_id(toProp)
            processedValuesCount = 0
            for origPropValue in new_item[fromProp]:
                if origPropValue['type'] == 'uri':
                    processedValuesCount += 1
                    checking = '@id'
                    newPropvalue = {'value': origPropValue['@id'], 'type': 'uri', 'label': origPropValue['o:label']}
                elif origPropValue['type'] == 'literal':
                    processedValuesCount += 1
                    checking = '@value'
                    newPropvalue = {'value': origPropValue['@value'], 'type': 'literal'}
                else:
                    raise ValueError("property value is unclear", origPropValue)
                if origPropValue[checking] in existingIds:
                    print('skiped ', origPropValue[checking], ' to avoid duplicate' )
                    continue
                formatted_newProp = omeka.prepare_property_value(newPropvalue, toProp_id)
                toPropValues += [formatted_newProp,]
            print('processed ', processedValuesCount, ' values')
            if delFrom:
                del new_item[fromProp]
                print('deleteing values of ', fromProp )
            updated_item = omeka.update_resource(new_item, 'items')
            assert origItem['o:id'] == updated_item['o:id']

def check(items):
    for item in items['results']:
        if len(item.get('dcterms:description', []))>1:
            print(item['o:id'])

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

def changeClass(items, classFrom, classTo):
    """
    classFrom and classTo are string like  crm:E36_Visual_Item
    """
    classF = omeka.get_resource_by_term(classFrom, resource_type='resource_classes')
    classT = omeka.get_resource_by_term(classTo, resource_type='resource_classes')
    print(f"  class from term: {classF['o:term']} \t\tid: {classF['o:id']} \n  class to term: {classT['o:term']} \tid: {classT['o:id']}")
    for origItem in items['results']:
        origItemClass = origItem.get('o:resource_class')
        if not origItemClass:
            print("  this item has no class:", origItem['o:id'])
        elif origItemClass['o:id'] == classF['o:id']:
            print("  this item class should be updated", origItem['o:id'])

pageNum=0
search = True
while search:
    pageNum+=1
    APIitems = getItemsinPage(pageNum)
    search = len(APIitems['results'])#0 quand il n'y a plus rien 
    if search:
        changeClass(APIitems, 'crm:E31_Document', 'crm:E22_Human-Made_Object')

# a voir comment éviter de re-query l'api pour retrouver les class ou les propriétés à chaque page
# positionner le fetch au bon endroit.