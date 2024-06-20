# omekaSedit
python scripts to edit omeka CMS data  
it uses a [fork of omeka_s_tools](https://github.com/mquantin/omeka_s_tools) (many updates for ease of use)


# scripts features
- move property value from one property to another. Remains in the same item. Example:
   > "move value of `dcterms:Date` property into `crm:P4_has_time-span` property"
- update item class
- check existing classes
- update item thumbnail
- create new item "event items" based on a property in existing items. Example
  > "for all items containing a value in `dcterms:Date` property,
  >  create new items of class `crm:E65_Creation`
  >  and put value of `dcterms:Date` in a new prop `crm:P4_has_time-span`"
  ![schema for create events behaviour](https://github.com/mquantin/omekaSedit/blob/main/createEvents.svg)
 
 Event creation is (minimally) compatible with [Teams module](https://github.com/UIUCLibrary/teams)