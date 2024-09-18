import json

full_string = ''
with open('J_Medline.txt', 'r') as in_file:
    for line in in_file:
        full_string += line

journals_info = full_string.split('--------------------------------------------------------')
journals_info = [j.split('\n')[1:8] for j in journals_info]
journals_meta = {}
for entry in journals_info[1:]:
    d = {}
    for item in entry:
        fields = item.split(':')
        key=fields[0]
        value=fields[1].lstrip()
        if key=='MedAbbr':
            journal_title = value
        else:
            d[key] = value
    journals_meta[journal_title]=d


with open('journals_ids.json', 'w') as outjson:
    json.dump(journals_meta, outjson)
