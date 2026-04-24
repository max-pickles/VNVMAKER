## ???????????????????????????????????????????????
##  VN Maker ? State + Notification System
## ???????????????????????????????????????????????

init python:
    import time as _time

    class _VNUndoRedo:
        MAX = 50
        def __init__(self):
            self._undo_stack = []  # list of (name, do_fn, undo_fn)
            self._redo_stack = []

        def commit(self, name, do_fn, undo_fn):
            do_fn()
            self._undo_stack.append((name, do_fn, undo_fn))
            self._redo_stack.clear()
            if len(self._undo_stack) > self.MAX:
                self._undo_stack.pop(0)

        def undo(self):
            if self._undo_stack:
                name, do_fn, undo_fn = self._undo_stack.pop()
                undo_fn()
                self._redo_stack.append((name, do_fn, undo_fn))
                renpy.restart_interaction()

        def redo(self):
            if self._redo_stack:
                name, do_fn, undo_fn = self._redo_stack.pop()
                do_fn()
                self._undo_stack.append((name, do_fn, undo_fn))
                renpy.restart_interaction()

        def can_undo(self): return bool(self._undo_stack)
        def can_redo(self): return bool(self._redo_stack)
        def undo_name(self): return self._undo_stack[-1][0] if self._undo_stack else ""
        def redo_name(self): return self._redo_stack[-1][0] if self._redo_stack else ""

    class _VNState:
        """Single source of truth for the entire editor."""
        def __init__(self):
            self.panel      = "home"
            self.project    = None
            self.scene_id   = None
            self.event_id   = None
            self.char_id    = None
            self.asset_cb   = None
            self.asset_mode = "images"
            self.asset_path = "images"
            self.history    = _VNUndoRedo()
            self.notifications = []
            self.new_proj   = {'title': '', 'author': '', 'show': False, 'focus': 'title'}
            self.import_proj = {'show': False, 'path': '', 'title': '', 'author': '', 'result': None, 'warnings': []}
            self.ui         = {
                'asset_search':    '',
                'asset_folder':    '',
                'scene_label':     '',
                'export_path':     '',
                'dialogue_search': '',
                '_focus':          '',   ## tracks which input box is currently active
            }
            self.test_external = False
            self.preview_scene_id = None

        # ?? Navigation ?????????????????????????
        def go(self, panel):
            self.panel = panel
            self.ui['_focus'] = ''   ## clear input focus on panel switch
            renpy.restart_interaction()

        def open_project(self, proj):
            self.project  = proj
            self.scene_id = None
            self.event_id = None
            self.char_id  = None
            self.panel    = "hub"
            vng.reset_layout(proj)
            renpy.restart_interaction()

        def close_project(self):
            self.project  = None
            self.panel    = "home"
            renpy.restart_interaction()

        # ?? Save shortcut ???????????????????????
        def save(self):
            """Explicit user save - shows notification."""
            if self.project:
                vng.save_layout(self.project)
                vn_save(self.project)
                self.notify("Project saved!", "ok")

        def save_silent(self):
            """Auto-save: persists data without showing a notification."""
            if self.project:
                vng.save_layout(self.project)
                vn_save(self.project)

        # ?? Notifications ???????????????????????
        def notify(self, text, kind="info"):
            now = _time.time()
            # Deduplicate: skip if same message shown in last 1.5s
            for n in self.notifications:
                if n['text'] == text and (n['expires'] - 4.0) > now - 1.5:
                    return
            # Cap at 3 toasts
            if len(self.notifications) >= 3:
                self.notifications.pop(0)
            self.notifications.append({
                'id':      str(id(text)) + str(int(now * 1000)),
                'text':    text,
                'kind':    kind,
                'expires': now + 4.0,
            })
            renpy.restart_interaction()

        def tick_notifications(self):
            now = _time.time()
            before = len(self.notifications)
            self.notifications = [n for n in self.notifications if n['expires'] > now]
            if len(self.notifications) != before:
                renpy.restart_interaction()

        # ?? Current helpers ?????????????????????
        @property
        def scene(self):
            if self.project and self.scene_id:
                return vn_find_scene(self.project, self.scene_id)
            return None

        @property
        def events(self):
            s = self.scene
            return s['events'] if s else []

        @property
        def char(self):
            if self.project and self.char_id:
                return vn_find_char(self.project, self.char_id)
            return None

        def pick_asset(self, category, current=None, callback=None):
            """
            Transition to the Generic Asset Browser to pick a file.
            category: 'images', 'movie', 'audio'
            Executes callback(path) when selected.
            """
            self.asset_mode = category
            self.asset_cb = callback
            self.ui['_asset_prev_panel'] = self.panel
            self.go("assets")

    vns = _VNState()  # global singleton

## ?? Notification overlay ?????????????????????????????????????????????????????

transform vn_ntf_fade():
    alpha 1.0
    pause 3.0
    linear 0.3 alpha 0.0

screen vn_notifications():
    zorder 200
    $ vns.tick_notifications()

    frame background None xalign 1.0 yalign 0.0 xoffset -16 yoffset 16 xsize 360 padding (0,0):
        vbox spacing 6 xfill True:
            for ntf in vns.notifications:
                $ col = {"ok": VN_OK, "warn": VN_WARN, "err": VN_ERR, "info": VN_INFO}.get(ntf['kind'], VN_INFO)
                $ icon = {"ok": "✅", "warn": "⚠️", "err": "❌", "info": "ℹ️"}.get(ntf['kind'], "ℹ️")
                
                frame background Solid(VN_BG2) xfill True padding (0, 0) at vn_ntf_fade():
                    vbox spacing 0:
                        ## Coloured top strip
                        frame background Solid(col) xfill True ysize 2 padding (0,0)
                        ## Body
                        frame background Solid(VN_BG2) xfill True padding (14, 12):
                            hbox spacing 12 yalign 0.5:
                                text icon style "vn_t" color col size 16 yalign 0.5
                                text ntf['text'] style "vn_t" size 14 yalign 0.5 xfill True color VN_TEXT


## ?? Editor Scene Compilation (Play from Here) ??????????????????????????????????




screen vn_play_overlay():
    zorder 1000
    frame background Solid("#000000a0") padding (16, 10) xalign 1.0 yalign 0.0 xoffset -20 yoffset 20:
        hbox spacing 12 yalign 0.5:
            text "👁️ Live Preview" style "vn_t_sub" size 16 yalign 0.5
            textbutton "⬅️ Return to Editor" style "vn_btn_danger":
                action Jump("_vn_preview_end")

label _vn_preview_end:
    hide screen vn_play_overlay
    stop music fadeout 0.5
    stop sound
    stop voice
    return


## ?? Color palette swatch helper (used in char/template editors) ???????????????

init python:
    VN_PALETTE = [
        "#c8d0ff","#ff9eb5","#ffcba4","#ffe58a","#b5ffb5","#a4e4ff",
        "#e0b5ff","#ff8888","#88ffcc","#ffffff","#aaaaaa","#666666",
        "#ff6b6b","#ffa07a","#ffd700","#90ee90","#87ceeb","#dda0dd",
        "#6c63ff","#00d4c8","#f04545","#f5a623","#27d476","#4ba0f0",
        "#1a1a2e","#16213e","#0f3460","#e94560","#533483","#2b2d42",
    ]

    VN_FONTS = [
        ("DejaVuSans.ttf",         "Regular"),
        ("DejaVuSans.ttf",         "Bold"),
        ("DejaVuSans.ttf",         "Italic"),
    ]

    VN_SIZES = [14, 16, 18, 20, 22, 24, 26, 28, 32, 36, 42]

    VN_TRANSITIONS = ["dissolve", "fade", "flash", "wipe_left", "wipe_right", "none"]

    VN_EFFECTS = ["dissolve", "fade", "flash", "shake", "wipe_left", "wipe_right"]

    VN_POSES = ["neutral", "happy", "sad", "angry", "surprised", "custom1", "custom2"]

    VN_SIDES = ["left", "center", "right"]


init python:
    def _vn_hub_stats(proj):
        """Compute project statistics for the hub dashboard."""
        if not proj:
            return {}
        import time as _t
        scenes = proj.get('scenes', [])
        total_ev = sum(len(s.get('events', [])) for s in scenes)
        total_words = 0
        for s in scenes:
            for ev in s.get('events', []):
                for key in ('text', 'prompt'):
                    total_words += len((ev.get(key) or '').split())
        read_min = max(1, total_words // 200)
        updated = proj.get('updated', 0)
        last_saved = _t.strftime('%b %d %Y %I:%M%p', _t.localtime(updated)) if updated else 'Never'
        return {
            'scenes':     len(scenes),
            'characters': len(proj.get('characters', [])),
            'events':     total_ev,
            'words':      total_words,
            'read_min':   read_min,
            'last_saved': last_saved,
        }
