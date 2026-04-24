## ???????????????????????????????????????????????
##  VN Maker ? Emitter / Compiler
## ???????????????????????????????????????????????
## Takes the JSON/Dictionary state of the visual node graph and
## converts it directly into a runnable standard Ren'Py script!

init python:
    import json
    import os
    import re

    def _vn_compile_events(events, proj, lines, prefix="    ", is_preview=False):
        """Universal event-to-script generator used by exporting and live-preview."""
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
                        # Always scale bg to fill screen using Transform fit=cover
                        fill = f'Transform("{bg_path}", fit="cover", xsize=config.screen_width, ysize=config.screen_height)'
                        if ev.get('atl_code'):
                            lines.append(f"{prefix}scene expression {fill}:")
                            for atl_line in ev['atl_code'].split('\n'):
                                if atl_line.strip():
                                    lines.append(f"{prefix}    {atl_line}")
                        else:
                            lines.append(f"{prefix}scene expression {fill}")
                            
                elif t == 'image':
                    img_path = ev.get('image', '').replace('"', '\\"')
                    if img_path:
                        side = ev.get('side', 'left')
                        at_clause = f" at {side}" if side in ('left', 'center', 'right') else ""
                        if ev.get('atl_code'):
                            lines.append(f"{prefix}show expression \"{img_path}\" at {side}:")
                            for atl_line in ev['atl_code'].split('\n'):
                                if atl_line.strip():
                                    lines.append(f"{prefix}    {atl_line}")
                            if preview_zoom != 1.0:
                                lines.append(f"{prefix}    zoom {preview_zoom}")
                        else:
                            if preview_zoom != 1.0:
                                lines.append(f"{prefix}show expression \"{img_path}\"{at_clause}:")
                                lines.append(f"{prefix}    zoom {preview_zoom}")
                            else:
                                lines.append(f"{prefix}show expression \"{img_path}\"{at_clause}")
                            
                elif t == 'music':
                    music_path = ev.get('music', '').replace('"', '\\"')
                    if music_path:
                        lines.append(f"{prefix}play music \"{music_path}\"")
                        
                elif t == 'sfx':
                    sfx_path = ev.get('sfx', '').replace('"', '\\"')
                    if sfx_path:
                        lines.append(f"{prefix}play sound \"{sfx_path}\"")
                        
                elif t == 'dialogue':
                    char = vn_find_char(proj, ev.get('char_id'))
                    c_ref = f"vnc_{char['id']}" if (char and not is_preview) else "narrator"
                    if is_preview and char:
                        c_ref = f"Character('{char['display']}', color='{char['color']}')"
                        
                    if ev.get('char_id'):
                        sprite = vn_char_sprite(proj, ev.get('char_id'), ev.get('pose', 'neutral'))
                        if sprite:
                            align = {"left": "left", "center": "center", "right": "right"}.get(ev.get('side', 'center'), "center")
                            if preview_zoom != 1.0:
                                lines.append(f"{prefix}show expression \"{sprite}\" at {align}:")
                                lines.append(f"{prefix}    zoom {preview_zoom}")
                            else:
                                lines.append(f"{prefix}show expression \"{sprite}\" at {align}")
                            
                    txt = ev.get('text', '').replace('"', '\\"').replace('\n', '\\n')
                    lines.append(f"{prefix}{c_ref} \"{txt}\"")
                
                elif t == 'narration':
                    txt = ev.get('text', '').replace('"', '\\"').replace('\n', '\\n')
                    lines.append(f"{prefix}\"{txt}\"")
                
                elif t == 'choice' or t == 'menu':
                    opts = ev.get('opts', [])
                    prompt = ev.get('prompt', '').replace('"', '\\"').replace('\n', '\\n')
                    
                    if not opts:
                        if prompt:
                            lines.append(f"{prefix}\"{prompt}\"")
                        continue
                        
                    lines.append(f"{prefix}menu:")
                    if prompt:
                        lines.append(f"{prefix}    \"{prompt}\"")
                    for opt in opts:
                        opt_txt = opt.get('text', '').replace('"', '\\"').replace('\n', '\\n')
                        lines.append(f"{prefix}    \"{opt_txt}\":")
                        if opt.get('scene'):
                            target = opt['scene']
                            if is_preview:
                                lines.append(f"{prefix}        call vn_preview_{target}")
                            else:
                                lines.append(f"{prefix}        jump vns_scene_{target}")
                        else:
                            lines.append(f"{prefix}        pass")
                            
                elif t == 'jump':
                    target = ev.get('scene_id')
                    trans = ev.get('transition', 'dissolve')
                    if target:
                        if trans and trans != 'none':
                            lines.append(f"{prefix}with {trans}")
                        if is_preview:
                            lines.append(f"{prefix}call vn_preview_{target}")
                        else:
                            lines.append(f"{prefix}jump vns_scene_{target}")
                
                elif t == 'wait':
                    dur = ev.get('dur', 1.0)
                    lines.append(f"{prefix}pause {dur}")
                
                elif t == 'effect':
                    txt = ev.get('text', '').strip()
                    if txt:
                        txt = txt.replace('"', '\\"').replace('\n', '\\n')
                        lines.append(f"{prefix}\"{txt}\"")
                        
                    kind = ev.get('kind', 'fade')
                    if kind == 'dissolve':
                        lines.append(f"{prefix}with Dissolve(0.5)")
                    elif kind == 'fade':
                        lines.append(f"{prefix}with Fade(0.5, 0.0, 0.5)")
                    elif kind == 'flash':
                        lines.append(f"{prefix}with Fade(0.1, 0.0, 0.5, color='#fff')")
                    else:
                        lines.append(f"{prefix}with {kind}")
                
                elif t == 'setvar':
                    vname = ev.get('var_name', 'var')
                    vval = ev.get('var_val', 'True')
                    lines.append(f"{prefix}$ {vname} = {vval}")
                    
                elif t == 'if':
                    cond = ev.get('condition', 'True')
                    lines.append(f"{prefix}if {cond}:")
                    if ev.get('scene_true'):
                        target_true = ev['scene_true']
                        if is_preview:
                            lines.append(f"{prefix}    call vn_preview_{target_true}")
                        else:
                            lines.append(f"{prefix}    jump vns_scene_{target_true}")
                    else:
                        lines.append(f"{prefix}    pass")
                    
                    if ev.get('scene_false'):
                        lines.append(f"{prefix}else:")
                        target_false = ev['scene_false']
                        if is_preview:
                            lines.append(f"{prefix}    call vn_preview_{target_false}")
                        else:
                            lines.append(f"{prefix}    jump vns_scene_{target_false}")
                
                if t != 'wait':
                    dur = ev.get('duration', 0)
                    try:
                        dur = float(dur)
                        if dur > 0:
                            lines.append(f"{prefix}pause {dur}")
                    except:
                        pass

    def _vn_extract_vars(proj):
        """Scan project for all variables used in setvar/if nodes to auto-initialize them."""
        import re
        keywords = {'True', 'False', 'None', 'and', 'or', 'not', 'is', 'in'}
        vars_found = set()
        for sc in proj.get('scenes', []):
            for ev in sc.get('events', []):
                if ev.get('type') == 'setvar' and ev.get('var_name'):
                    vars_found.add(ev['var_name'].strip())
                elif ev.get('type') == 'if' and ev.get('condition'):
                    tokens = re.findall(r'\b([a-zA-Z_]\w*)\b', ev['condition'])
                    for t in tokens:
                        if t not in keywords:
                            vars_found.add(t)
        return sorted(list(vars_found))

    def vn_compile_project(proj, output_path=None, as_export=False):
        """Compiles the given project into a raw .rpy script file."""
        if not proj:
            return False, "No project"
            
        game_dir = renpy.config.gamedir
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', proj.get('title', 'compiled_project')).lower()
        if not output_path:
            output_path = os.path.join(game_dir, f"vns_build_{safe_name}.rpy")
            
        lines = [
            f"# ???????????????????????????????????????????????",
            f"# AUTO-GENERATED SCRIPT: {proj.get('title', 'Unknown Project')}",
            f"# AUTHOR: {proj.get('author', 'Unknown Author')}",
            f"# ???????????????????????????????????????????????",
            f"",
        ]
        
        if as_export:
            res = proj.get('resolution', [1920, 1080])
            res_w, res_h = int(res[0]), int(res[1])
            lines.extend([
                f"## ?? Resolution Configuration",
                f"init python:",
                f"    config.screen_width  = {res_w}",
                f"    config.screen_height = {res_h}",
                "",
            ])

        auto_vars = _vn_extract_vars(proj)
        if auto_vars:
            lines.append(f"## ?? Auto-Discovered Variables ?????????")
            for v in auto_vars:
                lines.append(f"default {v} = False")
            lines.append("")
        
        ## 1. Compile Characters
        lines.append(f"## ?? Characters ?????????")
        for char in proj.get('characters', []):
            cid = char['id']
            cname = char['display']
            ccolor = char.get('color', '#ffffff')
            lines.append(f"define vnc_{cid} = Character('{cname}', color='{ccolor}')")
            
        lines.append("")
            
        ## 2. Compile Scenes
        lines.append(f"## ?? Scenes ?????????????")
        for sc in proj.get('scenes', []):
            lbl = f"vns_scene_{sc['id']}"
            lines.append(f"label {lbl}:")
            
            if sc.get('bg'):
                lines.append(f"    scene expression Transform(\"{sc['bg']}\", fit=\"cover\", xsize=config.screen_width, ysize=config.screen_height)")
            if sc.get('music'):
                lines.append(f"    play music \"{sc['music']}\"")
                
            events = sc.get('events', [])
            if not events:
                lines.append("    pass")
            else:
                _vn_compile_events(events, proj, lines, prefix="    ", is_preview=False)
                
            lines.append("    return")
            lines.append("")
            
        ## 3. Entry point mapping
        start_sid = proj.get('start')
        start_sc = next((s for s in proj.get('scenes', []) if s['id'] == start_sid), None)
        if not start_sc and proj.get('scenes'):
            start_sc = proj['scenes'][0]

        if start_sc:
            lines.append(f"## Entry Point")
            if as_export:
                lines.append(f"label start:")
                lines.append(f"    jump vns_scene_{start_sc['id']}")
            else:
                proj_id = re.sub(r'[^a-zA-Z0-9_]', '_', proj.get('id', 'proj'))
                lines.append(f"label vns_{proj_id}_start:")
                lines.append(f"    jump vns_scene_{start_sc['id']}")
            lines.append("")
            
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            msg = f"Compiled successfully to {os.path.basename(output_path)}!"
            if not as_export and hasattr(store, 'vns'):
                store.vns.notify(msg, "ok")
            return True, msg
        except Exception as e:
            if not as_export and hasattr(store, 'vns'):
                store.vns.notify(f"Compile error: {e}", "err")
            return False, str(e)

    def vn_export(proj, out_dir):
        """Alias for exporting the standalone game script."""
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "script_vn.rpy")
        return vn_compile_project(proj, output_path=path, as_export=True)

    def _vn_export_standalone(proj, project_name):
        """Export the project as a completely standalone game folder in the SDK root."""
        import shutil
        import re
        
        if not proj or not project_name:
            return False, "Invalid project or name."
            
        safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', project_name).strip()
        if not safe_name:
            return False, "Invalid project name."
            
        sdk_root = os.path.dirname(renpy.config.basedir)
        out_dir = os.path.join(sdk_root, safe_name)
        
        if os.path.exists(out_dir):
            return False, f"Folder '{safe_name}' already exists in projects directory."
            
        template_dir = os.path.join(sdk_root, "gui")
        if not os.path.exists(template_dir):
            return False, "Could not find Ren'Py default template ('gui' folder) in SDK root."
            
        try:
            # 1. Copy template scaffold
            shutil.copytree(template_dir, out_dir)
            
            # Remove project.json so it is not hidden in the launcher
            pjson = os.path.join(out_dir, "project.json")
            if os.path.exists(pjson):
                os.remove(pjson)
                
            # Update options.rpy to use the real project title and safe folder name
            options_path = os.path.join(out_dir, "game", "options.rpy")
            if os.path.exists(options_path):
                proj_title = proj.get('title', safe_name)
                proj_author = proj.get('author', '')
                with open(options_path, "r", encoding="utf-8") as f:
                    opts = f.read()
                # config.name = display title shown in window and main menu
                opts = re.sub(r'define config\.name = _\(".*?"\)', f'define config.name = _("{proj_title}")', opts)
                # build.name must be ASCII-only for distributions
                opts = re.sub(r'define build\.name = ".*?"', f'define build.name = "{safe_name}"', opts)
                # save_directory must be ASCII-only
                opts = re.sub(r'define config\.save_directory = ".*?"', f'define config.save_directory = "{safe_name}"', opts)
                with open(options_path, "w", encoding="utf-8") as f:
                    f.write(opts)
            
            # 2. Compile script over the template's script.rpy
            script_path = os.path.join(out_dir, "game", "script.rpy")
            success, msg = vn_compile_project(proj, output_path=script_path, as_export=True)
            if not success:
                shutil.rmtree(out_dir, ignore_errors=True)
                return False, f"Script compilation failed: {msg}"
                
            # 3. Copy media assets (images and audio)
            src_game = renpy.config.gamedir
            dst_game = os.path.join(out_dir, "game")
            
            for folder in ["images", "audio"]:
                src_folder = os.path.join(src_game, folder)
                dst_folder = os.path.join(dst_game, folder)
                if os.path.exists(src_folder):
                    shutil.copytree(src_folder, dst_folder, dirs_exist_ok=True)
                    
            return True, f"Successfully exported standalone game:\n{safe_name}"
            
        except Exception as e:
            return False, f"Export failed: {e}"

    def _vns_build_full_preview(proj):
        """Build a script string containing vn_preview_<id> labels for EVERY scene.
        Returns the list of lines (without the entry-point trampoline)."""
        lines = []
        auto_vars = _vn_extract_vars(proj)
        for v in auto_vars:
            lines.append(f"default {v} = False")
        lines.append("")
        for s in proj.get('scenes', []):
            sid = s['id']
            lines.append(f"label vn_preview_{sid}:")
            lines.append(f"    show screen vn_play_overlay")
            if s.get('bg'):
                lines.append(f"    scene expression Transform(\"{s['bg']}\", fit=\"cover\", xsize=config.screen_width, ysize=config.screen_height)")
            if s.get('music'):
                lines.append(f"    play music \"{s['music']}\"")
            _vn_compile_events(s.get('events', []), proj, lines, prefix="    ", is_preview=True)
            lines.append("    hide screen vn_play_overlay")
            lines.append("    stop music fadeout 0.5")
            lines.append("    stop sound")
            lines.append("    stop voice")
            lines.append("    return")
            lines.append("")
        return lines

    def _vns_compile_scene(sc_id):
        """Compile ALL project scenes into live Ren'Py labels and execute the target scene."""
        if not vns.project: return
        sc = vn_find_scene(vns.project, sc_id)
        if not sc: return

        vns.preview_scene_id = sc_id
        import time as _t
        entry = f"vn_preview_entry_{sc_id}_{int(_t.time()*100) % 100000}"

        lines = _vns_build_full_preview(vns.project)
        ## Entry-point trampoline so we always re-execute even if label already loaded
        lines.append(f"label {entry}:")
        lines.append(f"    call vn_preview_{sc_id}")
        lines.append(f"    return")

        renpy.load_string("\n".join(lines))
        renpy.call_in_new_context(entry)

    def _vns_compile_scene_from(sc_id, start_idx):
        """Compile ALL project scenes and play the target scene starting from a specific event index."""
        if not vns.project: return
        sc = vn_find_scene(vns.project, sc_id)
        if not sc: return

        vns.preview_scene_id = sc_id
        import time as _t
        entry = f"vn_preview_entry_{sc_id}_from{start_idx}_{int(_t.time()*100) % 100000}"

        ## Build all sibling scenes normally so cross-scene calls resolve
        lines = _vns_build_full_preview(vns.project)

        ## Override the target scene with the sliced version
        lines.append(f"label {entry}:")
        lines.append(f"    show screen vn_play_overlay")
        
        last_bg = sc.get('bg')
        last_music = sc.get('music')
        events = sc.get('events', [])
        
        for ev_slot in events[:start_idx]:
            slot_events = []
            for k in ev_slot.keys():
                if k.startswith('layer') and isinstance(ev_slot[k], dict) and ev_slot[k].get('type'):
                    slot_events.append(ev_slot[k])
            if ev_slot.get('type'):
                slot_events.append(ev_slot)
                
            for sub_ev in slot_events:
                t = sub_ev.get('type')
                if t == 'bg' and sub_ev.get('bg'):
                    last_bg = sub_ev.get('bg')
                elif t == 'music' and sub_ev.get('music'):
                    last_music = sub_ev.get('music')
        
        if last_bg:
            bg_path = last_bg.replace('"', '\\"')
            lines.append(f"    scene expression Transform(\"{bg_path}\", fit=\"cover\", xsize=config.screen_width, ysize=config.screen_height)")
        if last_music:
            m_path = last_music.replace('"', '\\"')
            lines.append(f"    play music \"{m_path}\"")
            
        events_from_here = sc.get('events', [])[start_idx:]
        _vn_compile_events(events_from_here, vns.project, lines, prefix="    ", is_preview=True)
        lines.append("    hide screen vn_play_overlay")
        lines.append("    stop music fadeout 0.5")
        lines.append("    stop sound")
        lines.append("    stop voice")
        lines.append("    return")

        renpy.load_string("\n".join(lines))
        renpy.call_in_new_context(entry)
