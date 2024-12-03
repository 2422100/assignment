import flet as ft
import json

json_file_path = "/Users/marina/Lecture/DS-Programming2/jma/area.json"

with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

centers = data.get('centers', {})

name_list = []
enName_list = []
officeName_list = []
children_list = []

for center_id, center_info in centers.items():
    name = center_info.get('name')
    enName = center_info.get('enName')
    officeName = center_info.get('officeName')
    children = center_info.get('children', [])

    name_list.append(name)
    enName_list.append(enName)
    officeName_list.append(officeName)
    children_list.append(children)

offices = data.get('offices', {})

offices_list = []
o_name_list = []
o_enName_list = []
o_officeName_list = []
o_parent_list = []
o_children_list = []

for office_id, office_info in offices.items():
    offices = office_info.get('offices_id')
    o_name = office_info.get('name')
    o_enName = office_info.get('enName')
    o_officeName = office_info.get('officeName')
    o_parent = office_info.get('parent')
    o_children = office_info.get('children', [])

    offices_list.append(offices)
    o_name_list.append(o_name)
    o_enName_list.append(o_enName)
    o_officeName_list.append(o_officeName)
    o_parent_list.append(o_parent)
    o_children_list.append(o_children)

class10s = data.get('class10s', {})

c_name_list = []
c_enName_list = []
c_parent_list = []
c_children_list = []

for class10_id, class10_info in class10s.items():
    c_name = class10_info.get('name')
    c_enName = class10_info.get('enName')
    c_parent = class10_info.get('parent')
    c_children = class10_info.get('children', [])

    c_name_list.append(c_name)
    c_enName_list.append(c_enName)
    c_parent_list.append(c_parent)
    c_children_list.append(c_children)

class15s = data.get('class15s', {})

c2_name_list = []
c2_enName_list = []
c2_parent_list = []
c2_children_list = []

for class15_id, class15_info in class15s.items():
    c2_name = class15_info.get('name')
    c2_enName = class15_info.get('enName')
    c2_parent = class15_info.get('parent')
    c2_children = class15_info.get('children', [])

    c2_name_list.append(c2_name)
    c2_enName_list.append(c2_enName)
    c2_parent_list.append(c2_parent)
    c2_children_list.append(c2_children)

class20s = data.get('class20s', {})

c3_name_list = []
c3_enName_list = []
c3_kana_list = []
c3_parent_list = []

for class20_id, class20_info in class20s.items():
    c3_name = class20_info.get('name')
    c3_enName = class20_info.get('enName')
    c3_kana = class20_info.get('kana')
    c3_parent = class20_info.get('parent')

    c3_name_list.append(c3_name)
    c3_enName_list.append(c3_enName)
    c3_kana_list.append(c3_kana)
    c3_parent_list.append(c3_parent)

print(children_list)

