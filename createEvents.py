#!python3
# -*- coding: utf-8 -*-

from copy import deepcopy
###local imports
import utils




def createEvents(omeka, items, mapping):
  """
  For each startItem with 
  triggerProp
  if startItem is already linked with linkProperty from a targetItem of targetItemClass:
    if targetItem has no property targetProp:
      move the value content of triggerProp to targetProp in the existing targetItem
    else:
      warn
  else if startItem is already linked with any other property from a targetItem of targetItemClass:
    warn
  else if
    create a new targetItem with targetItemClass as class
    move the value content of triggerProp to targetProp in that targetItem
    create a linkProperty in that targetItem, pointing to our startItem

  Mapping example
    {
      'triggerProp': 'dcterms:date',
      'targetProp': 'crm:P4_has_time-span', 
      'targetItemClass': 'crm:E65_Creation',
      'linkProperty': 'crms:p1_has_conceived',
      }
  """

