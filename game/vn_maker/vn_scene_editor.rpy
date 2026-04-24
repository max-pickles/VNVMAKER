## ───────────────────────────────────────────────
##  VN Maker - Scene Editor (Timeline Drag & Drop)
## ───────────────────────────────────────────────

init python:
    def _vn_is_input_focused():
        if store.vns.ui.get('_ted_focused', False) or store.vns.ui.get('_ted_live_focused', False):
            return True
        f = renpy.display.focus.get_focused()
        import renpy.display.behavior as b
        return isinstance(f, b.Input)

    def _vn_add_event(sc, factory):
        """Add an event with undo support. Layer 0 = new click slot.
        Layer 1/2 = add data to current click.
        """
        import copy
        ev    = factory()
        evs   = sc.setdefault('events', [])
        ph    = vns.ui.get('se_ph', len(evs))
        layer = vns.ui.get('se_active_layer', 0)
        ev_type = ev.get('type', 'event')

        if layer == 0:
            ## Layer 0: ALWAYS replace the slot at the playhead.
            ## New slots are only created by the 🎌 Start flag, not by placing a tool.
            if ph > len(evs):
                while len(evs) < ph:
                    evs.append(vn_new_empty_slot())

            ph_slot = evs[ph] if ph < len(evs) else None
            old_slot = ph_slot

            def _do_add(pp=ph, es=evs, new_ev=ev, old_ev=old_slot):
                if pp < len(es):
                    es[pp] = new_ev
                else:
                    es.append(new_ev)
                vns.ui['se_ph'] = pp
                vns.event_id = new_ev['id']
                vns.save_silent()
                renpy.restart_interaction()
            def _undo_add(pp=ph, es=evs, old_ev=old_slot):
                if old_ev is not None and pp < len(es):
                    es[pp] = old_ev
                elif pp < len(es):
                    es.pop(pp)
                vns.ui['se_ph'] = pp
                vns.event_id = None
                vns.save_silent()
                renpy.restart_interaction()
            vns.history.commit("Place " + ev_type.title(), _do_add, _undo_add)
        else:
            ## Other layers: write data INTO the current click slot
            if ph < len(evs):
                target = evs[ph]
            else:
                # Pad the timeline with empty slots up to the target index
                while len(evs) <= ph:
                    evs.append(vn_new_empty_slot())
                target = evs[ph]
                vns.event_id = target['id']
            layer_key = 'layer' + str(layer)
            old_ldata = copy.deepcopy(target.get(layer_key))
            new_ldata = {
                'type': ev.get('type', 'effect'),
                'text': ev.get('text', ''),
                'music': ev.get('music', ''),
                'image': ev.get('image', ''),
            }
            def _do_layer(t=target, k=layer_key, nd=new_ldata):
                t.setdefault(k, {}).update(nd)
                vns.event_id = t['id']
                vns.save_silent()
                renpy.restart_interaction()
            def _undo_layer(t=target, k=layer_key, od=old_ldata):
                if od is None:
                    t.pop(k, None)
                else:
                    t[k] = od
                vns.save_silent()
                renpy.restart_interaction()
            vns.history.commit("Add layer data", _do_layer, _undo_layer)

    def _vn_insert_click(sc, ci):
        """Used by the Scene Boundary Flags to explicity inject a new click at a specific index."""
        evs = sc.setdefault('events', [])
        insert_at = min(abs(ci), len(evs))
        def _do_add():
            if insert_at >= len(evs):
                evs.append(vn_new_empty_slot())
            else:
                evs.insert(insert_at, vn_new_empty_slot())
            vns.ui['se_ph'] = insert_at
            vns.save_silent()
            renpy.restart_interaction()
        def _undo_add():
            if insert_at < len(evs):
                evs.pop(insert_at)
            vns.ui['se_ph'] = max(0, insert_at - 1)
            vns.save_silent()
            renpy.restart_interaction()
        vns.history.commit("Insert Click", _do_add, _undo_add)

    def _vn_remove_last_click(sc):
        """Used by the End Flag to shrink the timeline."""
        evs = sc.get('events', [])
        if not evs: return
        popped = evs[-1]
        def _do_remove():
            evs.pop()
            vns.ui['se_ph'] = min(vns.ui.get('se_ph', 0), max(0, len(evs) - 1))
            vns.save_silent()
            renpy.restart_interaction()
        def _undo_remove():
            evs.append(popped)
            vns.save_silent()
            renpy.restart_interaction()
        vns.history.commit("Remove Last Click", _do_remove, _undo_remove)

    def _vn_move_ev(sc, i, delta):
        evs = sc['events']
        j = i + delta
        if 0 <= j < len(evs):
            def _do(ii=i, jj=j):
                evs[ii], evs[jj] = evs[jj], evs[ii]
                vns.save_silent()
                renpy.restart_interaction()
            def _undo(ii=i, jj=j):
                evs[jj], evs[ii] = evs[ii], evs[jj]
                vns.save_silent()
                renpy.restart_interaction()
            vns.history.commit("Move Event", _do, _undo)
        else:
            vns.save_silent()

    def _vn_delete_event(sc):
        """Clear the content of the selected cell.
        NEVER removes a click slot or layer -- use C- / L- for that.
        Layer 0: wipe event type + text/music/image fields (slot stays empty).
        Layer 1+: remove the sub-layer data dict from the event.
        """
        evs   = sc.get('events', [])
        ph    = vns.ui.get('se_ph', 0)
        layer = vns.ui.get('se_active_layer', 0)
        if ph >= len(evs):
            vns.notify("Nothing selected.", "warn")
            return
        ev = evs[ph]
        if layer == 0:
            ## Clear this event's content but keep the slot
            old_id = ev.get('id')
            ev.clear()
            ev['id'] = old_id  ## preserve id so the slot still exists
            ev['type'] = ''
            vns.ui['se_inspector'] = None
            vns.save_silent()
            vns.notify("Cell cleared.", "ok")
        else:
            ## Remove sub-layer data from the event
            layer_key = 'layer' + str(layer)
            if layer_key in ev:
                del ev[layer_key]
                vns.ui['se_inspector'] = None
                vns.save_silent()
                vns.notify("Layer " + str(layer + 1) + " data cleared.", "ok")
            else:
                vns.notify("No data on layer " + str(layer + 1) + ".", "warn")
        renpy.restart_interaction()

    def _vn_add_scene(label="Scene"):
        """Create a new scene at click-time and select it immediately."""
        if not vns.project:
            return
        sc = vn_new_scene(label or "Scene")
        vns.project['scenes'].append(sc)
        vns.scene_id = sc['id']
        ## sync graph layout so the node appears straight away
        i = len(vns.project['scenes']) - 1
        vng.layout[sc['id']] = _vng_default_pos(i, len(vns.project['scenes']))
        ## clear the input box
        vns.ui['scene_label'] = ''
        ## save directly ?" avoids the "Project saved!" double-notification
        vn_save(vns.project)
        ## single notification; its restart_interaction() is enough
        vns.notify("Scene added!", "ok")


    def _vn_move_scene(i, delta):
        """Move scene i up (-1) or down (+1) in the project list."""
        scenes = vns.project.get('scenes', [])
        j = i + delta
        if 0 <= j < len(scenes):
            def _do(ii=i, jj=j):
                scenes[ii], scenes[jj] = scenes[jj], scenes[ii]
                vns.save_silent()
                renpy.restart_interaction()
            def _undo(ii=i, jj=j):
                scenes[jj], scenes[ii] = scenes[ii], scenes[jj]
                vns.save_silent()
                renpy.restart_interaction()
            vns.history.commit("Move Scene", _do, _undo)

    def _vn_set_start_scene(sc_id):
        """Set the specified scene as the start scene."""
        vns.project['start'] = sc_id
        vns.save_silent()
        vns.notify("Start scene set!", "ok")
        renpy.restart_interaction()

    def _vn_delete_event_undo(sc, ev):
        """Delete an event with full undo support."""
        if ev not in sc.get('events', []):
            return
        idx   = sc['events'].index(ev)
        ev_id = ev.get('id')
        def _do():
            if ev in sc['events']:
                sc['events'].remove(ev)
            if vns.event_id == ev_id:
                vns.event_id = None
            vns.save_silent()
            renpy.restart_interaction()
        def _undo():
            sc['events'].insert(idx, ev)
            vns.event_id = ev_id
            vns.save_silent()
            renpy.restart_interaction()
        vns.history.commit("Delete Event", _do, _undo)

    def _vn_delete_scene_undo(sc):
        """Delete a scene with full undo support."""
        if not vns.project or sc not in vns.project.get('scenes', []):
            return
        idx       = vns.project['scenes'].index(sc)
        sc_id     = sc['id']
        layout_pos = vng.layout.get(sc_id)
        def _do():
            if sc in vns.project['scenes']:
                vns.project['scenes'].remove(sc)
            if vns.scene_id == sc_id:
                vns.scene_id = None
            vng.layout.pop(sc_id, None)
            vns.save_silent()
            vns.notify("Scene deleted.", "warn")
            renpy.restart_interaction()
        def _undo():
            vns.project['scenes'].insert(idx, sc)
            if layout_pos:
                vng.layout[sc_id] = layout_pos
            vns.scene_id = sc_id
            vns.save_silent()
            vns.notify("Scene restored.", "ok")
            renpy.restart_interaction()
        vns.history.commit("Delete Scene", _do, _undo)


## ── Scene Editor Canvas State ────────────────────────────────────────────────
default _vn_se_pan_x   = 0.0
default _vn_se_pan_y   = 0.0
default _vn_se_zoom    = 1.0
default _vn_se_panning = False
default _vn_se_last_xy = None
default _vn_se_space   = False
default _vn_se_playing = False
default _vn_se_ph_time = 0.0   ## fractional playhead position (click units)
default _vn_se_xadj    = ui.adjustment()

init python:
    import pygame as _se_pg


    ## ── Tool system helpers ──────────────────────────────────────────────────
    def _vn_set_tool(tool_type):
        """Toggle the active bottom-bar tool. Second click on same tool disarms."""
        if vns.ui.get('se_tool') == tool_type:
            vns.ui['se_tool'] = None
        else:
            vns.ui['se_tool'] = tool_type
        vns.ui['se_tool_file'] = None
        renpy.restart_interaction()

    def _vn_list_audio():
        """Return list of audio files in the game folder."""
        try:
            exts = ('.mp3', '.ogg', '.wav', '.flac')
            return sorted([f for f in renpy.list_files()
                           if f.lower().endswith(exts)])
        except Exception:
            return []

    def _vn_list_images():
        """Return list of image files, excluding Ren'Py engine internals."""
        try:
            exts = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
            EXCLUDE = ('gui/', 'cache/', 'renpy/', 'common/', 'fonts/')
            return sorted([f for f in renpy.list_files()
                           if f.lower().endswith(exts)
                           and not any(f.startswith(ex) for ex in EXCLUDE)])
        except Exception:
            return []

    def _vn_apply_tool_to_click(sc, ci, tgt_li=None, tool=None):
        """Place the armed tool at click-column ci. Allows direct override of the target layer."""
        ## Safety: never operate if no valid project is loaded
        if not vns.project or not vns.project.get('id'):
            return
        if not sc:
            return
        tool = tool or vns.ui.get('se_tool')
        if not tool:
            return
            
        if tgt_li is not None:
            vns.ui['se_active_layer'] = tgt_li
            
        evs = sc.setdefault('events', [])
        # Move playhead there (adjusting for column offset)
        target_idx = max(0, ci - 1)
        ev = evs[target_idx] if target_idx < len(evs) else None
        vns.ui['se_ph'] = target_idx
        vns.event_id = ev['id'] if ev else None
        # Add the event
        factories = {
            'dialogue': vn_new_dialogue,
            'narration': vn_new_narration,
            'choice': vn_new_choice,
            'effect': vn_new_effect,
            'wait': vn_new_wait,
            'music': vn_new_music,
            'bg': vn_new_bg,
            'image': vn_new_image,
            'sfx': vn_new_sfx,
        }
        
        factory = factories.get(tool)
        if factory:
            _vn_add_event(sc, factory)
            
        vns.save_silent()
        ## Select the newly placed cell so the right inspector opens
        evs2 = sc.get('events', [])
        ev_new = evs2[ci] if ci < len(evs2) else None
        _vn_se_select_cell(ci, ev_new, vns.ui.get('se_active_layer', 0))
        renpy.restart_interaction()

    def _vn_apply_music(sc, filename):
        """Set music on the currently selected event, or create a wait event."""
        evs = sc.setdefault('events', [])
        ph  = vns.ui.get('se_ph', 0)
        if ph < len(evs) and evs[ph]:
            evs[ph]['music'] = filename
        else:
            ev = vn_new_wait()
            ev['music'] = filename
            sc['events'] = evs
            evs.insert(ph, ev)
        vns.save_silent()
        vns.notify(filename.split('/')[-1] + " set!", "ok")
        if not vns.ui.get('se_tool_pin'):
            vns.ui['se_tool'] = None
        renpy.restart_interaction()

    def _vn_apply_bg(sc, filename):
        """Set the scene background image."""
        sc['bg'] = filename
        vns.save_silent()
        vns.notify(filename.split('/')[-1] + " set as BG!", "ok")
        if not vns.ui.get('se_tool_pin'):
            vns.ui['se_tool'] = None
        renpy.restart_interaction()

    ## ── Drag physics ─────────────────────────────────────────────────────────
    def _vn_timeline_clip_dragged(drags, drop):
        drag = drags[0]

        # Helper: snap a tool drag back to its home position
        def _snap_tool_home(dn):
            ttype = dn.split("_")[1] if "_" in dn else "dialogue"
            orig_x = 195 if ttype == "dialogue" else 346 if ttype == "music" else 496
            orig_y = int(renpy.config.screen_height) - 32
            drag.snap(orig_x, orig_y, 0.18)

        ## ── TOOL EMOJI DROP ──────────────────────────────────────────────────
        if drag.drag_name.startswith("tool_"):
            _snap_tool_home(drag.drag_name)

            sc = vns.scene
            if not sc:
                return

            # Use mouse position to find the drop cell
            mx, my = renpy.get_mouse_pos()
            sh = int(renpy.config.screen_height)
            sw = int(renpy.config.screen_width)

            col_w    = vns.ui.get('_tl_col_w', 50)
            row_h    = vns.ui.get('_tl_row_h', 50)
            hdr_h    = vns.ui.get('_tl_hdr_h', 36)
            zone23_h = vns.ui.get('_tl_zone23_h', 200)
            ls       = vns.ui.get('_tl_ls', 0)
            scroll_x = vns.ui.get('_tl_scroll_x', 0)

            # Timeline Y range (zone 2 sits at the bottom above zone 3)
            tl_top    = sh - zone23_h
            tl_bottom = tl_top + hdr_h + vns.ui.get('_tl_vis_layers', 3) * (row_h + 1)

            # Timeline X range (after 110px label column)
            tl_left = 110

            if not (tl_left <= mx <= sw and tl_top + hdr_h <= my <= tl_bottom):
                # Mouse not over the timeline grid at all
                return

            # Column index
            tx = mx - tl_left + scroll_x
            ci = int(tx // (col_w + 1))

            # Row/layer index
            ty = my - tl_top - hdr_h
            li_rel = int(ty // (row_h + 1))
            li = ls + li_rel
            li = max(1, li)  ## emoji drags always go to alternate layers (1+)

            tool_type = drag.drag_name.split("_")[1]
            evs = sc.setdefault('events', [])

            if li == 0:
                # Layer 0: replace the main event slot
                factories = {
                    'dialogue': vn_new_dialogue, 'narration': vn_new_narration,
                    'choice': vn_new_choice, 'effect': vn_new_effect,
                    'wait': vn_new_wait, 'music': vn_new_music,
                    'bg': vn_new_bg, 'image': vn_new_image, 'sfx': vn_new_sfx,
                }
                factory = factories.get(tool_type)
                if factory:
                    target_idx = max(0, ci - 1)
                    while len(evs) <= target_idx:
                        evs.append(vn_new_wait())
                    new_ev = factory()
                    evs[target_idx] = new_ev
                    vns.ui['se_ph'] = target_idx
                    vns.ui['se_active_layer'] = 0
                    vns.event_id = new_ev['id']
                    vns.save_silent()
                    _vn_se_select_cell(max(1, ci), new_ev, 0)
            else:
                _vn_apply_tool_to_click(sc, ci, li, tool_type)

            renpy.restart_interaction()
            return

        try:
            tgt_parts = drop.drag_name.split("_")
            tgt_ci = int(tgt_parts[1])
            tgt_li = int(tgt_parts[2])
        except (IndexError, ValueError, AttributeError):
            if drag.drag_name.startswith("tool_"):
                tool_type = drag.drag_name.split("_")[1]
                orig_x = 176 if tool_type == "dialogue" else 331 if tool_type == "music" else 481
                drag.snap(orig_x, int(renpy.config.screen_height) - 52, 0.15)
            else:
                drag.snap(drag.start_x, drag.start_y, 0.2)
            return

        sc = vns.scene
        if not sc:
            if drag.drag_name.startswith("tool_"):
                tool_type = drag.drag_name.split("_")[1]
                orig_x = 176 if tool_type == "dialogue" else 331 if tool_type == "music" else 481
                drag.snap(orig_x, int(renpy.config.screen_height) - 52, 0.15)
            else:
                drag.snap(drag.start_x, drag.start_y, 0.2)
            return
            
        evs = sc.setdefault('events', [])

        if drag.drag_name.startswith("tool_"):
            tool_type = drag.drag_name.split("_")[1]
            orig_x = 176 if tool_type == "dialogue" else 331 if tool_type == "music" else 481
            drag.snap(orig_x, int(renpy.config.screen_height) - 52, 0.15)
            
            # Overwrite the cell if layer 0
            if tgt_li == 0:
                factories = {
                    'dialogue': vn_new_dialogue, 'narration': vn_new_narration, 'choice': vn_new_choice,
                    'effect': vn_new_effect, 'wait': vn_new_wait, 'music': vn_new_music,
                    'bg': vn_new_bg, 'image': vn_new_image, 'sfx': vn_new_sfx,
                }
                factory = factories.get(tool_type)
                if factory:
                    target_idx = max(0, tgt_ci - 1)
                    while len(evs) <= target_idx:
                        evs.append(vn_new_wait())
                    
                    new_ev = factory()
                    evs[target_idx] = new_ev
                    vns.ui['se_ph'] = target_idx
                    vns.ui['se_active_layer'] = 0
                    vns.event_id = new_ev['id']
                    vns.save_silent()
                    _vn_se_select_cell(tgt_ci, new_ev, 0)
            else:
                _vn_apply_tool_to_click(sc, tgt_ci, tgt_li, tool_type)

            renpy.restart_interaction()
            return

        elif drag.drag_name.startswith("clip_"):
            try:
                src_parts = drag.drag_name.split("_")
                src_ci = int(src_parts[1])
                src_li = int(src_parts[2])
            except (IndexError, ValueError):
                drag.snap(drag.start_x, drag.start_y, 0.2)
                return

            if src_ci == tgt_ci and src_li == tgt_li:
                drag.snap(drag.start_x, drag.start_y, 0.2)
                return

            # Ensure array is safely padded
            while len(evs) <= max(src_ci, tgt_ci):
                evs.append({})

            def get_k(li): return None if li == 0 else 'layer' + str(li)
            src_k = get_k(src_li)
            tgt_k = get_k(tgt_li)

            s_data = _vn_se_extract_core(evs, src_ci, src_k)
            t_data = _vn_se_extract_core(evs, tgt_ci, tgt_k)
            _vn_se_inject_core(evs, tgt_ci, tgt_k, s_data)
            _vn_se_inject_core(evs, src_ci, src_k, t_data)

            # Update selection single
            vns.ui['se_ph'] = max(0, tgt_ci - 1)
            vns.ui['se_active_layer'] = tgt_li
            vns.ui['se_multi'] = [(tgt_ci, tgt_li)]

            drag.snap(drag.start_x, drag.start_y, 0.2)
            renpy.restart_interaction()
            return

            vns.save_silent()
            renpy.restart_interaction()

    def _vn_se_cam_fn(trans, st, at):
        trans.xoffset = int(store._vn_se_pan_x)
        trans.yoffset = int(store._vn_se_pan_y)
        trans.zoom    = store._vn_se_zoom
        return None  ## only redraw when explicitly triggered via restart_interaction

    def _vn_se_reset_view():
        store._vn_se_pan_x   = 0.0
        store._vn_se_pan_y   = 0.0
        store._vn_se_zoom    = 1.0
        store._vn_se_panning = False
        store._vn_se_last_xy = None
        renpy.restart_interaction()

    def _vn_se_play_step():
        """Advance playhead by one click slot."""
        evs = vns.scene.get('events', []) if vns.scene else []
        cur = vns.ui.get('se_ph', 0)
        nxt = cur + 1
        if nxt < len(evs):
            _vn_se_move_ph(nxt + 1, evs[nxt])
            # Auto scroll if off screen
            _t_zoom = vns.ui.get('se_timeline_zoom', 1.0)
            _col_w = int(56 * _t_zoom)
            ph_x = nxt * (_col_w + 1)
            adj = store._vn_se_xadj
            try:
                vw = renpy.config.screen_width - 110 # approx viewport width
                if ph_x > adj.value + vw - (_col_w*2):
                    adj.value = min(adj.range, adj.value + vw // 2)
                elif ph_x < adj.value:
                    adj.value = max(0, ph_x - vw // 4)
            except:
                pass
        else:
            store._vn_se_playing = False
        renpy.restart_interaction()

    class SceneCanvasEvents(renpy.Displayable):
        """Transparent overlay intercepting mouse events for the Scene Editor preview."""
        def __init__(self, **kwargs):
            super(SceneCanvasEvents, self).__init__(**kwargs)

        def render(self, width, height, st, at):
            return renpy.Render(width, height)

        def event(self, ev, x, y, st):
            ## Track spacebar for pan mode
            if ev.type == _se_pg.KEYDOWN and ev.key == _se_pg.K_SPACE:
                store._vn_se_space = True
            elif ev.type == _se_pg.KEYUP and ev.key == _se_pg.K_SPACE:
                store._vn_se_space = False
                store._vn_se_panning = False
                store._vn_se_last_xy = None

            if ev.type == _se_pg.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    if store._vn_se_space:
                        store._vn_se_panning = True
                        store._vn_se_last_xy = (x, y)
                        raise renpy.IgnoreEvent()
                    elif vns.ui.get('se_tool'):
                        ## Click on canvas while a tool is armed → disarm the tool
                        vns.ui['se_tool'] = None
                        renpy.restart_interaction()
                        raise renpy.IgnoreEvent()
                elif ev.button == 4:   ## scroll up → zoom in (Ctrl+Scroll only)
                    if _se_pg.key.get_mods() & _se_pg.KMOD_CTRL:
                        oz = store._vn_se_zoom
                        store._vn_se_zoom = min(4.0, oz * 1.15)
                        store._vn_se_pan_x = x - (x - store._vn_se_pan_x) * (store._vn_se_zoom / oz)
                        store._vn_se_pan_y = y - (y - store._vn_se_pan_y) * (store._vn_se_zoom / oz)
                        renpy.restart_interaction()
                        raise renpy.IgnoreEvent()
                elif ev.button == 5:   ## scroll down → zoom out (Ctrl+Scroll only)
                    if _se_pg.key.get_mods() & _se_pg.KMOD_CTRL:
                        oz = store._vn_se_zoom
                        store._vn_se_zoom = max(0.25, oz / 1.15)
                        store._vn_se_pan_x = x - (x - store._vn_se_pan_x) * (store._vn_se_zoom / oz)
                        store._vn_se_pan_y = y - (y - store._vn_se_pan_y) * (store._vn_se_zoom / oz)
                        renpy.restart_interaction()
                        raise renpy.IgnoreEvent()

            elif ev.type == _se_pg.MOUSEBUTTONUP:
                if ev.button == 1:
                    store._vn_se_panning = False
                    store._vn_se_last_xy = None

            elif ev.type == _se_pg.MOUSEMOTION:
                if store._vn_se_panning and store._vn_se_last_xy:
                    dx = x - store._vn_se_last_xy[0]
                    dy = y - store._vn_se_last_xy[1]
                    store._vn_se_pan_x += dx
                    store._vn_se_pan_y += dy
                    store._vn_se_last_xy = (x, y)
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()

        def visit(self):
            return []

    def _vn_se_extract_core(evs, ci, k):
        if k is None:
            c = {}
            if ci >= len(evs): return None
            d = evs[ci]
            if not d.get('type'): return None
            for key in list(d.keys()):
                if not key.startswith('layer') and key != 'id':
                    c[key] = d.pop(key)
            return c
        else:
            if ci >= len(evs): return None
            return evs[ci].pop(k, None)
            
    def _vn_se_inject_core(evs, ci, k, data):
        if not data: return
        while len(evs) <= ci: evs.append({})
        if k is None:
            evs[ci].update(data)
        else:
            evs[ci][k] = data

## Helper: move the scene editor playhead and optionally select event
python early:
    _vn_se_clipboard = []

    def _vn_se_duplicate_core(evs, ci, k):
        import copy
        if k is None:
            c = {}
            if ci >= len(evs): return None
            d = evs[ci]
            if not d.get('type'): return None
            for key in list(d.keys()):
                if not key.startswith('layer') and key != 'id':
                    c[key] = copy.deepcopy(d[key])
            return c
        else:
            if ci >= len(evs): return None
            return copy.deepcopy(evs[ci].get(k, None))

    def _vn_se_copy():
        store._vn_se_clipboard = []
        sc = vns.scene
        if not sc: return
        evs = sc.get('events', [])
        multi = vns.ui.get('se_multi', [])
        if not multi: return
        
        multi.sort(key=lambda c: (c[0], c[1]))
        base_ci = multi[0][0]
        base_li = multi[0][1]
        
        for (ci, li) in multi:
            k = None if li == 0 else 'layer' + str(li)
            data = _vn_se_duplicate_core(evs, ci, k)
            if data and data.get('type'):
                store._vn_se_clipboard.append({
                    'rel_ci': ci - base_ci,
                    'rel_li': li - base_li,
                    'data': data
                })
        vns.notify("Copied to clipboard.", "ok")

    def _vn_se_paste():
        if not store._vn_se_clipboard: return
        sc = vns.scene
        if not sc: return
        evs = sc.setdefault('events', [])
        ph = vns.ui.get('se_ph', 0)
        active_li = vns.ui.get('se_active_layer', 0)
        max_layers = vns.ui.get('se_layers', 3)
        
        import copy
        for item in store._vn_se_clipboard:
            tgt_ci = ph + item['rel_ci']
            tgt_li = active_li + item['rel_li']
            if tgt_li < 0 or tgt_li >= max_layers: continue
            
            k = None if tgt_li == 0 else 'layer' + str(tgt_li)
            _vn_se_inject_core(evs, tgt_ci, k, copy.deepcopy(item['data']))
        
        vns.save_silent()
        renpy.restart_interaction()
        vns.notify("Pasted from clipboard.", "ok")

    def _vn_se_clear_clip(ci, li):
        sc = vns.scene
        if not sc: return
        evs = sc.get('events', [])
        k = None if li == 0 else 'layer' + str(li)
        _vn_se_extract_core(evs, ci, k)
        vns.save_silent()
        renpy.restart_interaction()

    def _vn_se_convert_to_menu(ci, li):
        """Convert the clip at (ci, li) to a Ren'Py menu event, preserving the id."""
        sc = vns.scene
        if not sc: return
        evs = sc.get('events', [])
        if ci >= len(evs): return
        ev = evs[ci]
        if li == 0:
            ## Replace the whole event data in place, keeping the id
            new = vn_new_menu()
            new['id'] = ev['id']
            evs[ci] = new
            vns.event_id = new['id']
        else:
            lkey = 'layer' + str(li)
            new_layer = {'type': 'menu', 'prompt': '', 'opts': [
                {'id': str(uuid.uuid4())[:6], 'text': 'Option 1', 'scene': None},
                {'id': str(uuid.uuid4())[:6], 'text': 'Option 2', 'scene': None},
            ]}
            ev[lkey] = new_layer
        vns.save_silent()
        renpy.restart_interaction()



    def _vn_se_eval_state(sc, max_ci):
        """Evaluate the cumulative background and sprite states up to max_ci slot, including prior scenes."""
        bg = None
        sprites = {}
        fg_images = {}
        
        def _eval_scene(_s, _max_ci=None):
            nonlocal bg, sprites, fg_images
            if _s.get('bg'):
                bg = _s['bg']
                sprites.clear()
                fg_images.clear()
                
            _evs = _s.get('events', [])
            _lim = len(_evs) if _max_ci is None else min(_max_ci + 1, len(_evs))
            for i in range(_lim):
                ev = _evs[i]
                layers = [ev] if ev.get('type') else []
                for k, v in ev.items():
                    if k.startswith('layer') and isinstance(v, dict) and v.get('type'):
                        layers.append(v)
                        
                for item in layers:
                    if item.get('type') == 'bg' and item.get('bg'):
                        bg = item['bg']
                        sprites.clear()
                        fg_images.clear()
                    elif item.get('type') == 'image' and item.get('image'):
                        img_path = item['image']
                        tag = img_path.split('/')[-1].split('.')[0].split()[0]
                        fg_images[tag] = item
                    elif item.get('type') == 'dialogue':
                        char_id = item.get('char_id')
                        if char_id:
                            sprites[char_id] = {
                                'pose': item.get('pose', 'neutral'),
                                'side': item.get('side', 'center'),
                                'event_ref': item
                            }
                            
        if vns.project and 'scenes' in vns.project:
            for _s in vns.project['scenes']:
                if _s['id'] == sc['id']:
                    break
                _eval_scene(_s)
                
        _eval_scene(sc, max_ci)
        
        return bg, sprites, fg_images



    def _vn_se_move_ph(ci, ev):
        vns.ui['se_ph'] = max(0, ci - 1)
        vns.ui.setdefault('se_active_layer', 0)
        vns.ui['se_multi'] = [(ci, 0)]
        if ev:
            vns.event_id = ev['id']
        renpy.restart_interaction()

    def _vn_se_select_cell(ci, ev, layer_idx):
        """Select a click + layer cell, arm the layer, open the inspector."""
        import pygame
        is_shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
        
        vns.ui['se_ph'] = max(0, ci - 1)
        vns.ui['se_active_layer'] = layer_idx
        vns.ui['se_edit_mode'] = False
        vns.notify(f"Selected cell {ci} layer {layer_idx}")
        ## Auto-focus the text editor for dialogue/narration on L1 so user can type immediately
        if layer_idx == 0 and ev and ev.get('type', '') in ('dialogue', 'narration'):
            vns.ui['_ted_focused'] = True
        else:
            vns.ui['_ted_focused'] = False
        
        multi = vns.ui.setdefault('se_multi', [])
        if is_shift:
            if (ci, layer_idx) not in multi:
                multi.append((ci, layer_idx))
            else:
                multi.remove((ci, layer_idx)) # Toggle!
        else:
            vns.ui['se_multi'] = [(ci, layer_idx)]
            
        if ev and ev.get('type', ''):
            vns.event_id = ev['id']
            # Determine inspector mode from layer
            if layer_idx == 0:
                insp = ev.get('type', '')
            else:
                ldata = ev.get('layer' + str(layer_idx), {})
                insp = ldata.get('type', '')
            vns.ui['se_inspector'] = insp if insp else None
            # Pre-fill text buffer for dialogue/narration
            if insp in ('dialogue', 'narration', 'choice'):
                src = ev if layer_idx == 0 else ev.get('layer' + str(layer_idx), {})
                vns.ui['se_edit_text'] = src.get('text', '')
        else:
            vns.event_id = None
        renpy.restart_interaction()

    def _vn_timeline_nudge_clip(dr_x, dr_y):
        """Move selected clip by dx/dy steps, swapping if occupied. Updates active selection."""
        if vns.ui.get('_focus'): return
            
        sc = vns.scene
        if not sc: return
        
        multi = vns.ui.get('se_multi', [])
        # Fallback if se_multi corrupted
        if not multi: 
            multi = [(vns.ui.get('se_ph', 0), vns.ui.get('se_active_layer', 0))]
            
        # Sort so we push blocks securely without internally overriding our own sequence!
        cells = list(multi)
        if dr_x > 0: cells.sort(key=lambda c: c[0], reverse=True)
        elif dr_x < 0: cells.sort(key=lambda c: c[0], reverse=False)
        else:
            if dr_y > 0: cells.sort(key=lambda c: c[1], reverse=True)
            else: cells.sort(key=lambda c: c[1], reverse=False)
            
        evs = sc.setdefault('events', [])
        def get_k(li): return None if li == 0 else 'layer' + str(li)
        
        new_multi = []
        for (src_ci, src_li) in cells:
            tgt_ci = max(0, src_ci + dr_x)
            tgt_li = max(0, min(vns.ui.get('se_layers', 3), src_li + dr_y))
            
            if src_ci == tgt_ci and src_li == tgt_li:
                new_multi.append((src_ci, src_li))
                continue
                
            src_k = get_k(src_li)
            tgt_k = get_k(tgt_li)
            
            s_data = _vn_se_extract_core(evs, src_ci, src_k)
            t_data = _vn_se_extract_core(evs, tgt_ci, tgt_k)
            _vn_se_inject_core(evs, tgt_ci, tgt_k, s_data)
            _vn_se_inject_core(evs, src_ci, src_k, t_data)
            new_multi.append((tgt_ci, tgt_li))
            
            # Keep ph clamped to latest interaction point
            vns.ui['se_ph'] = max(0, tgt_ci - 1)
            vns.ui['se_active_layer'] = tgt_li

        vns.ui['se_multi'] = new_multi
        vns.save_silent()
        renpy.restart_interaction()

    def _vn_se_save_text(sc):
        """Write the live text buffer back to the selected event."""
        evs = sc.get('events', [])
        ph  = vns.ui.get('se_ph', 0)
        li  = vns.ui.get('se_active_layer', 0)
        txt = vns.ui.get('se_edit_text', '')
        if ph < len(evs):
            ev = evs[ph]
            if li == 0:
                ev['text'] = txt
            else:
                lkey = 'layer' + str(li)
                ev.setdefault(lkey, {})['text'] = txt
            vns.save_silent()
            vns.notify("Saved.", "ok")

screen vn_se_context_menu(ci, li):
    zorder 300
    modal True
    
    key "K_ESCAPE" action Hide("vn_se_context_menu")
    ## Right-clicking again while the menu is open just keeps it open (modal blocks it)
    button xfill True yfill True background None action Hide("vn_se_context_menu")
    
    $ pos = renpy.get_mouse_pos()
    
    frame background Solid("#0a1428") pos pos padding (2,2):
        vbox spacing 1:
            button xsize 180 padding (10,8) background None hover_background Solid("#381010") action [Hide("vn_se_context_menu"), Function(_vn_se_clear_clip, ci, li)]:
                text "Clear Clip" size 12 color "#ff5555"
            frame background Solid("#1a2a48") xsize 180 ysize 1 padding (0,0)
            button xsize 180 padding (10,8) background None hover_background Solid("#1a2a48") action [Hide("vn_se_context_menu"), Function(_vn_se_copy)]:
                text "Copy  (Ctrl+C)" size 12 color "#ffffff"
            button xsize 180 padding (10,8) background None hover_background Solid("#1a2a48") action [Hide("vn_se_context_menu"), Function(_vn_se_paste)]:
                text "Paste  (Ctrl+V)" size 12 color "#ffffff"
            frame background Solid("#1a2a48") xsize 180 ysize 1 padding (0,0)
            ## Convert clip to Ren'Py menu type
            button xsize 180 padding (10,8) background None hover_background Solid("#2a1a48") action [Hide("vn_se_context_menu"), Function(_vn_se_convert_to_menu, ci, li)]:
                hbox spacing 6 yalign 0.5:
                    text "📋" size 12 yalign 0.5
                    text "Make Ren'Py Menu" size 12 color "#cc66ff"
            frame background Solid("#1a2a48") xsize 180 ysize 1 padding (0,0)
            ## Ren'Py Preferences  — opens our own modal so right-click can't escape
            button xsize 180 padding (10,8) background None hover_background Solid("#1a3020") action [Hide("vn_se_context_menu"), Show("vn_prefs_popup")]:
                hbox spacing 6 yalign 0.5:
                    text "⚙️" size 12 yalign 0.5
                    text "Ren'Py Preferences" size 12 color "#66ffaa"
                    text "Ren'Py Preferences" size 12 color "#66ffaa"

init python:
    def _vn_se_incoming_scenes(proj, sc):
        """Return ordered list of scene dicts that link TO this scene via choice/jump events."""
        my_id = sc.get("id", "")
        seen, result = set(), []
        for other in proj.get("scenes", []):
            if other.get("id") == my_id:
                continue
            for ev in other.get("events", []):
                t = ev.get("type", "")
                linked = False
                if t == "choice":
                    if any(opt.get("scene") == my_id for opt in ev.get("opts", [])):
                        linked = True
                elif t == "jump" and ev.get("scene_id") == my_id:
                    linked = True
                if linked and other["id"] not in seen:
                    result.append(other)
                    seen.add(other["id"])
                    break
        return result

    def _vn_se_outgoing_scenes(proj, sc):
        """Return ordered list of scene dicts this scene links to via choice/jump events."""
        seen, result = set(), []
        for ev in sc.get('events', []):
            t = ev.get('type', '')
            if t == 'choice':
                for opt in ev.get('opts', []):
                    sid = opt.get('scene', '')
                    if sid and sid not in seen:
                        tgt = vn_find_scene(proj, sid)
                        if tgt:
                            result.append(tgt)
                            seen.add(sid)
            elif t == 'jump':
                sid = ev.get('scene_id', '')
                if sid and sid not in seen:
                    tgt = vn_find_scene(proj, sid)
                    if tgt:
                        result.append(tgt)
                        seen.add(sid)
        return result



    def _vn_se_asset_swap_cb(t, sc, ev):
        def cb(path):
            if t in ('image', 'bg'):
                ev[t] = path
            elif t in ('music', 'sfx'):
                ev[t] = path
            elif t == 'dialogue' or t == 'character':
                ev['pose'] = path # Just an example if we wanted pose swapping
            vns.save()
            vns.go("scene_editor")
            vns.notify("Asset swapped!", "ok")
        vns.asset_cb = cb

screen vn_se_left_state_panel(sc, ev):
    $ t = ev.get('type', '')
    vbox xfill True yfill True spacing 0:
        ## Header bar
        frame background Solid("#0a1428") xfill True padding (10, 8):
            hbox xfill True spacing 6 yalign 0.5:
                text "📦 ASSET & STATE" size 13 bold True color "#6677aa" yalign 0.5
        frame background Solid("#1a2850") xfill True ysize 1 padding (0, 0)
        
        viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
            frame background None xfill True padding (14, 16):
                if t in ('image', 'bg', 'music', 'sfx'):
                    vbox xfill True spacing 14:
                        text "CURRENT ASSET" style "vn_t_label"
                        $ _cf = ev.get(t, '')
                        text (_cf.split('/')[-1] if _cf else 'None Selected') style "vn_t_dim" size 13
                        if t in ('image', 'bg'):
                            textbutton "Swap Image" style "vn_btn_ghost":
                                action [
                                    SetField(vns, "asset_mode", "images"),
                                    Function(_vn_se_asset_swap_cb, t, sc, ev),
                                    Function(vns.go, "assets"),
                                ]
                        elif t in ('music', 'sfx'):
                            textbutton "Swap Audio" style "vn_btn_ghost":
                                action [
                                    SetField(vns, "asset_mode", "audio"),
                                    Function(_vn_se_asset_swap_cb, t, sc, ev),
                                    Function(vns.go, "assets"),
                                ]
                                
                        frame background Solid("#1a2850") xfill True ysize 1 padding (0,0)
                        text "TIMING" style "vn_t_label"
                        hbox spacing 8 yalign 0.5:
                            text "Duration:" style "vn_t_dim" size 13 yalign 0.5
                            $ _dur = ev.get('duration', 0)
                            if vns.ui.get('_focus') == "ev_dur_input":
                                button style "vn_fr_input" xsize 60 yalign 0.5:
                                    action NullAction()
                                    input id "ev_dur_input" style "vn_input" value DictInputValue(ev, 'duration') size 13 allow "0123456789."
                            else:
                                button style "vn_fr_input" xsize 60 yalign 0.5:
                                    action [SetDict(vns.ui, '_focus', "ev_dur_input"), Function(renpy.set_focus, None, "ev_dur_input")]
                                    text (str(_dur) if _dur else "0") style "vn_input" size 13 color VN_TEXT
                            text "sec" style "vn_t_faint" size 13 yalign 0.5
                        text "Set duration > 0 (e.g. 1.0, 2.5) to make this clip play out in time instead of waiting for a click." style "vn_t_faint" size 11
                        
                        frame background Solid("#1a2850") xfill True ysize 1 padding (0,0)
                        text "ANIMATION TWEEN" style "vn_t_label"
                        hbox spacing 8 yalign 0.5:
                            $ _tween = ev.get('tween', 'linear')
                            textbutton _tween style "vn_btn_ghost":
                                action SetDict(vns.ui, '_tween_picker_ev', ev)
                            text "Controls easing curve" style "vn_t_faint" size 11 yalign 0.5
                else:
                    vbox xfill True spacing 14:
                        text "TIMING" style "vn_t_label"
                        hbox spacing 8 yalign 0.5:
                            text "Duration:" style "vn_t_dim" size 13 yalign 0.5
                            $ _dur = ev.get('duration', 0)
                            if vns.ui.get('_focus') == "ev_dur_input":
                                button style "vn_fr_input" xsize 60 yalign 0.5:
                                    action NullAction()
                                    input id "ev_dur_input" style "vn_input" value DictInputValue(ev, 'duration') size 13 allow "0123456789."
                            else:
                                button style "vn_fr_input" xsize 60 yalign 0.5:
                                    action [SetDict(vns.ui, '_focus', "ev_dur_input"), Function(renpy.set_focus, None, "ev_dur_input")]
                                    text (str(_dur) if _dur else "0") style "vn_input" size 13 color VN_TEXT
                            text "sec" style "vn_t_faint" size 13 yalign 0.5
                        text "Duration makes this event automatically advance." style "vn_t_faint" size 11




## =============================================================================
##  Full-Screen Scene Editor  —  Professional Layout  v7
##
##  fixed root
##  ├─ Zone 1 [yfill, bottom-pad 264px]:  hero preview (fills all)  +  inspector
##  └─ Zone 2+3 [ysize 264, yalign 1.0]:
##       Zone 2 [200px]: timeline rack (NO scrollbar - drag to scroll)
##           Row heights: header=30, TEXT=56, IMAGE=56, AUDIO=56  (+dividers=2)
##       Zone 3  [64px]: bottom control bar
## =============================================================================

screen vn_scene_editor():
    if not vns.scene:
        frame background Solid(VN_BG0) xfill True yfill True:
            vbox xalign 0.5 yalign 0.5 spacing 16:
                text "No scene selected." style "vn_t_dim" xalign 0.5
                textbutton "Back to Scenes" style "vn_btn_ghost":
                    action Function(vns.go, "scenes")
    else:
        $ sc      = vns.scene
        $ vns.ui.setdefault('se_ph', 0)
        $ vns.ui.setdefault('se_active_layer', 0)
        $ vns.ui.setdefault('show_guides', True)
        $ _cur_ev = vn_find_event(sc, vns.event_id) if vns.event_id else None
        $ _eval_bg, _eval_sprites, _eval_fg = _vn_se_eval_state(sc, vns.ui.get('se_ph', 0))
        $ _bg_disp = Transform(_eval_bg, fit="contain", align=(0.5, 0.5)) if _eval_bg else Solid("#060a14")
        $ _evs    = sc.get('events', [])
        $ _ec     = len(_evs)
        ## Slot count can be controlled by the user (+ / - buttons)
        $ _slot_count = max(vns.ui.get('se_slot_count', 15), _ec)
        ## Incoming scenes (scenes that link TO this scene) — shown as portal cols before START
        $ _in_scenes = _vn_se_incoming_scenes(vns.project, sc)
        ## Outgoing scene connections (choice opts + jump targets) shown as portal cols after FINISH
        $ _conn_scenes = _vn_se_outgoing_scenes(vns.project, sc)
        ## START col + events + FINISH col + one portal col per connected scene
        $ _slots  = _ec + 2 + len(_conn_scenes)
        ## Active layer
        $ _active_layer = vns.ui.get('se_active_layer', 0)
        ## Layer colors and names
        $ _layer_count  = vns.ui.get('se_layers', 3)
        $ _layer_colors_list = ["#1a44aa", "#6614cc", "#aa2244", "#14aa66", "#aa6614", "#44aaaa", "#aa5500", "#8855cc", "#228844", "#cc2288"]
        ## Square cells: col_w == row_h so every cell is a perfect square
        $ _t_zoom = vns.ui.get('se_timeline_zoom', 1.0)
        $ _col_w   = int(50 * _t_zoom)
        $ _row_h   = int(50 * _t_zoom)
        $ _hdr_h   = 36
        ## Timeline shows exactly 3 layers at all times
        $ _vis_layers = 3
        ## Exact pixel height of the 3-row grid (no extra padding here)
        $ _grid_h   = _hdr_h + _vis_layers * (_row_h + 1)
        ## Add 16 pixels for the horizontal scrollbar below the grid
        $ _zone2_h  = _grid_h + 16
        $ _btn_bar_h = 64
        $ _zone23_h = _zone2_h + 64
        ## Layer scroll offset (which layer rows are visible, 0-based)
        $ _ls_raw = vns.ui.get('se_lscroll', 0)
        $ _ls     = max(0, min(_ls_raw, _layer_count - _vis_layers))
        $ _ls_max = max(0, _layer_count - _vis_layers)

        ## Cache timeline geometry so the drag handler can use mouse-position drop detection
        $ vns.ui['_tl_col_w']   = _col_w
        $ vns.ui['_tl_row_h']   = _row_h
        $ vns.ui['_tl_hdr_h']   = _hdr_h
        $ vns.ui['_tl_zone2_h'] = _zone2_h
        $ vns.ui['_tl_zone23_h']= _zone23_h
        $ vns.ui['_tl_ls']      = _ls
        $ vns.ui['_tl_vis_layers'] = _vis_layers
        $ vns.ui['_tl_scroll_x'] = int(_vn_se_xadj.value)

        ## Event-type colour table: (cell_bg_dim, block_hi, short_label)
        $ _TC = {
            'dialogue': ('#0e2818', '#1a7a3a', '💬'),
            'narration': ('#0c1638', '#1a40aa', '📝'),
            'choice':    ('#160e30', '#5522bb', '👤'),
            'menu':      ('#1a0e28', '#7a22aa', '📋'),
            'effect':    ('#2a1406', '#b05a12', '✨'),
            'jump':      ('#221c00', '#907800', '➡'),
            'wait':      ('#101418', '#2a3888', '⏳'),
            'music':     ('#0c1a28', '#2266aa', '🎵'),
            'sfx':       ('#280c12', '#aa2244', '🔊'),
            'bg':        ('#1e180c', '#bbaa33', '🌄'),
            'image':     ('#1a0c28', '#9933cc', '🖼'),
            'setvar':    ('#2a220c', '#cc9922', '🔑'),
            'if':        ('#2a0c0c', '#cc3333', '🔀'),
        }

        key "ctrl_K_c"         action Function(_vn_se_copy)
        key "ctrl_K_v"         action Function(_vn_se_paste)
        key "ctrl_K_d"         action Function(_vn_duplicate_event, sc, vns.event_id)
        key "ctrl_K_n"         action [Function(_vn_add_event, sc, vn_new_dialogue)]
        
        if not _vn_is_input_focused():
            key "ctrl_K_DELETE"    action Function(_vn_delete_event, sc)
            key "ctrl_K_BACKSPACE" action Function(_vn_delete_event, sc)
            
            key "ctrl_K_UP"        action Function(_vn_timeline_nudge_clip, 0, -1)
            key "ctrl_K_DOWN"      action Function(_vn_timeline_nudge_clip, 0, 1)
            key "ctrl_K_LEFT"      action Function(_vn_timeline_nudge_clip, -1, 0)
            key "ctrl_K_RIGHT"     action Function(_vn_timeline_nudge_clip, 1, 0)
            
            ## Plain delete - guarded so text inputs can process Backspace/Delete normally
            key "K_DELETE"         action Function(_vn_delete_event, sc)
            key "K_BACKSPACE"      action Function(_vn_delete_event, sc)
        key "K_ESCAPE"   action Function(vns.go, "scenes")
        ## Zoom keyboard shortcuts
        key "K_0"        action [SetVariable("_vn_se_zoom", 1.0), SetVariable("_vn_se_pan_x", 0.0), SetVariable("_vn_se_pan_y", 0.0)]
        key "K_EQUALS"   action SetVariable("_vn_se_zoom", min(4.0, _vn_se_zoom * 1.15))
        key "K_PLUS"     action SetVariable("_vn_se_zoom", min(4.0, _vn_se_zoom * 1.15))
        key "K_MINUS"    action SetVariable("_vn_se_zoom", max(0.25, _vn_se_zoom / 1.15))

        fixed xfill True yfill True:

            ## ================================================================
            ## ZONE 1: Hero preview + Inspector
            ## ================================================================
            frame background (None if vns.ui.get('live_mode', False) else Solid("#040608")) xfill True yfill True padding (0, 0, 0, _zone23_h):
                if not vns.ui.get('live_mode', False):
                    hbox xfill True yfill True spacing 0:

                        ## ── Left Tool Panel (always visible) ────────────────
                        frame background Solid("#030810") xsize 240 yfill True padding (0, 0):
                            vbox xfill True yfill True spacing 0:
                                $ _tp = vns.ui.get('se_tool')
                                if not _tp:
                                    if _cur_ev:
                                        use vn_se_left_state_panel(sc, _cur_ev)
                                    else:
                                        frame background Solid("#0a1428") xfill True padding (10, 8):
                                            hbox xfill True spacing 6 yalign 0.5:
                                                text "🛠️ TOOLS" size 13 bold True color "#667799" yalign 0.5
                                        frame background Solid("#1a2850") xfill True ysize 1 padding (0, 0)
                                        frame background None xfill True padding (14, 16):
                                            vbox xfill True spacing 8 yalign 0.5:
                                                text "No tool armed." size 14 color "#556688" xalign 0.5
                                                text "Click a tool below" size 12 color "#445577" xalign 0.5
                                                text "to place events." size 12 color "#445577" xalign 0.5
                                else:
                                    $ _tp_icons  = {'dialogue':'💬','narration':'📝','choice':'👤','effect':'✨','wait':'⏳','music':'🎵','sfx':'🔊','bg':'🌄','image':'🖼'}
                                    $ _tp_colors = {'dialogue':'#2acc66','narration':'#4a88ee','choice':'#9955ff','effect':'#ee8833','wait':'#4466bb','music':'#4499ff','sfx':'#ffaa22','bg':'#44cc88','image':'#aa66ff'}
                                    $ _tp_icon   = _tp_icons.get(_tp, '?')
                                    $ _tp_color  = _tp_colors.get(_tp, '#aaaaaa')
                                    ## Header bar
                                    frame background Solid("#0a1428") xfill True padding (10, 8):
                                        hbox xfill True spacing 6 yalign 0.5:
                                            text (_tp_icon + " " + _tp.upper()) size 13 bold True color _tp_color yalign 0.5
                                            null xfill True
                                            ## Pin toggle - keeps panel open after file select
                                            $ _tp_pinned = vns.ui.get('se_tool_pin', False)
                                            textbutton ("📌" if _tp_pinned else "📍"):
                                                action ToggleDict(vns.ui, 'se_tool_pin')
                                                padding (5, 3) text_size 13
                                            textbutton "✕ Close":
                                                action [SetDict(vns.ui, 'se_tool', None), SetDict(vns.ui, 'se_tool_pin', False)]
                                                padding (6, 3) text_size 11 text_color "#888" text_hover_color "#fff"
                                    frame background Solid("#1a2850") xfill True ysize 1 padding (0, 0)
                                    ## Content by tool type
                                    if _tp in ('music', 'sfx'):
                                        $ _audio_files = _vn_list_audio()
                                        if not _audio_files:
                                            vbox xalign 0.5 yalign 0.5 spacing 8:
                                                text "🎵" size 36 xalign 0.5
                                                text "No audio files found" size 11 xalign 0.5 color "#334466"
                                                text "Add audio to game/audio/" size 9 xalign 0.5 color "#223355"
                                        else:
                                            viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                                                frame background None xfill True padding (4, 6):
                                                    vbox xfill True spacing 1:
                                                        for _af in _audio_files:
                                                            $ _af_name = _af.split('/')[-1]
                                                            hbox spacing 4 xfill True:
                                                                textbutton "▶":
                                                                    action Function(renpy.music.play, _af, channel="preview")
                                                                    padding (8, 5) text_size 11
                                                                    background Solid("#080c18") hover_background Solid("#2266aa")
                                                                    text_color "#aaeeff" text_hover_color "#ffffff"
                                                                textbutton _af_name:
                                                                    action Function(_vn_apply_music, sc, _af)
                                                                    xfill True padding (8, 5) text_size 11
                                                                    background Solid("#080c18") hover_background Solid("#101c30")
                                                                    text_color "#88aadd" text_hover_color "#aaccff"
                                    elif _tp in ('bg', 'image'):
                                        $ _img_files = _vn_list_images()
                                        if not _img_files:
                                            vbox xalign 0.5 yalign 0.5 spacing 8:
                                                text "🖼" size 36 xalign 0.5
                                                text "No images found" size 11 xalign 0.5 color "#334466"
                                        else:
                                            viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                                                frame background None xfill True padding (4, 6):
                                                    vbox xfill True spacing 1:
                                                        for _imgf in _img_files:
                                                            $ _imgf_name = _imgf.split('/')[-1]
                                                            textbutton _imgf_name:
                                                                action Function(_vn_apply_bg, sc, _imgf)
                                                                xfill True padding (8, 5) text_size 11
                                                                background Solid("#080c18") hover_background Solid("#101c30")
                                                                text_color "#88aacc" text_hover_color "#aaccff"
                                    else:
                                        ## Text-based tools: show arm indicator + instructions
                                        frame background None xfill True padding (14, 16):
                                            vbox xfill True spacing 10:
                                                frame background Solid(_tp_color + "22") xfill True padding (12, 12):
                                                    hbox spacing 10 yalign 0.5:
                                                        text _tp_icon size 30 yalign 0.5
                                                        vbox yalign 0.5 spacing 4:
                                                            text _tp.upper() + " ARMED" size 14 bold True color _tp_color
                                                            hbox spacing 5 yalign 0.5:
                                                                frame background Solid(_tp_color) xsize 7 ysize 7 yalign 0.5 padding (0,0)
                                                                text "Click a cell to place" size 9 color "#6688aa"
                                                frame background Solid(_tp_color + "44") xfill True ysize 1 padding (0, 0)
                                                frame background None xfill True padding (12, 10):
                                                    vbox xfill True spacing 8:
                                                        text "Click any empty timeline cell" size 10 color "#2a4466"
                                                        text "to place a " + _tp.upper() + " event there."
                                                        textbutton "X  Disarm " + _tp.upper():
                                                            action SetDict(vns.ui, 'se_tool', None)
                                                            xfill True padding (10, 7) text_size 11
                                                            background Solid("#200808") hover_background Solid("#380e0e")
                                                            text_color "#cc4444" text_hover_color "#ff7777"

                        ## Hero preview — fills all available left area, no text
                        frame background Solid("#020408") xsize (renpy.config.screen_width - 240 - 280) yfill True padding (0, 0):
                            ## ── VIRTUAL GAME SCREEN (Matches Project Aspect Ratio) ──
                            fixed xfill True yfill True clipping True:
                                $ _pw, _ph = vns.project.get('resolution', [1280, 720])
                                fixed xsize _pw ysize _ph:
                                    at Transform(fit="contain", align=(0.5, 0.5))

                                    ## The "Gray Block" actual game canvas bounds
                                    frame background Solid("#04060b") xfill True yfill True padding (0,0)

                                    ## Layer 1: Panned/Zoomed camera contents
                                    fixed xfill True yfill True:
                                        at transform:
                                            function store._vn_se_cam_fn
                                    
                                        ## Background image scales perfectly into canvas
                                        if _eval_bg:
                                            add Transform(_eval_bg, fit="contain", align=(0.5, 0.5))
                                            
                                        ## Generic Foreground Images
                                        for _tag, _fg_item in _eval_fg.items():
                                            $ _img_path = _fg_item.get('image')
                                            if _img_path:
                                                add Transform(_img_path, align=(0.5, 1.0))
                                        
                                        ## Character sprite
                                        for _char_id, _char_st in _eval_sprites.items():
                                            $ _chr = vn_find_char(vns.project, _char_id)
                                            $ _spr = vn_char_sprite(vns.project, _char_id, _char_st.get('pose', 'neutral'))
                                            $ _sid = _char_st.get('side', 'center')
                                            if _chr and _spr:
                                                add _spr:
                                                    yalign 1.0
                                                    xalign {'left': 0.15, 'center': 0.5, 'right': 0.85}.get(_sid, 0.5)
                                                    zoom 0.55

                                    ## Layer 2: Safe-area guides (un-panned, but locked to canvas)
                                    if vns.ui.get('show_guides', True):
                                        frame background Solid("#ffffff09") xfill True yfill True padding (int(_pw*0.05), int(_ph*0.05)):
                                            frame background Solid("#ffffff14") xfill True yfill True padding (0, 0):
                                                pass

                                    ## Layer 3: Mockup UI (Dialogue / Choices)
                                    $ _ph_ev = _evs[vns.ui.get('se_ph', 0)] if vns.ui.get('se_ph', 0) < _ec else None
                                    if _ph_ev:
                                        $ _pev_type = _ph_ev.get('type')
                                        if _pev_type in ('dialogue', 'narration'):
                                            frame background Solid("#000000cc") xalign 0.5 yalign 0.95 xsize int(_pw*0.8) ysize int(_ph*0.25) padding (int(_pw*0.05), int(_ph*0.05)):
                                                vbox spacing int(_ph*0.01):
                                                    if _pev_type == 'dialogue' and _ph_ev.get('char_id'):
                                                        $ _pchr = vn_find_char(vns.project, _ph_ev['char_id'])
                                                        if _pchr:
                                                            text _pchr.get('display', '') style "vn_t" size int(_ph*0.05) color _pchr.get('color', '#fff') bold True
                                                    $ _is_selected = (_ph_ev['id'] == vns.event_id)
                                                    if _is_selected:
                                                        $ _live_ed = vns.ui.get('_live_ed')
                                                        if not _live_ed or _live_ed.ev.get('id') != _ph_ev['id']:
                                                            if _live_ed:
                                                                $ _live_ed.commit_history()
                                                            $ _live_ed = store.VNTextEditor(_ph_ev, 'text')
                                                            $ vns.ui['_live_ed'] = _live_ed
                                                        use vn_live_texteditor(_live_ed, int(_ph*0.04), "#ffffff")
                                                    else:
                                                        text _ph_ev.get('text', '') style "vn_t" size int(_ph*0.04) color "#ffffff"
                                        elif _pev_type == 'choice':
                                            vbox xalign 0.5 yalign 0.5 spacing int(_ph*0.02) xfill True:
                                                if _ph_ev.get('prompt') and _ph_ev['prompt'] != "(none)":
                                                    text _ph_ev['prompt'] style "vn_t" size int(_ph*0.05) color "#ffffff" xalign 0.5 text_align 0.5
                                                for _opt in _ph_ev.get('opts', []):
                                                    button background Solid("#000000aa") hover_background Solid("#224488aa") xsize int(_pw*0.6) ysize int(_ph*0.08) xalign 0.5:
                                                        text _opt.get('text', '') style "vn_t" size int(_ph*0.04) color "#aaccff" xalign 0.5 yalign 0.5

                                ## Layer 4: Invisible interaction catchers (Fills preview window)
                                fixed xfill True yfill True:
                                                pass

                                ## Layer 3: Invisible interaction catchers (Fills preview window)
                                fixed xfill True yfill True:
                                    add SceneCanvasEvents()




                                ## Reset-view button (top-right) - visible and clickable
                                button xalign 1.0 yalign 0.0 padding (10, 6) xoffset -4 yoffset 4:
                                    action [SetVariable("_vn_se_zoom", 1.0), SetVariable("_vn_se_pan_x", 0.0), SetVariable("_vn_se_pan_y", 0.0)]
                                    background Solid("#0a142899")
                                    hover_background Solid("#1a285099")
                                    hbox spacing 6 yalign 0.5:
                                        text "⊙" size 14 color "#4477bb" yalign 0.5
                                        vbox yalign 0.5 spacing 0:
                                            text "Reset View" size 11 color "#5577aa"
                                            text "Press 0 to reset" size 9 color "#2a3d66"
                                ## HUD: Zoom level (top-left)
                                frame background Solid("#000000bb") xalign 0.0 yalign 0.0 padding (8, 6) xoffset 4 yoffset 4:
                                    hbox spacing 6 yalign 0.5:
                                        frame background Solid("#1a3a6a") padding (4, 2) yalign 0.5:
                                            text "ZOOM" size 8 bold True color "#4a88cc"
                                        text "[_vn_se_zoom:.0%]" size 14 bold True color "#55aadd" yalign 0.5
                                        text "•" size 14 color "#55aadd" yalign 0.5
                                        $ _guides_on = vns.ui.get('show_guides', True)
                                        textbutton ("Guides: ON" if _guides_on else "Guides: OFF"):
                                            action ToggleDict(vns.ui, 'show_guides')
                                            text_size 10 padding (2, 2) text_color "#88aadd" text_hover_color "#ffffff" yalign 0.5
                                ## Pan hint when Space is held
                                if _vn_se_space:
                                    frame background Solid("#00000066") xalign 0.5 yalign 0.5 padding (12, 8):
                                        text "✋ PAN" size 14 bold True color "#aaccff"

                        ## Inspector sidebar
                        frame background Solid("#05080f") xsize 280 yfill True padding (0, 0) xalign 1.0:
                            vbox spacing 0 xfill True yfill True:
                                ## Header with type badge
                                frame background Solid("#0a0f20") xfill True padding (12, 9):
                                    hbox spacing 8 yalign 0.5 xfill True:
                                        if _cur_ev:
                                            $ _hc = {'dialogue':'#2acc66','narration':'#4488ff','choice':'#9955ff','effect':'#ff8833','jump':'#ddcc22','wait':'#4466bb'}.get(_cur_ev.get('type',''), VN_ACC)
                                            frame background Solid(_hc) xsize 4 ysize 16 yalign 0.5
                                            text _cur_ev.get('type','?').upper() style "vn_t" size 12 color _hc yalign 0.5
                                        else:
                                            text "INSPECTOR" style "vn_t_faint" size 11 color "#2a3a5a"
                                        
                                        null xfill True
                                        if __import__("time").time() - vns.project.get('updated', 0) < 1.0:
                                            text "✓ Synced" style "vn_t" size 10 color "#44dd88" yalign 0.5
                                frame background Solid("#111c38") xfill True ysize 1 padding (0, 0)
                                ## Scene BG controls
                                frame background Solid("#060a18") xfill True padding (12, 10):
                                    vbox spacing 8 xfill True:
                                        text "SCENE" style "vn_t_label"
                                        hbox spacing 6:
                                            textbutton "Set Background" style "vn_btn_ghost":
                                                action Show("vn_bg_gallery_modal", sc=sc)
                                            if sc.get('bg'):
                                                textbutton "Clear" style "vn_btn_ghost":
                                                    action [SetDict(sc, 'bg', None), Function(vns.save)]
                                frame background Solid("#111c38") xfill True ysize 1 padding (0, 0)
                                ## Event inspector — layer-aware
                                if _cur_ev:
                                    ## For L2+, inspect the layer data dict instead of the event root
                                    $ _insp_layer = vns.ui.get('se_active_layer', 0)
                                    $ _insp_ev = _cur_ev
                                    if _insp_layer > 0:
                                        $ _layer_data = _cur_ev.get('layer' + str(_insp_layer))
                                        if _layer_data:
                                            $ _insp_ev = _layer_data
                                    $ _insp_t = _insp_ev.get('type', '')
                                    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                                        frame background None xfill True padding (14, 14):
                                            vbox spacing 14 xfill True:
                                                use vn_event_inspector(_insp_ev, sc)
                                else:
                                    vbox xalign 0.5 yalign 0.5 spacing 8:
                                        text "No event selected" style "vn_t_faint" size 12 xalign 0.5
                                        text "Click a block in the" style "vn_t_faint" size 11 xalign 0.5
                                        text "timeline to edit it." style "vn_t_faint" size 11 xalign 0.5

            ## ================================================================
            ## ZONE 2 + 3: Timeline + Control bar  (dynamic height)
            ## ================================================================
            vbox spacing 0 xfill True ysize _zone23_h yalign 1.0:

                ## ── Zone 2: Timeline rack ───────────────────────────────────
                frame background Solid("#040810") xfill True ysize _zone2_h padding (0, 0):
                    hbox spacing 0 xfill True ysize _zone2_h:

                        ## ── Dynamic layer label column (left) ─────────────────
                        $ _layer_names  = ["LAYER " + str(i+1) for i in range(_layer_count)]
                        frame background Solid("#08101e") xsize 110 ysize _zone2_h padding (0, 0):
                            vbox spacing 0 xsize 110:
                                ## Header: timeline label + optional scroll arrows
                                frame background Solid("#070e1c") xsize 110 ysize _hdr_h padding (8, 0):
                                    hbox xfill True yalign 0.5 spacing 4:
                                        frame background Solid("#1a3888") xsize 3 yfill True yalign 0.5 padding (0,4)
                                        vbox yalign 0.5 spacing 1:
                                            text "TIMELINE" style "vn_t_faint" size 8 bold True color "#1e3a78"
                                            if _layer_count > _vis_layers:
                                                text (str(_ls + 1) + "-" + str(min(_ls + _vis_layers, _layer_count)) + " / " + str(_layer_count)) style "vn_t_faint" size 7 color "#253a55"
                                        null xfill True
                                        if _layer_count > _vis_layers:
                                            vbox spacing 1 yalign 0.5:
                                                textbutton "▲" yalign 0.5:
                                                    action SetDict(vns.ui, 'se_lscroll', max(0, _ls - 1))
                                                    padding (4, 1) text_size 8 text_color "#4466aa" text_hover_color "#88aaff"
                                                textbutton "▼" yalign 0.5:
                                                    action SetDict(vns.ui, 'se_lscroll', min(_ls_max, _ls + 1))
                                                    padding (4, 1) text_size 8 text_color "#4466aa" text_hover_color "#88aaff"
                                                textbutton "▲" yalign 0.5:
                                                    action SetDict(vns.ui, 'se_lscroll', max(0, _ls - 1))
                                                    padding (5, 1) text_size 9 text_color "#6688bb" text_hover_color "#aaccff"
                                                textbutton "▼" yalign 0.5:
                                                    action SetDict(vns.ui, 'se_lscroll', min(_ls_max, _ls + 1))
                                                    padding (5, 1) text_size 9 text_color "#6688bb" text_hover_color "#aaccff"
                                frame background Solid("#0d1830") xsize 110 ysize 1 padding (0, 0)
                                ## Layer label rows
                                for _li in range(_ls, min(_ls + _vis_layers, _layer_count)):
                                    $ _lcol  = _layer_colors_list[_li % len(_layer_colors_list)]
                                    $ _l_armed = (_active_layer == _li)
                                    ## Layer icon generic
                                    $ _l_icon = "☰"
                                    button xsize 110 ysize _row_h padding (0, 0):
                                        background Solid("#111e36" if _l_armed else "#080e1c")
                                        hover_background Solid("#1a2a48")
                                        action SetDict(vns.ui, 'se_active_layer', _li)
                                        fixed xfill True yfill True:
                                            ## Armed left glow stripe
                                            if _l_armed:
                                                frame background Solid(_lcol + "cc") xsize 3 yfill True xalign 0.0 padding (0,0)
                                                frame background Solid(_lcol + "18") xfill True yfill True padding (0,0)
                                            frame background None xfill True yfill True padding (10, 0):
                                                hbox xfill True yfill True yalign 0.5 spacing 6:
                                                    frame background Solid(_lcol + ("cc" if _l_armed else "66")) xsize 3 ysize 20 yalign 0.5 padding (0,0)
                                                    vbox yalign 0.5 spacing 2:
                                                        text ("L" + str(_li+1)) style "vn_t" size 14 bold True color ("#ddeeff" if _l_armed else "#5577aa")
                                                        text _l_icon size 12 xalign 0.0
                                                        if _l_armed:
                                                            text "ARMED" style "vn_t_faint" size 7 bold True color _lcol
                                    frame background Solid("#0d1830") xsize 110 ysize 1 padding (0, 0)

                        frame background Solid("#111c38") xsize 1 ysize _zone2_h padding (0, 0)

                        ## Incoming scene portal columns (fixed, before scroll area)
                        $ _in_panel_w = len(_in_scenes) * (_col_w + 1)
                        for _in_sc in _in_scenes:
                            vbox spacing 0 xsize _col_w ysize _zone2_h:
                                ## Header strip
                                frame background Solid("#0a1022") xsize _col_w ysize _hdr_h padding (0, 0):
                                    vbox xalign 0.5 yalign 0.5 spacing 1:
                                        text "←" style "vn_t" size 10 bold True xalign 0.5 color "#4488ee"
                                frame background Solid("#0d1830") xsize _col_w ysize 1 padding (0, 0)
                                ## Clickable portal body
                                $ _in_flag_h = min(_vis_layers, _layer_count - _ls) * (_row_h + 1)
                                button xsize _col_w ysize _in_flag_h padding (0, 2):
                                    background Solid("#070d1a")
                                    hover_background Solid("#0e1e3a")
                                    action [SetField(vns, "scene_id", _in_sc["id"]), Function(vns.go, "scene_editor")]
                                    fixed xfill True yfill True:
                                        vbox xalign 0.5 yalign 0.5 spacing 2:
                                            text "⬅" size 20 xalign 0.5 color "#4488ee"
                                            text (_in_sc.get("label", "?")[:10]) size 8 xalign 0.5 color "#4488ee" text_align 0.5
                                frame background Solid("#111c38") xsize _col_w ysize 1 padding (0, 0)
                        if _in_scenes:
                            frame background Solid("#111c38") xsize 1 ysize _zone2_h padding (0, 0)

                        ## Scrollable click-columns: each column is _col_w wide, cells are _col_w x _row_h (square)
                        $ _vp_w = renpy.config.screen_width - 110 - 1 - _in_panel_w - (24 if _layer_count > _vis_layers else 0)
                        viewport id "vn_se_vp" xsize _vp_w ysize _zone2_h mousewheel "horizontal" scrollbars "horizontal" style_prefix "vn_hscroll" xadjustment _vn_se_xadj:
                            fixed xfit True ysize _zone2_h:

                                ## Calculate visible columns for culling (Clamped to prevent velocity explosion bugs)
                                $ _scroll_x = max(0, min(int(_vn_se_xadj.value), (_slots * (_col_w + 1))))
                                $ _first_ci = max(0, min(_slots, int(_scroll_x // (_col_w + 1)) - 1))
                                $ _last_ci  = min(_slots, _first_ci + int(_vp_w // (_col_w + 1)) + 3)

                                ## PASS 1: The empty grid and notches
                                hbox spacing 0 ysize _grid_h:
                                    if _first_ci > 0:
                                        null xsize (_first_ci * (_col_w + 1))
                                    
                                    for _ci in range(_first_ci, _last_ci):
                                        $ _cev_idx = _ci - 1
                                        $ _cev   = _evs[_cev_idx] if _cev_idx >= 0 and _cev_idx < _ec else None
                                        $ _csel  = bool(_cev) and vns.event_id == _cev['id']
                                        $ _is_ph = (vns.ui.get('se_ph', 0) + 1) == _ci
                                        $ _tc    = _TC.get(_cev.get('type', '') if _cev else '', ('#0a0e16', '#1e2840', '...'))
                                        $ _tc_dim, _tc_hi, _tc_lbl = _tc
                                        $ _is_conn_col = _ci > _ec + 1
                                        $ _conn_col_sc = _conn_scenes[_ci - (_ec + 2)] if _is_conn_col and (_ci - (_ec + 2)) < len(_conn_scenes) else None

                                        vbox spacing 0 xsize _col_w ysize _grid_h:
                                            ## ── Click number header ──
                                            button xsize _col_w ysize _hdr_h padding (0, 0):
                                                background Solid("#38180a" if _is_ph else ("#101830" if _csel else "#07090f"))
                                                hover_background Solid("#4a2010" if _is_ph else "#18224a")
                                                action Function(_vn_se_move_ph, _ci, _cev)
                                                fixed xfill True yfill True:
                                                    if _is_ph:
                                                        frame background Solid("#ee1100") xsize 2 yfill True xalign 0.5
                                                    vbox xalign 0.5 yalign 0.5 spacing 1:
                                                        $ _col_title = "START" if _ci == 0 else ("FINISH" if _ci == _ec + 1 else ("→" if _is_conn_col else str(_ci)))
                                                        $ _col_size = 8 if _is_conn_col else (11 if _col_title in ("START", "FINISH") else 13)
                                                        $ _col_color = "#2db354" if _is_conn_col else ("#ff6644" if _is_ph else ("#7788cc" if _csel else "#2e3d6a"))
                                                        text _col_title style "vn_t" size _col_size bold True xalign 0.5 color _col_color
                                                        if _cev and not _is_conn_col:
                                                            text _tc_lbl style "vn_t_faint" size 8 bold True xalign 0.5 color ("#ffaa88" if _is_ph else "#445577")

                                            ## ── Layer notches: only show visible scroll window ──
                                            if _ci == _ec + 1:
                                                $ _flag_h = min(_vis_layers, _layer_count - _ls) * (_row_h + 1)
                                                button xsize _col_w ysize _flag_h padding (0, 0):
                                                    background Solid("#7a3203")
                                                    hover_foreground Solid("#ffffff14")
                                                    action If(
                                                        vns.ui.get('se_tool'),
                                                        Function(_vn_apply_tool_to_click, sc, _ci, _active_layer),
                                                        Function(_vn_remove_last_click, sc))
                                                    fixed xfill True yfill True:
                                                        text "🏁" size 32 align (0.5, 0.5)
                                            elif _ci == 0:
                                                $ _flag_h = min(_vis_layers, _layer_count - _ls) * (_row_h + 1)
                                                button xsize _col_w ysize _flag_h padding (0, 0):
                                                    background Solid("#16284a")
                                                    hover_foreground Solid("#ffffff14")
                                                    action Function(_vn_insert_click, sc, 1)
                                                    fixed xfill True yfill True:
                                                        text "🎌" size 32 align (0.5, 0.5)
                                            elif _is_conn_col and _conn_col_sc:
                                                ## ── Portal column: click to jump to connected scene ──
                                                $ _flag_h = min(_vis_layers, _layer_count - _ls) * (_row_h + 1)
                                                button xsize _col_w ysize _flag_h padding (0, 2):
                                                    background Solid("#081a08")
                                                    hover_background Solid("#122e14")
                                                    action [SetField(vns, "scene_id", _conn_col_sc['id']), Function(vns.go, "scene_editor")]
                                                    fixed xfill True yfill True:
                                                        vbox xalign 0.5 yalign 0.5 spacing 2:
                                                            text "➡" size 20 xalign 0.5 color "#2db354"
                                                            text (_conn_col_sc.get('label', '?')[:10]) size 8 xalign 0.5 color "#2db354" text_align 0.5
                                            else:
                                                for _li in range(_ls, min(_ls + _vis_layers, _layer_count)):
                                                    $ _li_armed = (_active_layer == _li)
                                                    $ _li_col   = _layer_colors_list[_li % len(_layer_colors_list)]
                                                    $ _notch_bg = "#0a1222" if _li == 0 else ("#0e0904" if _li == 1 else ("#0c0606" if _li == 2 else "#080810"))
    
                                                    drag:
                                                        drag_name "notch_{}_{}".format(_ci, _li)
                                                        draggable False
                                                        droppable True
                                                        xfill True
                                                        ysize _row_h
    
                                                        button xsize _col_w ysize _row_h padding (0, 0):
                                                            background Solid(_notch_bg)
                                                            hover_foreground Solid("#ffffff0c")
                                                            action If(
                                                                vns.ui.get('se_tool'),
                                                                Function(_vn_apply_tool_to_click, sc, _ci, _li),
                                                                Function(_vn_se_select_cell, _ci, _cev, _li))
                                                            fixed xfill True yfill True:
                                                                    if _ci % 2 == 0:
                                                                        frame background Solid("#ffffff03") xfill True yfill True padding (0, 0)
                                                                    if (_ci, _li) in vns.ui.get('se_multi', []):
                                                                        frame background Solid("#ff110022") xfill True yfill True padding (0, 0)
                                                                        frame background Solid("#ff1100") xsize 3 yfill True xalign 0.5
                                                                    elif _is_ph:
                                                                        frame background Solid("#ff110014") xfill True yfill True padding (0, 0)
                                                                        frame background Solid("#ee1100") xsize 2 yfill True xalign 0.5
                                                                    if _li_armed:
                                                                        frame background Solid(_li_col + "22") xfill True yfill True padding (0, 0)
                                                                        frame background Solid(_li_col) xsize 3 yfill True xalign 0.0
    
                                                    ## Horizontal grid line
                                                    frame background Solid("#1a2850") xsize _col_w ysize 1 padding (0, 0)

                                        ## Vertical grid line between columns
                                        frame background Solid("#1a2850") xsize 1 ysize _grid_h padding (0, 0)

                                    if _last_ci < _slots:
                                        null xsize ((_slots - _last_ci) * (_col_w + 1))

                                ## PASS 2: The Floating Colored Event Clips
                                for _ci in range(_first_ci, _last_ci):
                                    $ _cev_idx_p2 = _ci - 1
                                    if _cev_idx_p2 >= 0 and _cev_idx_p2 < _ec:
                                        $ _cev = _evs[_cev_idx_p2]
                                        $ _ctyp = _cev.get('type', '')
                                        $ _tc = _TC.get(_ctyp, ('#0a0e16', '#1e2840', '...'))
                                        $ _tc_dim, _tc_hi, _tc_lbl = _tc
                                        $ _l0_active = bool(_cev.get('type'))

                                        ## ── Character color for dialogue tinting ──
                                        $ _char_col = None
                                        $ _char_label = None
                                        if _ctyp == 'dialogue' and _cev.get('char_id'):
                                            $ _cchar = vn_find_char(vns.project, _cev['char_id'])
                                            if _cchar:
                                                $ _char_col = _cchar.get('color', None)
                                                $ _char_label = (_cchar.get('display') or '')[:4].upper()
                                        
                                        for _li in range(_ls, min(_ls + _vis_layers, _layer_count)):
                                            $ _ldata = None
                                            if _li == 0: 
                                                $ _ldata = _cev if _l0_active else None
                                            else:
                                                $ _ldata = _cev.get('layer' + str(_li))
                                            
                                            ## ── Empty slot hint on L1 ──
                                            if _li == 0 and not _ldata:
                                                fixed xsize _col_w ysize _row_h xpos (_ci * (_col_w + 1)) ypos (_hdr_h):
                                                    text "···" style "vn_t" size 11 color "#1e2a44" xalign 0.5 yalign 0.5
                                            
                                            if _ldata:
                                                $ _ltype = _ldata.get('type', '')
                                                $ _tc    = _TC.get(_ltype, ('#080810', _layer_colors_list[_li % len(_layer_colors_list)], 'DATA'))
                                                $ _li_bg, _li_hi, _li_lbl = _tc

                                                ## ── Apply character tint for dialogue on L1 ──
                                                $ _tint_hi = _li_hi
                                                if _li == 0 and _char_col:
                                                    $ _tint_hi = _char_col + "88"

                                                drag:
                                                    drag_name "clip_{}_{}".format(_ci, _li)
                                                    draggable True
                                                    droppable True
                                                    dragged _vn_timeline_clip_dragged
                                                    clicked If(
                                                        vns.ui.get('se_tool'),
                                                        Function(_vn_apply_tool_to_click, sc, _ci, _li),
                                                        Function(_vn_se_select_cell, _ci, _cev, _li))
                                                    alternate Show("vn_se_context_menu", ci=_ci, li=_li)
                                                    hovered SetDict(vns.ui, 'tl_hover_clip', f"{_ci}_{_li}")
                                                    unhovered SetDict(vns.ui, 'tl_hover_clip', None)
                                                    xpos (_ci * (_col_w + 1))
                                                    ypos (_hdr_h + (_li - _ls) * (_row_h + 1))
                                                    
                                                    frame xsize _col_w ysize _row_h padding (0,0):
                                                        background Solid(_li_bg)
                                                        foreground (Solid("#ffffff11") if vns.ui.get('tl_hover_clip') == f"{_ci}_{_li}" else Null())
                                                        
                                                        # Content block
                                                        $ _cprev = ""
                                                        if _ldata.get("text"):
                                                            $ _cprev = _ldata["text"][:7].strip()
                                                        elif _ldata.get("bg"):
                                                            $ _cprev = _ldata["bg"].split("/")[-1][:7]
                                                        elif _ldata.get("music"):
                                                            $ _cprev = _ldata["music"].split("/")[-1][:7]
                                                        elif _ldata.get("image"):
                                                            $ _cprev = _ldata["image"].split("/")[-1][:7]
                                                        elif _ldata.get("sfx"):
                                                            $ _cprev = _ldata["sfx"].split("/")[-1][:7]
                                                        elif _ltype in ('image', 'bg', 'music', 'sfx'):
                                                            $ _cprev = "none"
                                                            
                                                        frame background Solid(_tint_hi) xfill True yfill True padding (0,0):
                                                            ## Left color stripe for character identity
                                                            if _li == 0 and _char_col:
                                                                frame background Solid(_char_col) xsize 3 yfill True xalign 0.0 padding (0,0)
                                                            viewport xsize _col_w ysize _row_h clipping True:
                                                                ## Emoji center
                                                                text _li_lbl style "vn_t" size 20 bold True color "#ffffff" xalign 0.5 yalign 0.5
                                                                ## Speaker name tag — top of block
                                                                if _li == 0 and _char_label:
                                                                    text _char_label style "vn_t" size 8 bold True color (_char_col if _char_col else "#aaccff") xalign 0.5 yalign 0.0
                                                                elif _li == 0 and _ctyp == 'dialogue':
                                                                    text "NAR" style "vn_t" size 8 bold True color "#8899bb" xalign 0.5 yalign 0.0
                                                                ## Preview text pinned to bottom
                                                                if _cprev:
                                                                    text _cprev style "vn_t" size 9 color "#ccddff" xalign 0.5 yalign 1.0


                        ## ── Layer vertical scrollbar (Right side) ──
                        if _layer_count > _vis_layers:
                            frame background Solid("#0a1222") xsize 24 yfill True padding (5, 5, 5, 20):
                                vbar value DictValue(vns.ui, 'se_lscroll', _ls_max, step=1, force_step=True) style "vn_layer_vscroll"


                ## Combined Bottom Bar: [Scene nav | 9 tools | LCD + Playback + L/C]
                frame background Solid("#020408") xfill True ysize 64 padding (0, 0):
                    frame background Solid("#0d1830") xfill True ysize 1 padding (0,0) yalign 0.0
                    if _vn_se_playing:
                        timer 1.8 repeat True action Function(_vn_se_play_step)
                    hbox xfill True yfill True spacing 0:

                        ## Graph back button
                        frame background Solid("#040610") xsize 80 yfill True padding (0, 0):
                            button xfill True yfill True padding (0, 0):
                                action Function(vns.go, "graph")
                                background Solid("#06090f")
                                hover_background Solid("#0d1428")
                                fixed xfill True yfill True:
                                    frame background Solid(VN_TEAL) xfill True ysize 2 yalign 0.0 padding (0,0)
                                    vbox xalign 0.5 yalign 0.5 spacing 2:
                                        text "\U0001f5fa" size 20 xalign 0.5 color VN_TEAL
                                        text "GRAPH" size 9 bold True xalign 0.5 color VN_TEAL
                                        
                        frame background Solid("#0d1830") xsize 1 yfill True padding (0, 0)

                        frame background Solid("06090f") xsize 240 yfill True padding (0, 0):
                            hbox yfill True spacing 0:
                                frame background Solid(VN_ACC + "99") xsize 3 yfill True padding (0,0)
                                frame background None xfill True yfill True padding (10, 0):
                                    vbox xfill True yalign 0.5 spacing 3:
                                        $ _back_label = "Scenes"
                                        $ _cf = getattr(store.vng, 'current_folder', None)
                                        if _cf:
                                            $ _folder = next((f for f in vns.project.get('folders', []) if f['id'] == _cf), None)
                                            if _folder:
                                                $ _back_label = _folder.get('label', 'Folder')

                                        textbutton "\u25c4 " + _back_label yalign 0.5:
                                            action Function(vns.go, "scenes")
                                            padding (0, 0) text_size 10 text_color "#3a5577" text_hover_color "#6699cc"
                                        hbox spacing 4 yalign 0.5 xfill True:
                                            text sc.get('label', 'Scene') size 13 bold True color "#6699cc" yalign 0.5
                                            null xfill True
                                            textbutton "\u27b2":
                                                action Function(vns.history.undo) 
                                                text_size 14 text_color "#4a6688" text_hover_color "#ffcc33" padding (4, 0)
                                            textbutton "\u27b3":
                                                action Function(vns.history.redo) 
                                                text_size 14 text_color "#4a6688" text_hover_color "#ffcc33" padding (4, 0)

                        frame background Solid("#0d1830") xsize 1 yfill True padding (0, 0)

                        ## DIALOGUE — draggable tool
                        $ _ta = vns.ui.get('se_tool') == 'dialogue'
                        fixed xsize 150 yfill True:
                            button xsize 150 yfill True padding (0, 0):
                                action Function(_vn_set_tool, 'dialogue')
                                background Solid("#0b1f36" if _ta else "#05090f")
                                hover_background Solid("#0f2a44")
                                fixed xfill True yfill True:
                                    frame background Solid("#1e8844" if _ta else "#0a2218") xfill True ysize 2 yalign 0.0 padding (0,0)
                                    if _ta:
                                        frame background Solid("#2aff8810") xfill True yfill True padding (0,0)
                                    hbox xalign 0.5 yalign 0.5 spacing 8:
                                        ## Emoji placeholder (real draggable is the floating overlay)
                                        frame xsize 36 ysize 36 yalign 0.5 padding (0,0) background None:
                                            text "💬" size 26 align (0.5, 0.5) color ("#2aff88" if _ta else "#aaffcc")
                                        text "DIALOGUE" size 15 bold True yalign 0.5 color ("#2aff88" if _ta else "#55cc88")

                        ## MUSIC — draggable tool
                        $ _ta = vns.ui.get('se_tool') == 'music'
                        fixed xsize 150 yfill True:
                            button xsize 150 yfill True padding (0, 0):
                                action Function(_vn_set_tool, 'music')
                                background Solid("#0b1f36" if _ta else "#05090f")
                                hover_background Solid("#0f2a44")
                                fixed xfill True yfill True:
                                    frame background Solid("#2266aa" if _ta else "#0a2218") xfill True ysize 2 yalign 0.0 padding (0,0)
                                    if _ta:
                                        frame background Solid("#2266aa10") xfill True yfill True padding (0,0)
                                    hbox xalign 0.5 yalign 0.5 spacing 8:
                                        frame xsize 36 ysize 36 yalign 0.5 padding (0,0) background None:
                                            text "🎵" size 26 align (0.5, 0.5) color ("#44ccff" if _ta else "#99eeff")
                                        text "MUSIC" size 15 bold True yalign 0.5 color ("#44ccff" if _ta else "#4499cc")

                        ## IMAGE — draggable tool
                        $ _ta = vns.ui.get('se_tool') == 'image'
                        fixed xsize 150 yfill True:
                            button xsize 150 yfill True padding (0, 0):
                                action Function(_vn_set_tool, 'image')
                                background Solid("#0b1f36" if _ta else "#05090f")
                                hover_background Solid("#0f2a44")
                                fixed xfill True yfill True:
                                    frame background Solid("#9933cc" if _ta else "#0a2218") xfill True ysize 2 yalign 0.0 padding (0,0)
                                    if _ta:
                                        frame background Solid("#9933cc10") xfill True yfill True padding (0,0)
                                    hbox xalign 0.5 yalign 0.5 spacing 8:
                                        frame xsize 36 ysize 36 yalign 0.5 padding (0,0) background None:
                                            text "🖼" size 26 align (0.5, 0.5) color ("#bb88ff" if _ta else "#cc99ff")
                                        text "IMAGE" size 15 bold True yalign 0.5 color ("#bb88ff" if _ta else "#9966cc")

                        ## SETVAR — draggable tool
                        $ _ta = vns.ui.get('se_tool') == 'setvar'
                        fixed xsize 150 yfill True:
                            button xsize 150 yfill True padding (0, 0):
                                action Function(_vn_set_tool, 'setvar')
                                background Solid("#0b1f36" if _ta else "#05090f")
                                hover_background Solid("#0f2a44")
                                fixed xfill True yfill True:
                                    frame background Solid("#cc9922" if _ta else "#0a2218") xfill True ysize 2 yalign 0.0 padding (0,0)
                                    if _ta:
                                        frame background Solid("#cc992210") xfill True yfill True padding (0,0)
                                    hbox xalign 0.5 yalign 0.5 spacing 8:
                                        frame xsize 36 ysize 36 yalign 0.5 padding (0,0) background None:
                                            text "🔑" size 26 align (0.5, 0.5) color ("#ffcc44" if _ta else "#ccaa55")
                                        text "KEY" size 15 bold True yalign 0.5 color ("#ffcc44" if _ta else "#cc9922")


                        ## CHOICE — draggable tool
                        $ _ta = vns.ui.get('se_tool') == 'choice'
                        fixed xsize 140 yfill True:
                            button xsize 140 yfill True padding (0, 0):
                                action Function(_vn_set_tool, 'choice')
                                background Solid("#0b1f36" if _ta else "#05090f")
                                hover_background Solid("#0f2a44")
                                fixed xfill True yfill True:
                                    frame background Solid("#9955ff" if _ta else "#0a2218") xfill True ysize 2 yalign 0.0 padding (0,0)
                                    if _ta:
                                        frame background Solid("#9955ff10") xfill True yfill True padding (0,0)
                                    hbox xalign 0.5 yalign 0.5 spacing 8:
                                        frame xsize 36 ysize 36 yalign 0.5 padding (0,0) background None:
                                            text "❓" size 26 align (0.5, 0.5) color ("#aa77ff" if _ta else "#8844cc")
                                        text "CHOICE" size 14 bold True yalign 0.5 color ("#aa77ff" if _ta else "#9955ff")

                        frame background Solid("#0d1830") xsize 1 yfill True padding (0, 0)


                        ## RIGHT: LCD + Playback + L/C controls
                        frame background Solid("#04060c") xfill True yfill True padding (8, 0):
                            hbox xfill True spacing 6 yalign 0.5:
                                frame background Solid("#040810") padding (8, 4) yalign 0.5:
                                    vbox spacing 0 yalign 0.5:
                                        text "CLICK" size 6 bold True color "#1e3060" xalign 0.5
                                        $ _ph_disp = vns.ui.get('se_ph', 0) + 1
                                        hbox spacing 4 yalign 0.5 xalign 0.5:
                                            text "[_ph_disp]" size 18 bold True color "#5599ff" yalign 0.5
                                            text "/[_ec]" size 11 color "#2a4488" yalign 0.5
                                frame background Solid("#0d1830") xsize 1 ysize 36 yalign 0.5 padding (0, 0)
                                $ _ph_cur  = vns.ui.get('se_ph', 0)
                                $ _ph_back = max(0, _ph_cur - 1)
                                $ _ph_fwd  = min(max(0, _ec - 1), _ph_cur + 1)
                                $ _ph_end  = max(0, _ec - 1)
                                hbox spacing 1 yalign 0.5:
                                    textbutton "\u23ee" yalign 0.5:
                                        action [Function(_vn_se_move_ph, 1, _evs[0] if _evs else None), SetVariable("_vn_se_playing", False)]
                                        padding (5, 4) text_size 13
                                        background Solid("#06090f") hover_background Solid("#0d1428")
                                        text_color "#3a5577" text_hover_color "#7799cc"
                                    textbutton "\u23ea" yalign 0.5:
                                        action Function(_vn_se_move_ph, _ph_back + 1, _evs[_ph_back] if _ph_back < _ec else None)
                                        padding (5, 4) text_size 13
                                        background Solid("#06090f") hover_background Solid("#0d1428")
                                        text_color "#3a5577" text_hover_color "#7799cc"
                                    if not _vn_se_playing:
                                        textbutton "\u25b6" yalign 0.5:
                                            action SetVariable("_vn_se_playing", True)
                                            padding (10, 6) text_size 15
                                            background Solid("#0a2814") hover_background Solid("#143a1e")
                                            text_color "#2ecc71" text_hover_color "#44ff88"
                                    else:
                                        textbutton "\u23f8" yalign 0.5:
                                            action SetVariable("_vn_se_playing", False)
                                            padding (10, 6) text_size 15
                                            background Solid("#2a1c04") hover_background Solid("#3e2a08")
                                            text_color "#f39c12" text_hover_color "#ffcc44"
                                    textbutton "\u23e9" yalign 0.5:
                                        action Function(_vn_se_move_ph, _ph_fwd + 1, _evs[_ph_fwd] if _ph_fwd < _ec else None)
                                        padding (5, 4) text_size 13
                                        background Solid("#06090f") hover_background Solid("#0d1428")
                                        text_color "#3a5577" text_hover_color "#7799cc"
                                    textbutton "\u23ed" yalign 0.5:
                                        action [Function(_vn_se_move_ph, _ph_end + 1, _evs[_ph_end] if _ph_end < _ec else None), SetVariable("_vn_se_playing", False)]
                                        padding (5, 4) text_size 13
                                        background Solid("#06090f") hover_background Solid("#0d1428")
                                        text_color "#3a5577" text_hover_color "#7799cc"
                                frame background Solid("#0d1830") xsize 1 ysize 36 yalign 0.5 padding (0, 0)
                                ## ── Play from Here ──────────────────────────────
                                $ _ph_play = vns.ui.get('se_ph', 0)
                                null xfill True
                                hbox spacing 6 yalign 0.5:
                                    button yalign 0.5 padding (14, 0):
                                        action Function(_vns_compile_scene_from, sc['id'], _ph_play)
                                        background Solid("#0a1e06")
                                        hover_background Solid("#16370c")
                                        fixed xfit True yfill True:
                                            frame background Solid("#44ff66") xfill True ysize 2 yalign 0.0 padding (0,0)
                                            hbox spacing 6 xalign 0.5 yalign 0.5:
                                                text "▶" size 16 color "#44ff66" yalign 0.5
                                                vbox yalign 0.5 spacing 0:
                                                    text "PLAY" size 11 bold True color "#33ff44"
                                                    if _ph_play > 0:
                                                        text "from [_ph_play]" size 8 color "#227722"
                                                    else:
                                                        text "from start" size 8 color "#227722"
                                    frame background Solid("#0d1830") xsize 1 ysize 36 yalign 0.5 padding (0, 0)
                                    frame background Solid("#0d1830") xsize 1 ysize 36 yalign 0.5 padding (0, 0)
                                    vbox yalign 0.5 spacing 1:
                                        text "LAYERS" size 6 bold True xalign 0.5 color "#1e3a78"
                                        hbox spacing 2 yalign 0.5:
                                            textbutton "\u2212":
                                                action If(_layer_count > 1, [SetDict(vns.ui, 'se_layers', _layer_count - 1), SetDict(vns.ui, 'se_lscroll', max(0, _ls - 1))])
                                                padding (7, 3) text_size 12 text_color "#cc4444" text_hover_color "#ff8888"
                                                background Solid("#140808") hover_background Solid("#220e0e")
                                            frame background Solid("#0a1020") padding (5, 2) yalign 0.5:
                                                text str(_layer_count) size 12 bold True color "#4466bb" xalign 0.5
                                            textbutton "+":
                                                action If(_layer_count < 10, [SetDict(vns.ui, 'se_layers', _layer_count + 1), SetDict(vns.ui, 'se_lscroll', _layer_count)])
                                                padding (7, 3) text_size 12 text_color "#44cc44" text_hover_color "#88ff88"
                                                background Solid("#081408") hover_background Solid("#0e2010")
                                    vbox yalign 0.5 spacing 1:
                                        text "ZOOM" size 6 bold True xalign 0.5 color "#1e3a78"
                                        hbox spacing 2 yalign 0.5:
                                            textbutton "\u2212":
                                                action SetDict(vns.ui, 'se_timeline_zoom', max(0.5, _t_zoom / 1.15))
                                                padding (7, 3) text_size 12 text_color "#44aacc" text_hover_color "#88ccff"
                                                background Solid("#081014") hover_background Solid("#0e1a22")
                                            frame background Solid("#0a1020") padding (5, 2) yalign 0.5:
                                                text "[_t_zoom:.1f]x" size 12 bold True color "#4488ff" xalign 0.5
                                            textbutton "+":
                                                action SetDict(vns.ui, 'se_timeline_zoom', min(2.0, _t_zoom * 1.15))
                                                padding (7, 3) text_size 12 text_color "#44aacc" text_hover_color "#88ccff"
                                                background Solid("#081014") hover_background Solid("#0e1a22")
                                    vbox yalign 0.5 spacing 1:
                                        text "CLICKS" size 6 bold True xalign 0.5 color "#1e3060"
                                        hbox spacing 2 yalign 0.5:
                                            textbutton "\u2212":
                                                action SetDict(vns.ui, 'se_slot_count', max(_ec, _slot_count - 1))
                                                padding (7, 3) text_size 12 text_color "#cc4444" text_hover_color "#ff8888"
                                                background Solid("#140808") hover_background Solid("#220e0e")
                                            frame background Solid("#0a1020") padding (5, 2) yalign 0.5:
                                                text str(_slot_count) size 12 bold True color "#4488ff" xalign 0.5
                                            textbutton "+":
                                                action SetDict(vns.ui, 'se_slot_count', _slot_count + 1)
                                                padding (7, 3) text_size 12 text_color "#44cc44" text_hover_color "#88ff88"
                                                background Solid("#081408") hover_background Solid("#0e2010")
    
                                    frame background Solid("#0d1830") xsize 1 ysize 36 yalign 0.5 padding (0, 0)
                                    textbutton "🚪 Leave Scene Editor" yalign 0.5:
                                        action Function(vns.go, "graph")
                                        text_size 14 text_bold True padding (16, 12)
                                        background Solid("#3a1010") hover_background Solid("#5a1818")
                                        text_color "#ff8888" text_hover_color "#ffffff"

        ## ── DRAG LAYER (must be last child so it draws on top of everything) ────────
        use vn_se_emoji_drags()


## ── Floating emoji tool drags (rendered above everything) ────────────────────
## Three emoji icons that can be dragged freely across the whole screen.
## Drop on any timeline row to stamp that event type on that layer.
## Snaps back to home position above the toolbar buttons on release.

screen vn_se_emoji_drags():
    zorder 200
    modal False

    ## Home Y = vertically centered in the 64px toolbar at screen bottom
    $ _ey = renpy.config.screen_height - 32

    ## Home X = center of each 150px button (left nav=160+1 separator)
    ## Dialogue: 161..310 → center 235, emoji ~195
    ## Music:    312..461 → center 386, emoji ~346
    ## Image:    462..611 → center 536, emoji ~496
    $ _ex_dlg = 195
    $ _ex_mus = 346
    $ _ex_img = 496

    draggroup xfill True yfill True:
        ## ── 💬 Dialogue
        drag xpos _ex_dlg ypos _ey:
            drag_name "tool_dialogue_7"
            draggable True
            droppable False
            dragged _vn_timeline_clip_dragged
            anchor (0.5, 0.5)
            frame xsize 48 ysize 48 padding (0,0):
                background Solid("#00000066")
                hover_background Solid("#1e884488")
                text "💬" size 30 align (0.5, 0.5)

        ## ── 🎵 Music
        drag xpos _ex_mus ypos _ey:
            drag_name "tool_music_7"
            draggable True
            droppable False
            dragged _vn_timeline_clip_dragged
            anchor (0.5, 0.5)
            frame xsize 48 ysize 48 padding (0,0):
                background Solid("#00000066")
                hover_background Solid("#22669988")
                text "🎵" size 30 align (0.5, 0.5)

        ## ── 🖼 Image
        drag xpos _ex_img ypos _ey:
            drag_name "tool_image_7"
            draggable True
            droppable False
            dragged _vn_timeline_clip_dragged
            anchor (0.5, 0.5)
            frame xsize 48 ysize 48 padding (0,0):
                background Solid("#00000066")
                hover_background Solid("#9933cc88")
                text "🖼" size 30 align (0.5, 0.5)

        ## ── 🔑 Variable
        drag xpos 646 ypos _ey:
            drag_name "tool_setvar_7"
            draggable True
            droppable False
            dragged _vn_timeline_clip_dragged
            anchor (0.5, 0.5)
            frame xsize 48 ysize 48 padding (0,0):
                background Solid("#00000066")
                hover_background Solid("#cc992288")
                text "🔑" size 30 align (0.5, 0.5)

        ## ── 🔀 Logic If
        drag xpos 796 ypos _ey:
            drag_name "tool_if_7"
            draggable True
            droppable False
            dragged _vn_timeline_clip_dragged
            anchor (0.5, 0.5)
            frame xsize 48 ysize 48 padding (0,0):
                background Solid("#00000066")
                hover_background Solid("#cc333388")
                text "🔀" size 30 align (0.5, 0.5)

## ── Tween Picker ─────────────────────────────────────────────────────────────

screen vn_tween_picker():
    zorder 1000
    if vns.ui.get('_tween_picker_ev'):
        button xfill True yfill True action SetDict(vns.ui, '_tween_picker_ev', None)
        frame background Solid(VN_BG2) padding (20,20) xalign 0.5 yalign 0.5:
            vbox spacing 12:
                text "Select Animation Tween" style "vn_t_label"
                text "Standard Ren\'Py animation warpers" style "vn_t_faint" size 11
                hbox spacing 10 box_wrap True xmaximum 600:
                    for _t in ['linear', 'ease', 'easein', 'easeout', 'easein_elastic', 'easeout_elastic', 'easein_bounce', 'easeout_bounce']:
                        textbutton _t style "vn_btn":
                            action [
                                SetDict(vns.ui.get('_tween_picker_ev'), 'tween', _t),
                                Function(vns.save),
                                SetDict(vns.ui, '_tween_picker_ev', None)
                            ]
