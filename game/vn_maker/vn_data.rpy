## ???????????????????????????????????????????????
##  VN Maker ? Data Model + Persistence   init -5
## ???????????????????????????????????????????????

## Declare persistent storage so Ren'Py initializes it as {} not None
default persistent.vn_projects = {}

init -5 python:
    import json, os, uuid, time, shutil

    # ?? Constructors ??????????????????????????????

    def vn_new_project(title="My Visual Novel", author="Author", resolution=(1920, 1080)):
        p = {
            'id':         str(uuid.uuid4())[:8],
            'title':      title,
            'author':     author,
            'created':    time.time(),
            'updated':    time.time(),
            'cover':      None,
            'resolution': list(resolution),  # [W, H]
            'characters': [],
            'scenes':     [],
            'start':      None,
            'text_tpls':  [_vn_default_text_tpl()],
            'trans_tpls': [_vn_default_trans_tpl()],
        }
        return p

    def vn_new_character(name="New Character"):
        return {
            'id':   str(uuid.uuid4())[:8],
            'name': name,
            'display': name,
            'color': "#c8d0ff",
            'sprites': {
                'neutral':'', 'happy':'', 'sad':'',
                'angry':'', 'surprised':'', 'custom1':'', 'custom2':'',
            }
        }

    def vn_new_scene(label="Scene"):
        return {
            'id':     str(uuid.uuid4())[:8],
            'label':  label,
            'bg':     None,
            'music':  None,
            'events': [],
        }

    def vn_new_dialogue(char_id=None, text="", pose="neutral", side="center"):
        return {
            'id':      str(uuid.uuid4())[:8],
            'type':    'dialogue',
            'char_id': char_id,
            'pose':    pose,
            'text':    text,
            'side':    side,
            'tpl_id':  None,
        }

    def vn_new_menu(prompt=""):
        return {
            'id':     str(uuid.uuid4())[:8],
            'type':   'menu',
            'prompt': prompt,
            'opts': [
                {'id': str(uuid.uuid4())[:6], 'text': 'Option 1', 'scene': None},
                {'id': str(uuid.uuid4())[:6], 'text': 'Option 2', 'scene': None},
            ],
        }

    def vn_new_choice(prompt=""):
        return {
            'id':     str(uuid.uuid4())[:8],
            'type':   'choice',
            'prompt': prompt,
            'opts': [
                {'id': str(uuid.uuid4())[:6], 'text': 'Option 1', 'scene': None},
                {'id': str(uuid.uuid4())[:6], 'text': 'Option 2', 'scene': None},
            ],
        }

    def vn_new_effect(kind="dissolve"):
        return {
            'id':   str(uuid.uuid4())[:8],
            'type': 'effect',
            'kind': kind,
            'dur':  0.5,
        }

    def vn_new_jump(scene_id=None, transition="dissolve"):
        return {
            'id':         str(uuid.uuid4())[:8],
            'type':       'jump',
            'scene_id':   scene_id,
            'transition': transition,
        }

    def vn_new_wait(dur=1.0):
        return {'id': str(uuid.uuid4())[:8], 'type': 'wait', 'dur': dur}

    def vn_new_empty_slot():
        """A blank click slot with no event type — shown as an empty cell in the timeline."""
        return {'id': str(uuid.uuid4())[:8], 'type': ''}

    def vn_new_music(filename=""):
        return {'id': str(uuid.uuid4())[:8], 'type': 'music', 'music': filename}
        
    def vn_new_bg(filename=""):
        return {'id': str(uuid.uuid4())[:8], 'type': 'bg', 'bg': filename}
        
    def vn_new_image(filename=""):
        return {'id': str(uuid.uuid4())[:8], 'type': 'image', 'image': filename}
        
    def vn_new_sfx(filename=""):
        return {'id': str(uuid.uuid4())[:8], 'type': 'sfx', 'sfx': filename}


    def vn_new_narration(text=""):
        return {
            'id':     str(uuid.uuid4())[:8],
            'type':   'narration',
            'text':   text,
            'tpl_id': None,
        }

    def _vn_default_text_tpl():
        return {
            'id': 'default', 'name': 'Default',
            'font': 'DejaVuSans.ttf', 'size': 22,
            'color': '#ffffff', 'bold': False, 'italic': False,
            'outline': True, 'outline_color': '#000000', 'outline_size': 2,
            'shadow': False, 'shadow_color': '#000000aa',
            'box_bg': '#00000099', 'box_pad': 20, 'typing_speed': 0,
        }

    def _vn_default_trans_tpl():
        return {
            'id': 'default', 'name': 'Dissolve',
            'type': 'dissolve', 'dur': 0.5, 'color': '#000000',
        }

    def vn_new_text_tpl(name="Text Style"):
        t = _vn_default_text_tpl()
        t['id'] = str(uuid.uuid4())[:8]
        t['name'] = name
        return t

    def vn_new_trans_tpl(name="Transition"):
        t = _vn_default_trans_tpl()
        t['id'] = str(uuid.uuid4())[:8]
        t['name'] = name
        return t

    # ?? Persistence ???????????????????????????????

    def _vn_proj_dir():
        d = os.path.join(vn_game_dir(), "vnv_projects")
        os.makedirs(d, exist_ok=True)
        return d

    def _vn_migrate_persistent():
        """Move any existing projects out of Ren'Py persistent memory into JSON files."""
        db = getattr(persistent, 'vn_projects', None)
        if isinstance(db, dict) and db:
            d = _vn_proj_dir()
            for pid, proj in db.items():
                path = os.path.join(d, f"{pid}.json")
                if not os.path.exists(path):
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(proj, f, indent=2)
            persistent.vn_projects = {}
            renpy.save_persistent()

    def _vn_migrate_project(proj, fname):
        """Ensure a loaded project has all required fields (patch legacy formats)."""
        changed = False
        # Derive id from filename if missing
        if not proj.get('id'):
            proj['id'] = os.path.splitext(fname)[0]
            changed = True
        # Ensure standard top-level keys
        for key, default in [
            ('layout',     {}),
            ('folders',    []),
            ('characters', []),
            ('scenes',     []),
            ('updated',    0),
        ]:
            if key not in proj:
                proj[key] = default
                changed = True
        return changed

    def vn_save(proj):
        if not proj:
            return
        # If id is still missing, can't save safely
        if not proj.get('id'):
            return
        _vn_migrate_persistent()
        proj['updated'] = time.time()
        path = os.path.join(_vn_proj_dir(), f"{proj['id']}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(proj, f, indent=2)

    def vn_all():
        _vn_migrate_persistent()
        projects = []
        d = _vn_proj_dir()
        for fname in os.listdir(d):
            if fname.endswith(".json"):
                path = os.path.join(d, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        p = json.load(f)
                    ## Font migration
                    for t in p.get('text_tpls', []):
                        if t.get('font') in ("DejaVuSans-Oblique.ttf", "DejaVuSans-Bold.ttf"):
                            t['font'] = "DejaVuSans.ttf"
                    ## Field migration (patches id etc.)
                    if _vn_migrate_project(p, fname):
                        vn_save(p)  # persist the fixed fields immediately
                    projects.append(p)
                except: pass
        return sorted(projects, key=lambda p: -p.get('updated', 0))

    def vn_load(pid):
        path = os.path.join(_vn_proj_dir(), f"{pid}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    p = json.load(f)
                for t in p.get('text_tpls', []):
                    if t.get('font') in ("DejaVuSans-Oblique.ttf", "DejaVuSans-Bold.ttf"):
                        t['font'] = "DejaVuSans.ttf"
                fname = os.path.basename(path)
                if _vn_migrate_project(p, fname):
                    vn_save(p)  # persist any newly added fields
                return p
            except: pass
        return None

    def vn_delete(pid):
        path = os.path.join(_vn_proj_dir(), f"{pid}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
            except: pass

    # ?? File system helpers ???????????????????????

    def vn_game_dir():
        return renpy.config.gamedir

    def vn_ls(rel):
        full = os.path.join(vn_game_dir(), rel)
        if not os.path.isdir(full):
            return [], []
        items = os.listdir(full)
        return (sorted(i for i in items if os.path.isdir(os.path.join(full, i))),
                sorted(i for i in items if os.path.isfile(os.path.join(full, i))))

    def vn_mkdir(rel):
        full = os.path.join(vn_game_dir(), rel)
        try:
            os.makedirs(full, exist_ok=True)
            return True, "Folder created: " + rel
        except Exception as e:
            return False, str(e)

    def vn_scan_images(root="images"):
        base = vn_game_dir()
        full = os.path.join(base, root)
        exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
        out = []
        try:
            for r, _, fs in os.walk(full):
                for f in fs:
                    if os.path.splitext(f.lower())[1] in exts:
                        rel = os.path.relpath(os.path.join(r, f), base)
                        out.append(rel.replace('\\', '/'))
        except:
            pass
        return out

    def vn_scan_audio(root="audio"):
        base = vn_game_dir()
        full = os.path.join(base, root)
        exts = {'.ogg', '.mp3', '.wav', '.opus', '.flac'}
        out = []
        try:
            for r, _, fs in os.walk(full):
                for f in fs:
                    if os.path.splitext(f.lower())[1] in exts:
                        rel = os.path.relpath(os.path.join(r, f), base)
                        out.append(rel.replace('\\', '/'))
        except:
            pass
        return out

    # ?? Character/Scene lookups ???????????????????

    def vn_find_char(proj, cid):
        for c in proj.get('characters', []):
            if c['id'] == cid:
                return c
        return None

    def vn_find_scene(proj, sid):
        for s in proj.get('scenes', []):
            if s['id'] == sid:
                return s
        return None

    def vn_get_scene_bg(scene, project=None, visited=None):
        if visited is None:
            visited = set()
        if scene['id'] in visited:
            return None
        visited.add(scene['id'])

        if scene.get('bg'):
            return scene['bg']
        for ev in scene.get('events', []):
            if ev.get('type') == 'bg' and ev.get('bg'):
                return ev['bg']
            for i in range(1, 10):
                layer_data = ev.get('layer' + str(i))
                if layer_data and layer_data.get('type') == 'bg' and layer_data.get('bg'):
                    return layer_data['bg']
                    
        # If no bg found and we have project data, check incoming scenes
        if project:
            for other in project.get('scenes', []):
                if other['id'] == scene['id']:
                    continue
                is_incoming = False
                for ev in other.get('events', []):
                    if ev.get('type') == 'choice':
                        for opt in ev.get('opts', []):
                            if opt.get('scene') == scene['id']:
                                is_incoming = True
                                break
                    elif ev.get('type') == 'jump' and ev.get('scene_id') == scene['id']:
                        is_incoming = True
                    if is_incoming:
                        break
                
                if is_incoming:
                    bg = vn_get_scene_bg(other, project, visited)
                    if bg:
                        return bg
        return None

    def vn_find_event(scene, eid):
        for e in scene.get('events', []):
            if e['id'] == eid:
                return e
        return None

    def vn_char_sprite(proj, char_id, pose):
        c = vn_find_char(proj, char_id)
        if c:
            sprites = c.get('sprites', {})
            if sprites.get(pose):
                return sprites[pose]
        return None


    # ?? Ren'Py Script Importer ????????????????????\r\n
    def vn_import_rpy(folder_path, title="Imported Project", author="Author"):
        """
        Parse a standard Ren'Py game folder and convert it into a VNV Maker project.
        Supports: labels (->scenes), say (->dialogue/narration), menu (->choice), jump/call (->jump).
        Returns (project_dict, warnings_list).
        """
        import re, os

        warnings = []
        proj = vn_new_project(title, author)

        # ── 1. Collect all .rpy files ─────────────────────────────────────────
        game_dir = folder_path
        if not os.path.isdir(game_dir):
            return None, ["Folder not found: " + folder_path]

        rpy_files = []
        for root, dirs, files in os.walk(game_dir):
            # Skip vn_maker sub-folder to avoid reading ourselves
            dirs[:] = [d for d in dirs if d not in ('vn_maker',)]
            for f in files:
                if f.endswith('.rpy') and f not in ('options.rpy', 'gui.rpy', 'screens.rpy'):
                    rpy_files.append(os.path.join(root, f))

        if not rpy_files:
            return None, ["No .rpy script files found in: " + folder_path]

        # ── 2. Collect & deduplicate all lines ────────────────────────────────
        all_lines = []
        for fp in sorted(rpy_files):
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                    all_lines.extend(fh.readlines())
            except Exception as e:
                warnings.append("Could not read {}: {}".format(os.path.basename(fp), str(e)))

        # ── 3. Parse character definitions  `define e = Character("Eileen")` ──
        char_var_map = {}   # varname -> char_id
        char_def_re = re.compile(
            r'^define\s+(\w+)\s*=\s*Character\s*\(\s*["\']([^"\']+)["\']', re.M)
        for m in char_def_re.finditer(''.join(all_lines)):
            varname, charname = m.group(1), m.group(2)
            # Create character in project
            ch = vn_new_character(charname)
            proj['characters'].append(ch)
            char_var_map[varname] = ch['id']

        # ── 4. Tokenise lines into (indent, text) ─────────────────────────────
        tokens = []
        for raw in all_lines:
            stripped = raw.rstrip('\r\n')
            content  = stripped.lstrip()
            if not content or content.startswith('#'):
                continue
            indent = len(stripped) - len(content)
            tokens.append((indent, content))

        # ── 5. Walk tokens – state machine ────────────────────────────────────
        label_re   = re.compile(r'^label\s+([\w.]+)\s*:')
        say_re     = re.compile(r'^(\w+)\s+"(.*)"')
        narr_re    = re.compile(r'^"(.*)"')
        jump_re    = re.compile(r'^jump\s+([\w.]+)')
        call_re    = re.compile(r'^call\s+([\w.]+)')
        menu_re    = re.compile(r'^menu\s*:')
        choice_re  = re.compile(r'^"([^"]+)"\s*:')
        scene_re   = re.compile(r'^scene\s+([\w/.\- ]+)')
        play_re    = re.compile(r'^play\s+music\s+["\']([^"\']+)["\']')

        scene_nodes  = {}   # label -> scene_dict
        scene_order  = []
        pending_jumps = []  # (scene_id, target_label) resolved after all scenes built
        current_scene = None
        in_menu       = False
        menu_ev       = None

        def finish_menu():
            nonlocal in_menu, menu_ev
            if in_menu and menu_ev and current_scene:
                current_scene['events'].append(menu_ev)
            in_menu  = False
            menu_ev  = None

        for idx, (indent, line) in enumerate(tokens):

            # ── Label ──────────────────────────────────────────────────────────
            m = label_re.match(line)
            if m:
                finish_menu()
                lbl = m.group(1)
                sc  = vn_new_scene(lbl)
                scene_nodes[lbl] = sc
                scene_order.append(lbl)
                proj['scenes'].append(sc)
                current_scene = sc
                if lbl in ('start', 'START') and not proj.get('start'):
                    proj['start'] = sc['id']
                continue

            if current_scene is None:
                continue

            # ── scene command (background) ─────────────────────────────────────
            m = scene_re.match(line)
            if m:
                bg_name = m.group(1).strip()
                ev = vn_new_bg(bg_name)
                current_scene['events'].append(ev)
                current_scene['bg'] = bg_name
                continue

            # ── play music ────────────────────────────────────────────────────
            m = play_re.match(line)
            if m:
                ev = vn_new_music(m.group(1))
                current_scene['events'].append(ev)
                continue

            # ── menu: block ────────────────────────────────────────────────────
            m = menu_re.match(line)
            if m:
                finish_menu()
                in_menu  = True
                menu_ev  = vn_new_choice("")
                menu_ev['opts'] = []
                continue

            # ── choice option inside menu ──────────────────────────────────────
            if in_menu:
                m = choice_re.match(line)
                if m:
                    menu_ev['opts'].append({
                        'id':    str(uuid.uuid4())[:6],
                        'text':  m.group(1),
                        'scene': None,   # resolved in pass 2
                        '_lbl':  None,   # will be filled by next jump inside block
                    })
                    continue
                # jump inside a choice block
                m = jump_re.match(line)
                if m and menu_ev and menu_ev['opts']:
                    target = m.group(1)
                    menu_ev['opts'][-1]['_lbl'] = target
                    continue

            # ── jump / call ────────────────────────────────────────────────────
            m = jump_re.match(line) or call_re.match(line)
            if m:
                finish_menu()
                target = m.group(1)
                ev = vn_new_jump(scene_id=None)
                ev['_target_lbl'] = target   # resolve later
                current_scene['events'].append(ev)
                pending_jumps.append((current_scene['id'], ev, target))
                continue

            # ── say (character dialogue) ───────────────────────────────────────
            m = say_re.match(line)
            if m:
                finish_menu()
                varname, text = m.group(1), m.group(2)
                char_id = char_var_map.get(varname)
                if char_id:
                    ev = vn_new_dialogue(char_id=char_id, text=text)
                else:
                    # Unknown variable — treat as narration
                    ev = vn_new_narration(varname + ': ' + text)
                current_scene['events'].append(ev)
                continue

            # ── narration (standalone quoted string) ───────────────────────────
            m = narr_re.match(line)
            if m:
                finish_menu()
                ev = vn_new_narration(m.group(1))
                current_scene['events'].append(ev)
                continue

        finish_menu()

        # ── 6. Resolve jump targets & choice destinations ─────────────────────
        for sc_id, ev, target_lbl in pending_jumps:
            target_sc = scene_nodes.get(target_lbl)
            if target_sc:
                ev['scene_id'] = target_sc['id']
            else:
                warnings.append("Jump target '{}' not found as a label.".format(target_lbl))

        # Resolve choice opts
        for sc in proj['scenes']:
            for ev in sc.get('events', []):
                if ev.get('type') == 'choice':
                    for opt in ev.get('opts', []):
                        lbl = opt.pop('_lbl', None)
                        if lbl:
                            target_sc = scene_nodes.get(lbl)
                            if target_sc:
                                opt['scene'] = target_sc['id']
                            else:
                                warnings.append("Choice target '{}' not found.".format(lbl))

        # ── 7. Auto-set start scene if not found ─────────────────────────────
        if not proj.get('start') and proj['scenes']:
            proj['start'] = proj['scenes'][0]['id']

        if not proj['scenes']:
            return None, ["No labels found in the scripts — nothing to import."]

        warnings.insert(0, "Imported {} scenes, {} characters.".format(
            len(proj['scenes']), len(proj['characters'])))

        return proj, warnings


