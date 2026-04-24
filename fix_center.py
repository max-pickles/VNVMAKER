import json, os

path = os.path.join('game', 'vnv_projects', 'tqremake.json')
with open(path, 'r', encoding='utf-8') as f:
    proj = json.load(f)

fixes = 0
for scene in proj.get('scenes', []):
    for ev in scene.get('events', []):
        if ev.get('side') == 'left':
            ev['side'] = 'center'
            fixes += 1

with open(path, 'w', encoding='utf-8') as f:
    json.dump(proj, f, indent=2, ensure_ascii=False)

print(f"Updated {fixes} events to side='center'.")
