## ???????????????????????????????????????????????
##  VN Maker ? Test Player + Export
## ???????????????????????????????????????????????

## ?? Test Player ??????????????????????????????????????????????????????????????

init python:
    class _VNPlayer:
        """Interprets a VNProject and drives the player screen state."""
        def __init__(self):
            self.proj    = None
            self.scene   = None
            self.events  = []
            self.idx     = 0
            self.done    = False
            self.ev      = None
            self.choice_made = False
            self.choice_target = None

        def start(self, proj, scene_id=None):
            self.proj   = proj
            self.done   = False
            self.idx    = 0
            sid = scene_id or proj.get('start')
            if not sid and proj.get('scenes'):
                sid = proj['scenes'][0]['id']
            self.load_scene(sid)

        def load_scene(self, sid):
            self.scene  = vn_find_scene(self.proj, sid) if sid else None
            self.events = self.scene['events'] if self.scene else []
            self.idx    = 0
            self.refresh_ev()

        def refresh_ev(self):
            if self.scene and 0 <= self.idx < len(self.events):
                self.ev = self.events[self.idx]
            else:
                self.ev = None
                self.done = True

        def _get_active_ev(self):
            if not self.ev: return None
            
            # Unplug all layers including layer0
            slot_events = []
            if self.ev.get('type'):
                slot_events.append(self.ev)
                
            for k, v in self.ev.items():
                if k.startswith('layer') and isinstance(v, dict) and v.get('type'):
                    slot_events.append(v)
                    
            # Find the primary blocking event (dialogue/narration/choice) first
            for e in slot_events:
                if e.get('type') in ('dialogue', 'narration', 'choice'):
                    return e
            
            # Fallback to any effect/wait/jump
            for e in slot_events:
                if e.get('type') in ('effect', 'wait', 'jump', 'bg', 'music', 'image', 'sfx'):
                    return e
                    
            return None

        def advance(self):
            active = self._get_active_ev()
            if not active:
                self.idx += 1
                self.refresh_ev()
                return
                
            t = active.get('type')
            if t in ('dialogue', 'narration', 'effect', 'wait', 'bg', 'music', 'image', 'sfx'):
                self.idx += 1
                self.refresh_ev()
            elif t == 'jump':
                tid = active.get('scene_id')
                if tid:
                    self.load_scene(tid)
                else:
                    self.done = True

        def choose(self, opt):
            target = opt.get('scene')
            if target:
                self.load_scene(target)
            else:
                self.idx += 1
                self.refresh_ev()

        def current_char(self):
            active = self._get_active_ev()
            if active and active.get('type') == 'dialogue':
                return vn_find_char(self.proj, active.get('char_id'))
            return None

        def current_sprite(self):
            active = self._get_active_ev()
            if active and active.get('type') == 'dialogue' and active.get('char_id'):
                return vn_char_sprite(self.proj, active['char_id'], active.get('pose','neutral'))
            return None

    vnp = _VNPlayer()

screen vn_player_panel():
    frame background Solid(VN_BG0) xfill True yfill True padding (0,0):
        if not vns.project:
            vbox xalign 0.5 yalign 0.5 spacing 12:
                text "No project open." style "vn_t_dim" xalign 0.5
        else:
            vbox spacing 0 xfill True yfill True:
                ## Toolbar
                frame background Solid(VN_BG1) xfill True padding (14, 10):
                    hbox xfill True spacing 14:
                        textbutton "⬅️ Back to Editor" style "vn_btn_ghost":
                            action Function(vns.go, "hub")
                        frame background Solid(VN_BDR) xsize 1 yfill True
                        text "Test Player" style "vn_t_sub" yalign 0.5 xfill True
                        ## Scene picker
                        for sc in vns.project.get('scenes', []):
                            textbutton sc['label'] style "vn_btn":
                                action Function(_vnp_start, vns.project, sc['id'])
                        textbutton "⏯️ Start from beginning" style "vn_btn_teal":
                            action Function(_vnp_start, vns.project, None)

                ## Player area
                frame background Solid("#000") xfill True yfill True padding (0,0):
                    if vnp.proj is None:
                        vbox xalign 0.5 yalign 0.5 spacing 16:
                            text "▶️" size 64 xalign 0.5 color VN_TEAL
                            text "Press 'Start from beginning'" style "vn_t_dim" xalign 0.5
                            text "or choose a scene above" style "vn_t_faint" xalign 0.5
                    elif vnp.done:
                        vbox xalign 0.5 yalign 0.5 spacing 16:
                            text "✅" size 56 xalign 0.5 color VN_OK
                            text "Story complete!" style "vn_t_head" xalign 0.5
                            textbutton "🔄 Restart" style "vn_btn_accent" xalign 0.5:
                                action Function(_vnp_start, vns.project, None)
                    else:
                        ## Background via frame background (scales to fill)
                        $ sc = vnp.scene
                        $ _player_bg = Image(sc['bg']) if sc and sc.get('bg') else Solid("#000000")
                        frame background _player_bg xfill True yfill True padding (0,0):

                            ## Character sprite
                            $ spr = vnp.current_sprite()
                            if spr:
                                $ ev = vnp.ev
                                $ side = ev.get('side', 'center')
                                add spr:
                                    yalign 1.0
                                    xalign {"left":0.15,"center":0.5,"right":0.85}.get(side,0.5)
                                    zoom 0.65

                            ## UI overlay (bottom)
                            $ ev = vnp._get_active_ev()
                            if ev:
                                $ t = ev.get('type','')
                                if t == 'choice':
                                    ## Choice menu
                                    frame background Solid("#000000cc") xfill True yalign 1.0 padding (30, 20):
                                        vbox spacing 12 xalign 0.5:
                                            if ev.get('prompt'):
                                                text ev['prompt'] style "vn_t" size 18 xalign 0.5
                                            for opt in ev.get('opts', []):
                                                button style "vn_btn_accent" xsize 400 xalign 0.5:
                                                    action Function(vnp.choose, opt)
                                                    text opt.get('text','') xalign 0.5 style "vn_btn_accent_text"
                                elif t in ('dialogue', 'narration') or (t == 'effect' and ev.get('text', '').strip()):
                                    ## Dialogue box
                                    frame background Solid("#000000bb") xfill True yalign 1.0 padding (24, 20):
                                        vbox spacing 8:
                                            if t == 'dialogue':
                                                $ char = vnp.current_char()
                                                if char:
                                                    text char['display'] style "vn_t" font VN_FONTB size 17 color char['color']
                                            text ev.get('text','') style "vn_t" size 18
                                            text "🖱️ Click to continue" style "vn_t_faint" size 12 xalign 1.0

                                    ## Click anywhere to advance
                                    button background None xfill True yfill True:
                                        action Function(vnp.advance)
                                elif t in ('effect', 'wait', 'bg', 'music', 'image', 'sfx'):
                                    ## Auto-advance visual cue
                                    frame background None xfill True yalign 1.0 padding (20,10):
                                        hbox xalign 1.0:
                                            $ _tlbl = "[[" + t.upper() + "]]"
                                            text _tlbl style "vn_t_faint" size 13
                                            textbutton "Skip ⏭️" style "vn_btn_ghost":
                                                action Function(vnp.advance)

## ?? Export Panel ?????????????????????????????????????????????????????????????

screen vn_export_panel():
    default export_path = ""
    default export_done = False
    default export_msg  = ""


    frame background Solid(VN_BG0) xfill True yfill True padding (40, 40):
        vbox spacing 24 xfill True:
            text "Export Project" style "vn_t_head"
            text "Generate .rpy script files you can use in any Ren'Py project." style "vn_t_dim"

            ## Export info
            frame style "vn_fr_card" xfill True:
                vbox spacing 8:
                    $ sc_count = len(vns.project.get('scenes', [])) if vns.project else 0
                    $ ch_count = len(vns.project.get('characters', [])) if vns.project else 0
                    text f"Project: {vns.project['title'] if vns.project else '-'}" style "vn_t" size 17
                    text f"{sc_count} scenes  {ch_count} characters" style "vn_t_dim"

            ## Output path
            vbox spacing 8:
                text "Project Folder Name" style "vn_t_label"
                use vn_text_input("vn_export_path", vns.ui, "export_path", "My New Game", 200)
                text "This will create a new game folder in your Ren'Py projects directory." style "vn_t_faint" size 13

            ## Export button
            textbutton "📦 Create Standalone Game" style "vn_btn_accent" xsize 280:
                sensitive bool(vns.project and vns.ui.get('export_path'))
                action [
                    Function(_vn_do_export, vns.ui.get('export_path','')),
                ]

            ## Result message shown via notification system

            frame background Solid(VN_BDR) ysize 1 xfill True

            ## Also save as persistent JSON copy
            vbox spacing 8:
                text "Project Data" style "vn_t_sub"
                text "Your project is already auto-saved inside Ren'Py persistent storage.\nYou can also generate a JSON backup." style "vn_t_faint"
                textbutton "💾 Save JSON Backup" style "vn_btn_ghost":
                    sensitive bool(vns.project)
                    action Function(_vn_json_backup)

            textbutton "⬅️ Back" style "vn_btn_ghost":
                action Function(vns.go, "hub")

init python:
    def _vnp_start(proj, scene_id):
        vnp.start(proj, scene_id)
        renpy.restart_interaction()

    def _vn_do_export(rel_path):
        if not vns.project or not rel_path:
            return
        ok, msg = _vn_export_standalone(vns.project, rel_path)
        vns.notify(msg, "ok" if ok else "err")

    def _vn_json_backup():
        import json as _json
        base = vn_game_dir()
        backup_dir = os.path.join(base, "exports", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        fname = vns.project.get('title','project').replace(' ','_') + ".json"
        path  = os.path.join(backup_dir, fname)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                _json.dump(vns.project, f, indent=2, ensure_ascii=False)
            vns.notify(f"JSON backup saved:\nexports/backups/{fname}", "ok")
        except Exception as e:
            vns.notify(f"Backup failed: {e}", "err")
