# Builds the public copy of the grimoire app's player sheet page:
#   python build.py     -> db.json, icons/, ccc.png next to this file (index.html is written by hand)
# Official characters come from the app's assets; homebrew ones from the scripts in sheets/*.json (community format,
# as downloaded from botc.vnamu.com). A link then only has to carry character ids.
import glob, io, json, os, shutil, urllib.request
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
used = {r[4] for r in roles.values() if r[4]}
assert len(roles) > 150 and len(used) > 150, (len(roles), len(used))

# homebrew: their art is kept here as icons/hb/<id>.<ext>, fetched once, so the page does not depend on the image host
os.makedirs(os.path.join(HERE, 'icons', 'hb'), exist_ok=True)
sheets = {}
for path in sorted(glob.glob(os.path.join(HERE, 'sheets', '*.json'))):
    items = json.load(open(path, encoding='utf-8'))
    meta = next((x for x in items if isinstance(x, dict) and x.get('id') == '_meta'), {})
    ids = []
    for x in items:
        i = x if isinstance(x, str) else x.get('id')
        if i == '_meta': continue
        if isinstance(x, dict) and x.get('team') in TEAMS:
            assert i not in roles or roles[i][5:] == [path], f'homebrew id {i} clashes'
            img = (x.get('image') or [''])[0] if isinstance(x.get('image'), list) else x.get('image') or ''
            file = ''
            if img:
                file = f"hb/{i}{os.path.splitext(img.split('?')[0])[1] or '.png'}"
                dest = os.path.join(HERE, 'icons', file)
                if not os.path.exists(dest):
                    try:
                        data = urllib.request.urlopen(urllib.request.Request(img, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read()
                        assert data[:4] in (b'\x89PNG', b'RIFF') or data[:2] == b'\xff\xd8', 'not an image'
                        open(dest, 'wb').write(data)
                    except Exception as e:
                        print('no image for', i, e); file = ''
            roles[i] = [x['name'], '', TEAMS[x['team']], x.get('ability', ''), file]
        else:
            i = ''.join(c for c in i.lower() if c.isalnum())
            assert i in roles, f'{path}: unknown character {i}'
        if roles[i][2] < 4: ids.append(i)
    sheets[os.path.splitext(os.path.basename(path))[0]] = {'name': meta.get('name', ''), 'author': meta.get('author', ''), 'ids': ids}

json.dump({'roles': roles, 'jinxes': jinxes}, open(os.path.join(HERE, 'db.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for f in os.listdir(os.path.join(HERE, 'icons')):
    if f.endswith('.webp') and f not in used: os.remove(os.path.join(HERE, 'icons', f))
for f in used: shutil.copy(os.path.join(A, 'icons', f), os.path.join(HERE, 'icons', f))
shutil.copy(os.path.join(A, 'ccc.png'), os.path.join(HERE, 'ccc.png'))
# ready-made links for the bundled scripts
from urllib.parse import quote_plus
io.open(os.path.join(HERE, 'links.txt'), 'w', encoding='utf-8', newline='\n').write(''.join(
    f"{s['name']} ({s['author']})\nhttps://8eatles.github.io/botc-sheet/#n={quote_plus(s['name'])}&r={','.join(s['ids'])}\n\n" for s in sheets.values()))
print(len(roles), 'roles', len(jinxes), 'jinxes', len(used), 'official icons', {k: len(v['ids']) for k, v in sheets.items()})
