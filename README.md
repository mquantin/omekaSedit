# omekaSedit
python scripts to edit omeka CMS data  
it uses omeka_s_tools


# scripts features
- move prop value from one prop to another
- update item class
- check existing classes
- update item thumbnail
- create new item "event items" based on a property in existing items. Example
  > "for all items containing a value in `dcterms:Date` property,
  >  create new items of class `crm:E65_Creation`
  >  and put value of `dcterms:Date` in a new prop `crm:P4_has_time-span`"

