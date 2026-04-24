import json

def _vn_compile_events(events, proj, lines, prefix='    ', is_preview=False):
    res = proj.get('resolution', [1920, 1080])
    preview_zoom = 1920.0 / float(res[0]) if is_preview else 1.0
    for ev_slot in events:
        layer_indices = []
        for k in ev_slot.keys():
            if k.startswith('layer'):
                try:
                    layer_indices.append(int(k[5:]))
                except ValueError:
                    pass
        layer_indices.sort(reverse=True)
        slot_events = []
        for idx in layer_indices:
            if ev_slot[f'layer{idx}'].get('type'):
                slot_events.append(ev_slot[f'layer{idx}'])
        if ev_slot.get('type'):
            slot_events.append(ev_slot)
            
        for ev in slot_events:
            t = ev.get('type')
            if t == 'bg':
                bg_path = ev.get('bg', '').replace('"', '\\"')
                if bg_path:
                    fill = f'Transform("{bg_path}", fit="cover", xsize=config.screen_width, ysize=config.screen_height)'
                    if ev.get('atl_code'):
                        lines.append(f'{prefix}scene expression {fill}:')
                        for atl_line in ev['atl_code'].split('\n'):
                            if atl_line.strip():
                                lines.append(f'{prefix}    {atl_line}')
                    else:
                        lines.append(f'{prefix}scene expression {fill}')
            elif t == 'image':
                img_path = ev.get('image', '').replace('"', '\\"')
                if img_path:
                    side = ev.get('side', 'left')
                    at_clause = f' at {side}' if side in ('left', 'center', 'right') else ''
                    if ev.get('atl_code'):
                        lines.append(f'{prefix}show expression "{img_path}" at {side}:')
                        for atl_line in ev['atl_code'].split('\n'):
                            if atl_line.strip():
                                lines.append(f'{prefix}    {atl_line}')
                        if preview_zoom != 1.0:
                            lines.append(f'{prefix}    zoom {preview_zoom}')
                    else:
                        if preview_zoom != 1.0:
                            lines.append(f'{prefix}show expression "{img_path}"{at_clause}:')
                            lines.append(f'{prefix}    zoom {preview_zoom}')
                        else:
                            lines.append(f'{prefix}show expression "{img_path}"{at_clause}')
            elif t == 'music':
                music_path = ev.get('music', '').replace('"', '\\"')
                if music_path:
                    lines.append(f'{prefix}play music "{music_path}"')
            elif t == 'sfx':
                sfx_path = ev.get('sfx', '').replace('"', '\\"')
                if sfx_path:
                    lines.append(f'{prefix}play sound "{sfx_path}"')
            elif t == 'dialogue':
                # Simplified char handling for testing
                lines.append(f'{prefix}"Dialogue..."')
            elif t == 'narration':
                txt = ev.get('text', '').replace('"', '\\"').replace('\n', '\\n')
                lines.append(f'{prefix}"{txt}"')
            elif t == 'choice' or t == 'menu':
                prompt = ev.get('prompt', '').replace('"', '\\"').replace('\n', '\\n')
                lines.append(f'{prefix}menu:')
                if prompt:
                    lines.append(f'{prefix}    "{prompt}"')
                for opt in ev.get('opts', []):
                    opt_txt = opt.get('text', '').replace('"', '\\"').replace('\n', '\\n')
                    lines.append(f'{prefix}    "{opt_txt}":')
                    if opt.get('scene'):
                        target = opt['scene']
                        if is_preview:
                            lines.append(f'{prefix}        call vn_preview_{target}')
                        else:
                            lines.append(f'{prefix}        jump vns_scene_{target}')
                    else:
                        lines.append(f'{prefix}        pass')
            elif t == 'jump':
                target = ev.get('scene_id')
                trans = ev.get('transition', 'dissolve')
                if target:
                    if trans and trans != 'none':
                        lines.append(f'{prefix}with {trans}')
                    if is_preview:
                        lines.append(f'{prefix}call vn_preview_{target}')
                    else:
                        lines.append(f'{prefix}jump vns_scene_{target}')

with open('c:/Users/maxcm/OneDrive/Desktop/MEME KING/renpy-8.5.2-sdk/VNVMaker/game/vnv_projects/tqremake.json', 'r') as f:
    proj = json.load(f)

lines = []
for s in proj.get('scenes', []):
    sid = s['id']
    lines.append(f'label vn_preview_{sid}:')
    lines.append(f'    show screen vn_play_overlay')
    if s.get('bg'):
        lines.append(f'    scene expression Transform("{s["bg"]}", fit="cover", xsize=config.screen_width, ysize=config.screen_height)')
    if s.get('music'):
        lines.append(f'    play music "{s["music"]}"')
    _vn_compile_events(s.get('events', []), proj, lines, prefix='    ', is_preview=True)
    lines.append('    hide screen vn_play_overlay')
    lines.append('    return')
    lines.append('')

print(chr(10).join(lines))
