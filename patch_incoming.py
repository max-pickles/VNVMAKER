path = r'game\vn_maker\vn_scene_editor.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# ── PATCH 1: Add helper function ─────────────────────────────────────────────
old1 = (
    '    def _vn_se_outgoing_scenes(proj, sc):\n'
    '        """Return ordered list of scene dicts this scene links to via choice/jump events."""\n'
)
new1 = (
    '    def _vn_se_incoming_scenes(proj, sc):\n'
    '        """Return ordered list of scene dicts that link TO this scene via choice/jump events."""\n'
    '        my_id = sc.get("id", "")\n'
    '        seen, result = set(), []\n'
    '        for other in proj.get("scenes", []):\n'
    '            if other.get("id") == my_id:\n'
    '                continue\n'
    '            for ev in other.get("events", []):\n'
    '                t = ev.get("type", "")\n'
    '                linked = False\n'
    '                if t == "choice":\n'
    '                    if any(opt.get("scene") == my_id for opt in ev.get("opts", [])):\n'
    '                        linked = True\n'
    '                elif t == "jump" and ev.get("scene_id") == my_id:\n'
    '                    linked = True\n'
    '                if linked and other["id"] not in seen:\n'
    '                    result.append(other)\n'
    '                    seen.add(other["id"])\n'
    '                    break\n'
    '        return result\n'
    '\n'
    '    def _vn_se_outgoing_scenes(proj, sc):\n'
    '        """Return ordered list of scene dicts this scene links to via choice/jump events."""\n'
)
if old1 in src:
    src = src.replace(old1, new1, 1)
    print("PATCH 1 OK")
else:
    print("PATCH 1 FAILED")

# ── PATCH 2: Add _in_scenes computation near _conn_scenes ────────────────────
old2 = (
    '        ## Outgoing scene connections (choice opts + jump targets) shown as portal cols after FINISH\n'
    '        $ _conn_scenes = _vn_se_outgoing_scenes(vns.project, sc)\n'
)
new2 = (
    '        ## Incoming scenes (scenes that link TO this scene) — shown as portal cols before START\n'
    '        $ _in_scenes = _vn_se_incoming_scenes(vns.project, sc)\n'
    '        ## Outgoing scene connections (choice opts + jump targets) shown as portal cols after FINISH\n'
    '        $ _conn_scenes = _vn_se_outgoing_scenes(vns.project, sc)\n'
)
if old2 in src:
    src = src.replace(old2, new2, 1)
    print("PATCH 2 OK")
else:
    print("PATCH 2 FAILED")

# ── PATCH 3: Insert incoming portal columns + adjust _vp_w ───────────────────
old3 = (
    '                        ## Scrollable click-columns: each column is _col_w wide, cells are _col_w x _row_h (square)\n'
    '                        $ _vp_w = renpy.config.screen_width - 110 - 1 - (24 if _layer_count > _vis_layers else 0)\n'
)
new3 = (
    '                        ## Incoming scene portal columns (fixed, before scroll area)\n'
    '                        $ _in_panel_w = len(_in_scenes) * (_col_w + 1)\n'
    '                        for _in_sc in _in_scenes:\n'
    '                            vbox spacing 0 xsize _col_w ysize _zone2_h:\n'
    '                                ## Header strip\n'
    '                                frame background Solid("#0a1022") xsize _col_w ysize _hdr_h padding (0, 0):\n'
    '                                    vbox xalign 0.5 yalign 0.5 spacing 1:\n'
    '                                        text "\u2190" style "vn_t" size 10 bold True xalign 0.5 color "#4488ee"\n'
    '                                frame background Solid("#0d1830") xsize _col_w ysize 1 padding (0, 0)\n'
    '                                ## Clickable portal body\n'
    '                                $ _in_flag_h = min(_vis_layers, _layer_count - _ls) * (_row_h + 1)\n'
    '                                button xsize _col_w ysize _in_flag_h padding (0, 2):\n'
    '                                    background Solid("#070d1a")\n'
    '                                    hover_background Solid("#0e1e3a")\n'
    '                                    action [SetField(vns, "scene_id", _in_sc["id"]), Function(vns.go, "scene_editor")]\n'
    '                                    fixed xfill True yfill True:\n'
    '                                        vbox xalign 0.5 yalign 0.5 spacing 2:\n'
    '                                            text "\u2b05" size 20 xalign 0.5 color "#4488ee"\n'
    '                                            text (_in_sc.get("label", "?")[:10]) size 8 xalign 0.5 color "#4488ee" text_align 0.5\n'
    '                                frame background Solid("#111c38") xsize _col_w ysize 1 padding (0, 0)\n'
    '                        if _in_scenes:\n'
    '                            frame background Solid("#111c38") xsize 1 ysize _zone2_h padding (0, 0)\n'
    '\n'
    '                        ## Scrollable click-columns: each column is _col_w wide, cells are _col_w x _row_h (square)\n'
    '                        $ _vp_w = renpy.config.screen_width - 110 - 1 - _in_panel_w - (24 if _layer_count > _vis_layers else 0)\n'
)
if old3 in src:
    src = src.replace(old3, new3, 1)
    print("PATCH 3 OK")
else:
    print("PATCH 3 FAILED - searching...")
    idx = src.find("## Scrollable click-columns: each column is _col_w wide")
    print(repr(src[idx-10:idx+200]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("Done.")
