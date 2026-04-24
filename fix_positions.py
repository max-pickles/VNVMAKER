import json, os

path = os.path.join('game', 'vnv_projects', 'tqremake.json')
with open(path, 'r', encoding='utf-8') as f:
    proj = json.load(f)

sylvie_id = 'chSylv1'
fixes = 0

for scene in proj.get('scenes', []):
    for ev in scene.get('events', []):
        # Standalone image events: set side=left (these are all Sylvie sprites)
        if ev.get('type') == 'image':
            if 'sylvie' in ev.get('image', '').lower():
                ev['side'] = 'left'
                fixes += 1
        # Dialogue events for Sylvie: ensure side=left
        if ev.get('type') == 'dialogue' and ev.get('char_id') == sylvie_id:
            ev['side'] = 'left'
            fixes += 1

with open(path, 'w', encoding='utf-8') as f:
    json.dump(proj, f, indent=2, ensure_ascii=False)

print(f"Updated {fixes} events with side='left'.")
