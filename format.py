#!/usr/bin/python3.14

# ----------------------------------------------------------------------
#
# 2025-07-21: Migrate to jinja template

# 2024-01-22


# 2023-03-05:
#
# Check and format swade character
#
# ----------------------------------------------------------------------

import os
import sys
import argparse
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import jinja2
    
# --------------------
# Open and decode file
# --------------------

def yaml_file_read(path):

    with open(path, encoding='utf-8') as stream:
        data = load(stream, Loader=Loader)
    return data

# ----------------------------------------------------------------------
#
# advancement
#
# ----------------------------------------------------------------------

def apply_advancement(current, advancement):

    if not 'name' in advancement:
        print("%s: advancement must have 'name' key" % sys.argv[0])
        exit(1)
    
    if advancement['name'] == 'initial' and (not 'attributes' in advancement):
        print("%s: 'attributes' missing from 'swade'" % sys.argv[0])
        exit(1)

    # --------------------
    # Change list
    # --------------------

    change_list = []
    
    # --------------------
    # Hinderances
    # --------------------

    hinderances = current['hinderances'] if 'hinderances' in current else []
    if 'hinderances' in advancement:
        hinderances.extend(advancement['hinderances'])
        [ change_list.append("Hinderance: %s" % h['name']) for h in advancement['hinderances'] ]

    # --------------------
    # Attributes
    # --------------------

    attributes = current['attributes'] if 'attributes' in current else {}

    if 'attributes' in advancement:
        for attr in advancement['attributes']:
            if attr in attributes:
                attributes[attr] = {
                    'die': advancement['attributes'][attr],
                    'cost': 'Adv'
                }
            else:
                attributes[attr] = {
                    'die': advancement['attributes'][attr],
                    'cost': (advancement['attributes'][attr] - 4) // 2
                }
            change_list.append("Attribute: %s (%d)" % (attr, attributes[attr]['die']))

    # --------------------
    # Get skills
    # --------------------

    if advancement['name'] == 'initial' and (not 'skills' in advancement):
        print("%s: 'skills' missing from 'swade'" % sys.argv[0])
        exit(1)
        
    skills = current['skills'] if 'skills' in current else {}

    if 'skills' in advancement:
        for k,v in advancement['skills'].items():
            if not v['attribute'] in attributes:
                print("%s: stat %s incorrect" % (sys.argv[0], v['attribute']))
                exit(1)
            stat_die = attributes[v['attribute']]['die']

            die = v['die']
            initial = 2
            if 'initial' in v:
                initial = v['initial']
            if 'core' in v:
                initial = 4

            cost = 0
            for i in range(0, 6):
                d = 4 + i*2
                if d > die:
                    break
                if d <= initial:
                    continue
                if d <= stat_die:
                    cost += 1
                else:
                    cost = +2

            change_list.append("Skill: %s (%d)" % (k, die))
            print("%-20s die=%d initial=%d stat=%d cost=%d" % (k, die, initial, stat_die, cost))
            skills[k] = {
                'die': v['die'],
                'attribute': v['attribute'],
                'cost': cost,
                'initial': initial,
            }

    # --------------------
    # Edges
    # --------------------

    edges = current['edges'] if 'edges' in current else []
    if 'edges' in advancement:
        edges.extend(advancement['edges'])
        [ change_list.append("Edge: %s" % e) for e in advancement['edges'] ]

    if not 'changes' in current:
        current['changes'] = []

    if not advancement['name'] == 'Initial':
        current['changes'].append(
            {
                'name': advancement['name'],
                'changes': change_list,
            })
    
    # --------------------
    # Update current
    # --------------------

    current['attributes'] = attributes
    current['hinderances'] = hinderances
    current['edges'] = edges
    current['skills'] = skills
    current['advancement'] = advancement['name']

# ----------------------------------------------------------------------
#
# M A I N
#
# ----------------------------------------------------------------------

def format_swade(opts):
    character = yaml_file_read(opts['inpath'])
    if not 'swade' in character:
        print("%s: 'swade' missing from file %s" % (sys.argv[0], path))
        exit(1)
    swade = character['swade']

    if not 'advancement' in swade:
        print("%s: 'advancement' mising from file %s" % (sys.argv[0], path))
        exit(1)

    advancement = swade['advancement']
    if not isinstance(advancement, list):
        print("%s: [%s] 'advancement' not a list" % (sys.argv[0], path))
        
    current = {}
    for a in advancement:
        apply_advancement(current, a)

    # --------------------
    # Derived
    # --------------------
    
    derived = {
        'pace': 6
    }

    if 'fighting' in current['skills']:
        derived['parry'] = 2 + current['skills']['fighting']['die'] // 2
    else:
        derived['parry'] = 2

        derived['toughness'] = 2 + current['attributes']['vigor']['die'] // 2

    # --------------------
    # Items
    # --------------------
        
    weight = 0.0
    cost = 0.0
    index = 1
    gear_locations = {}
    for g in swade['gear']:
        number = 1
        if 'number' in g:
           number = g['number']
        t = {
            'name': g['name'],
            'number': number,
            'cost': g['cost'] * number
        }
        cost += t['cost']

        location = g['location'] if 'location' in g else 'Non Specific'
        if not location in gear_locations:
            gear_locations[location] = {
                'location': location,
                'weight': 0.0,
                'gear': []
            }

        if 'weight' in g:
            t['weight'] = g['weight'] * number
            weight += t['weight']
            gear_locations[location]['weight'] += t['weight']
            
        gear_locations[location]['gear'].append(t)

    gear_list = sorted(gear_locations.values(), key=lambda x: x['location'])

    index = 1
    for g in gear_list:
        g['index'] = index
        index += len(g['gear']) + 1
        
    gear = {
        'title': 'Gear (\\$%3.0f / %d lb)' % (cost, weight),
        'locations': gear_list,
        'indices': [ i['index'] for i in gear_list ]
        }

    # --------------------
    # table
    # --------------------

    char_table = {}
    char_table['name'] = character['name']
    if 'description' in character:
        char_table['description'] = character['description']

    if 'advancement' in current:
        char_table['advancement'] = current['advancement']

    if 'image' in character:
        char_table['image'] = character['image']

    char_table['hinderances'] = current['hinderances']
    char_table['attributes'] = current['attributes']
    char_table['derived'] = derived
    char_table['skills'] = current['skills']
    char_table['edges'] = current['edges']
    char_table['gear'] = gear
    char_table['changes'] = current['changes']
    row = 1
    for adv in current['changes']:
        adv['row'] = row
        row += len(adv['changes']) + 1

    
    # --------------------
    # Trailer
    # --------------------

    latex_jinja_env = jinja2.Environment(
        block_start_string = '\\BLOCK{',
        block_end_string = '}',
        variable_start_string = '\\VAR{',
        variable_end_string = '}',
        comment_start_string = '\\#{',
        comment_end_string = '}',
        line_statement_prefix = '%%',
        line_comment_prefix = '%#',
        trim_blocks = True,
        autoescape = False,
        loader = jinja2.FileSystemLoader(os.path.abspath('.'))
    )

    template_path = opts['template']
    if not (os.path.exists(template_path) and os.path.isfile(template_path)):
        print("Template %s either does not exist or is not a file" % template_path, file=sys.stderr)
        exit(1)

    template = latex_jinja_env.get_template(template_path)
    res = template.render(character = char_table)
    with open(opts['outpath'], 'w', encoding='utf-8') as stream:
        print(res, file=stream)

# ----------------------------------------------------------------------
#
# M A I N
#
# ----------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Format character JSON file to LuaLaTeX')
parser.add_argument("-t", "--template", action='store', type=str, required=True, help="Input file", dest="template")
parser.add_argument("-i", "--in", action='store', type=str, required=True, help="Input file", dest="inpath")
parser.add_argument("-o", "--out", action='store', type=str, required=True, help="Output file", dest="outpath")
args = parser.parse_args()

opts = {}

opts['template'] = args.template
opts['inpath'] = args.inpath
opts['outpath'] = args.outpath

format_swade(opts)
