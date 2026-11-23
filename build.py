# Builds the public copy of the grimoire app's player sheet page from the app's own assets:
#   python build.py     -> db.json, icons/, ccc.png next to this file (index.html is written by hand)
# The app's QR then only has to carry the script's character ids; see sheetWebUrl() in the app's Data.kt.
import json, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '..', 'apps', 'grimoire', 'src', 'main', 'assets')
read = lambda n: json.load(open(os.path.join(A, 'official', n), encoding='utf-8'))
TEAMS = {'townsfolk': 0, 'outsider': 1, 'minion': 2, 'demon': 3, 'traveller': 4, 'fabled': 5, 'loric': 5}
ko, icons = read('ko.json'), set(os.listdir(os.path.join(A, 'icons')))

def icon(i, team):   # same choice as Role.icon() in the app
    return next((f for f in (f'{i}{s}.webp' for s in ('_g' if team <= 1 else '_e', '', '_g', '_e')) if f in icons), '')

roles = {}
for o in read('roles.json'):
    if o.get('team') not in TEAMS: continue
    i, t, k = o['id'], TEAMS[o['team']], ko['roles'].get(o['id'])
    # [name, English name ('' when the name is already English), team, ability, icon file]
    roles[i] = [k['name'], o['name'], t, k['ability'], icon(i, t)] if k else [o['name'], '', t, o['ability'], icon(i, t)]
jinxes = [[o['id'], j['id'], ko['jinxes'].get(f"{o['id']}-{j['id']}", j['reason'])] for o in read('jinxes.json') for j in o['jinx']]
json.dump({'roles': roles, 'jinxes': jinxes}, open(os.path.join(HERE, 'db.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

shutil.rmtree(os.path.join(HERE, 'icons'), ignore_errors=True)
os.makedirs(os.path.join(HERE, 'icons'))
used = {r[4] for r in roles.values() if r[4]}
for f in used: shutil.copy(os.path.join(A, 'icons', f), os.path.join(HERE, 'icons', f))
shutil.copy(os.path.join(A, 'ccc.png'), os.path.join(HERE, 'ccc.png'))
assert len(roles) > 150 and all(len(r) == 5 for r in roles.values()) and len(used) > 150, (len(roles), len(used))
print(len(roles), 'roles', len(jinxes), 'jinxes', len(used), 'icons')
