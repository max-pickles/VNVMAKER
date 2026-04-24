## =============================================================================
##  VN Maker - Scene Flow + Dialogue Editor
## ...............................................

init python:
    renpy.music.register_channel("preview", mixer="music", loop=False)

## "?"? Multi-line Text Editor "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?
##
## vn_texteditor(ev, key): a Notepad-style multi-line text editor backed by
## ev[key].  Supports typing, Backspace, Delete, Enter, arrow keys,
## Home/End, Ctrl+A, and mouse-click-to-position via a transparent hit-grid.
## The cursor is rendered as a blinking | character drawn inline with the text.

python early:
    import pygame

    class VNTextEditor(object):
        """
        Holds cursor position and line-cache for one text-editor instance.
        Stored in a screen-local variable so it is recreated each time the
        inspector switches to a different event.
        """
        def __init__(self, ev, key):
            self.ev         = ev
            self.key        = key
            self.cursor     = len(ev.get(key, '') or '')
            self.sel_anchor = -1   ## -1 = no selection
            self._initial_text = self.text

        @property
        def sel_range(self):
            """Returns (lo, hi) char indices if selection active, else None."""
            if self.sel_anchor < 0:
                return None
            lo, hi = sorted((self.sel_anchor, self.cursor))
            return (lo, hi) if lo != hi else None

        def clear_sel(self):
            self.sel_anchor = -1

        def delete_selection(self):
            """Delete selected text, place cursor at lo. Returns True if deleted."""
            r = self.sel_range
            if not r:
                return False
            lo, hi = r
            self.text   = self.text[:lo] + self.text[hi:]
            self.cursor = lo
            self.sel_anchor = -1
            return True
            
        def commit_history(self):
            if self.text != self._initial_text:
                old_t = self._initial_text
                new_t = self.text
                target_ev = self.ev
                k = self.key
                def _do():
                    target_ev[k] = new_t
                def _undo():
                    target_ev[k] = old_t
                store.vns.history.commit("Edit Text", _do, _undo)
                self._initial_text = self.text

        @property
        def text(self):
            return self.ev.get(self.key, '') or ''

        @text.setter
        def text(self, v):
            self.ev[self.key] = v

        def lines(self):
            return self.text.split('\n')

        ## "?"? Cursor math "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?
        def _cur_row_col(self):
            t = self.text
            c = max(0, min(self.cursor, len(t)))
            before = t[:c]
            lines  = before.split('\n')
            return len(lines) - 1, len(lines[-1])

        def _pos_of(self, row, col):
            ls = self.lines()
            p = sum(len(ls[i]) + 1 for i in range(min(row, len(ls))))
            col_max = len(ls[min(row, len(ls)-1)]) if ls else 0
            return p + max(0, min(col, col_max))

        ## "?"? Keyboard actions "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?
        def insert(self, ch):
            self.delete_selection()   ## replace selection if any
            t = self.text
            c = self.cursor
            self.text   = t[:c] + ch + t[c:]
            self.cursor = c + len(ch)
            renpy.restart_interaction()

        def backspace(self):
            if self.delete_selection():   ## delete selection if any
                renpy.restart_interaction()
                return
            if self.cursor > 0:
                t = self.text
                c = min(self.cursor, len(t))
                self.text   = t[:c-1] + t[c:]
                self.cursor = c - 1
                renpy.restart_interaction()

        def delete_fwd(self):
            if self.delete_selection():   ## delete selection if any
                renpy.restart_interaction()
                return
            t = self.text
            c = min(self.cursor, len(t))
            if c < len(t):
                self.text = t[:c] + t[c+1:]
                renpy.restart_interaction()

        def move(self, dx, dy, extend_sel=False):
            if not extend_sel:
                self.clear_sel()
            elif self.sel_anchor < 0:
                self.sel_anchor = self.cursor  ## start new selection from here
            row, col = self._cur_row_col()
            ls = self.lines()
            if dy != 0:
                row = max(0, min(row + dy, len(ls) - 1))
            col = max(0, min(col + dx, len(ls[row])))
            if dx < 0 and col == len(ls[row]) and self.cursor > 0 and dy == 0:
                self.cursor -= 1
            elif dx > 0 and col == 0 and dy == 0:
                self.cursor += 1
            else:
                self.cursor = self._pos_of(row, col)
            renpy.restart_interaction()

        def home(self):
            row, _ = self._cur_row_col()
            self.cursor = self._pos_of(row, 0)
            renpy.restart_interaction()

        def end(self):
            row, _ = self._cur_row_col()
            ls = self.lines()
            self.cursor = self._pos_of(row, len(ls[row]))
            renpy.restart_interaction()

        def select_all(self):
            self.sel_anchor = 0
            self.cursor     = len(self.text)
            renpy.restart_interaction()

        ## "?"? Click-to-position "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?
        ## row, col estimated from pixel hit ?" good enough for monospace-ish
        def click(self, rx, ry, line_h=22, char_w=9):
            row = max(0, int(ry // line_h))
            col = max(0, int((rx + char_w // 2) // char_w))
            ls  = self.lines()
            row = min(row, len(ls) - 1)
            col = min(col, len(ls[row]))
            self.cursor = self._pos_of(row, col)
            renpy.restart_interaction()


## VNEditorInputValue needs init python so InputValue is in scope by then.
init python:
    class VNTextEditorCDD(renpy.Displayable):
        """
        Custom Displayable that intercepts all pygame.KEYDOWN events to give us full control
        over cursor movement (arrows), deletions (backspace/delete), and typing, avoiding
        the aggressive event-swallowing behavior of Ren'Py's native Input widget.
        Also handles MOUSEBUTTONDOWN for click-to-position the text cursor.
        """
        ## Font metrics for cursor hit-testing (matching vn_ted_text style)
        LINE_H  = 22  ## pixels per line
        CHAR_W  = 8   ## approximate monospace char width
        PAD_X   = 12  ## left padding inside the text frame
        PAD_Y   = 8   ## top  padding inside the text frame

        def __init__(self, ed, font_size=18, line_h=22, char_w=8, pad_x=12, pad_y=8, **kwargs):
            super(VNTextEditorCDD, self).__init__(**kwargs)
            self.ed        = ed
            self.line_h    = line_h
            self.char_w    = char_w
            self.pad_x     = pad_x
            self.pad_y     = pad_y
            self._dragging = False
            self._w        = 0
            self._h        = 0

        def _hit_to_cursor(self, x, y):
            """Convert pixel coords (relative to text area) to char index."""
            rel_x = x - self.pad_x
            rel_y = y - self.pad_y
            row = max(0, int(rel_y // self.line_h))
            col = max(0, int((rel_x + self.char_w // 2) // self.char_w))
            ls  = self.ed.lines()
            row = min(row, len(ls) - 1)
            col = min(col, len(ls[row]))
            return self.ed._pos_of(row, col)

        def _inside(self, x, y):
            """True when the mouse is within this displayable's rendered area."""
            return 0 <= x <= self._w and 0 <= y <= self._h

        def render(self, w, h, st, at):
            self._w = w
            self._h = h
            renpy.redraw(self, 0.5)
            return renpy.Render(w, h)

        def event(self, ev, x, y, st):
            if not store.vns.ui.get('_ted_live_focused', False) and not store.vns.ui.get('_ted_focused', False):
                return None

            ## ── Mouse drag → selection ─────────────────────────────────────
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if not self._inside(x, y):  ## click outside the text box — pass through
                    self._dragging = False
                    return None
                pos = self._hit_to_cursor(x, y)
                self.ed.sel_anchor = pos
                self.ed.cursor     = pos
                self._dragging     = True
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()

            if ev.type == pygame.MOUSEMOTION and self._dragging:
                self.ed.cursor = self._hit_to_cursor(x, y)
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self._dragging = False
                if not self._inside(x, y):
                    return None
                if self.ed.sel_range is None:
                    self.ed.clear_sel()
                raise renpy.IgnoreEvent()

            if ev.type == pygame.KEYDOWN:
                shift = bool(ev.mod & pygame.KMOD_SHIFT)
                ctrl  = bool(ev.mod & pygame.KMOD_CTRL)

                if ev.key == pygame.K_a and ctrl:
                    self.ed.select_all()
                    raise renpy.IgnoreEvent()

                if ev.key == pygame.K_z and ctrl:
                    if not shift:
                        self.ed.text = self.ed._initial_text
                        self.ed.cursor = len(self.ed.text)
                        self.ed.clear_sel()
                        raise renpy.IgnoreEvent()
                    return None  ## Let Redo pass through

                if ev.key == pygame.K_LEFT:
                    self.ed.move(-1, 0, extend_sel=shift)
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_RIGHT:
                    self.ed.move(1, 0, extend_sel=shift)
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_UP:
                    self.ed.move(0, -1, extend_sel=shift)
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_DOWN:
                    self.ed.move(0, 1, extend_sel=shift)
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_HOME:
                    self.ed.home()
                    if not shift: self.ed.clear_sel()
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_END:
                    self.ed.end()
                    if not shift: self.ed.clear_sel()
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_BACKSPACE:
                    self.ed.backspace()
                    raise renpy.IgnoreEvent()
                elif ev.key == pygame.K_DELETE:
                    self.ed.delete_fwd()
                    raise renpy.IgnoreEvent()
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.ed.insert('\n')
                    raise renpy.IgnoreEvent()
                elif ev.unicode and ev.unicode.isprintable():
                    self.ed.insert(ev.unicode)
                    raise renpy.IgnoreEvent()

screen vn_texteditor(ed):
    frame background Solid("#090c1e") xfill True ysize 180 padding (0, 0):
        fixed xfill True yfill True:

            ## Scrollable text area
            viewport id "vn_ted_vp" yadjustment None mousewheel True xfill True yfill True scrollbars "vertical" style_prefix "vn_vscroll":
                frame background None xfill True padding (12, 8):
                    vbox xfill True spacing 0:
                        $ _ted_row, _ted_col = ed._cur_row_col()
                        $ _ted_focused = vns.ui.get('_ted_focused', False)
                        $ _ted_sel = ed.sel_range
                        ## Compute line-start offsets once
                        $ _ted_ls = ed.lines()
                        $ _ted_offsets = []
                        $ _off = 0
                        for _tl in _ted_ls:
                            $ _ted_offsets.append(_off)
                            $ _off += len(_tl) + 1
                        for _li, _ln in enumerate(_ted_ls):
                            $ _line_start = _ted_offsets[_li]
                            $ _line_end   = _line_start + len(_ln)
                            hbox spacing 0 ysize 22:
                                if _ted_focused and _ted_sel:
                                    ## Compute per-line selection overlap
                                    $ _sel_lo = max(_ted_sel[0], _line_start) - _line_start
                                    $ _sel_hi = min(_ted_sel[1], _line_end)   - _line_start
                                    $ _sel_lo = max(0, min(_sel_lo, len(_ln)))
                                    $ _sel_hi = max(0, min(_sel_hi, len(_ln)))
                                    ## Before selection
                                    if _sel_lo > 0:
                                        text _ln[:_sel_lo] style "vn_ted_text"
                                    ## Highlighted selection
                                    if _sel_hi > _sel_lo:
                                        frame background Solid("#3a6bc888") padding (0,0) ysize 20 yalign 0.5:
                                            text _ln[_sel_lo:_sel_hi] style "vn_ted_text"
                                    ## Caret and rest
                                    if _li == _ted_row:
                                        ## Caret sits at cursor within this line
                                        text "|" style "vn_ted_cursor" at _vn_caret_blink
                                        text _ln[_ted_col:] style "vn_ted_text"
                                    else:
                                        text (_ln[_sel_hi:] if _sel_hi < len(_ln) else (' ' if not _ln else '')) style "vn_ted_text"
                                elif _ted_focused and _li == _ted_row:
                                    text _ln[:_ted_col] style "vn_ted_text"
                                    text "|" style "vn_ted_cursor" at _vn_caret_blink
                                    text _ln[_ted_col:] style "vn_ted_text"
                                else:
                                    text (_ln if _ln != '' else ' ') style "vn_ted_text"

            ## Click-catcher: only when not yet focused
            if not vns.ui.get('_ted_focused', False):
                button xfill True yfill True background None hover_background Solid("#ffffff08") padding (0,0):
                    action [SetDict(vns.ui, '_ted_focused', True), SetDict(vns.ui, '_ted_live_focused', False), Function(renpy.set_focus, None, None)]

            ## CDD covers entire area for keyboard + drag
            if vns.ui.get('_ted_focused', False):
                add VNTextEditorCDD(ed, pad_x=12, pad_y=8, line_h=22, char_w=8)

transform _vn_caret_blink:
    alpha 1.0
    pause 0.53
    alpha 0.0
    pause 0.47
    repeat

screen vn_live_texteditor(ed, t_size, t_color, t_italic=False):
    fixed xfill True yfit True:
        vbox xfill True spacing 0:
            $ _ted_row, _ted_col = ed._cur_row_col()
            $ _live_focused = vns.ui.get('_ted_live_focused', False)
            $ _live_sel = ed.sel_range
            $ _live_ls = ed.lines()
            $ _live_off = 0
            $ _live_offsets = []
            for _tl2 in _live_ls:
                $ _live_offsets.append(_live_off)
                $ _live_off += len(_tl2) + 1
            for _li, _ln in enumerate(_live_ls):
                $ _lstart = _live_offsets[_li]
                $ _lend   = _lstart + len(_ln)
                hbox spacing 0:
                    if _live_focused and _live_sel:
                        $ _slo = max(0, min(max(_live_sel[0], _lstart) - _lstart, len(_ln)))
                        $ _shi = max(0, min(min(_live_sel[1], _lend)   - _lstart, len(_ln)))
                        if _slo > 0:
                            text _ln[:_slo] style "vn_t" size t_size color t_color italic t_italic
                        if _shi > _slo:
                            frame background Solid("#3a6bc888") padding (0,0):
                                text _ln[_slo:_shi] style "vn_t" size t_size color t_color italic t_italic
                        if _li == _ted_row:
                            text "|" style "vn_t" size t_size color t_color italic t_italic at _vn_caret_blink
                            text _ln[_ted_col:] style "vn_t" size t_size color t_color italic t_italic
                        else:
                            text (_ln[_shi:] if _shi < len(_ln) else (' ' if not _ln else '')) style "vn_t" size t_size color t_color italic t_italic
                    elif _live_focused and _li == _ted_row:
                        text _ln[:_ted_col] style "vn_t" size t_size color t_color italic t_italic
                        text "|" style "vn_t" size t_size color t_color italic t_italic at _vn_caret_blink
                        text _ln[_ted_col:] style "vn_t" size t_size color t_color italic t_italic
                    else:
                        text (_ln if _ln != '' else ' ') style "vn_t" size t_size color t_color italic t_italic

        if not vns.ui.get('_ted_live_focused', False):
            button xfill True yfill True background None hover_background Solid("#ffffff22") padding (0,0):
                action [SetDict(vns.ui, '_ted_live_focused', True), SetDict(vns.ui, '_ted_focused', False), Function(renpy.set_focus, None, None)]
        else:
            add VNTextEditorCDD(ed, pad_x=0, pad_y=0, line_h=t_size+4, char_w=max(1, int(t_size*0.55)))



## "?"? Scene Flow Panel "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?

screen vn_scenes_panel():
    default new_label = ""


    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
        hbox spacing 0 xfill True yfill True:

            ## Scene list (left column)
            frame background Solid(VN_BG1) xsize 280 yfill True padding (0, 0):
                vbox xfill True yfill True spacing 0:
                    ## Header
                    frame background Solid(VN_BG2) xfill True padding (16, 12):
                        vbox spacing 10 xfill True:
                            text "Scenes" style "vn_t_sub" xfill True
                            hbox spacing 8 xfill True:
                                if vns.ui.get('_focus') == "vn_scene_label_input":
                                    button style "vn_fr_input" xfill True:
                                        action NullAction()
                                        input id "vn_scene_label_input" style "vn_input" value DictInputValue(vns.ui, 'scene_label') length 40 size 14
                                else:
                                    $ _fv = vns.ui.get('scene_label', '') or ''
                                    button style "vn_fr_input" xfill True:
                                        action [SetDict(vns.ui, '_focus', "vn_scene_label_input"), Function(renpy.set_focus, None, "vn_scene_label_input")]
                                        text (_fv if _fv else "Scene name…") style "vn_input" color (VN_FAINT if not _fv else VN_TEXT) size 14
                                textbutton "+" style "vn_btn_accent":
                                    action Function(
                                        _vn_add_scene,
                                        vns.ui.get('scene_label', '') or "Scene"
                                    )

                    ## Scene list
                    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                        vbox xfill True spacing 2 yoffset 4:
                            for i, sc in enumerate(vns.project.get('scenes', [])):
                                use vn_scene_row(sc, i)

            ## Scene detail / flow view (right)
            frame background Solid(VN_BG0) xfill True yfill True padding (28, 24):
                if vns.scene_id and vns.scene:
                    $ sc = vns.scene
                    vbox spacing 20 xfill True:
                        ## Scene header
                        hbox xfill True yalign 0.5:
                            vbox spacing 4 yalign 0.5:
                                text sc.get('label', '') style "vn_t_head"
                                text f"{len(sc.get('events',[]))} event(s)" style "vn_t_dim"
                                
                            null xfill True
                            
                            textbutton "🎯 Go To Node" style "vn_btn_ghost" yalign 0.5:
                                action [SetField(vng, 'selected_id', sc['id']), Function(vng.center_on_node, sc['id']), Function(vns.go, "graph")]
                            textbutton "➡️ Enter Scene" style "vn_btn_accent" yalign 0.5:
                                action Function(vns.go, "scene_editor")

                        ## Background
                        use vn_inspector_section("BACKGROUND & MUSIC", "sc_bg", "_vn_scenes_bg", sc)

                        ## Events summary
                        use vn_inspector_section("EVENTS PREVIEW", "sc_prev", "_vn_scenes_preview", sc)
                else:
                    vbox xalign 0.5 yalign 0.5 spacing 12:
                        text "🖱️ Select a scene" style "vn_t_dim" xalign 0.5
                        text "or create a new one" style "vn_t_faint" xalign 0.5

screen _vn_scenes_bg(sc):
    frame background None padding (10, 10):
        hbox spacing 16 yalign 0.0:
            vbox spacing 6:
                text "Background" style "vn_t_label"
                if sc.get('bg'):
                    frame background Solid(VN_BG3) xsize 220 ysize 130 padding (4, 4):
                        add sc['bg'] xsize 212 ysize 122 fit "cover" xalign 0.5 yalign 0.5
                else:
                    frame background Solid(VN_BG3) xsize 220 ysize 130 padding (0,0):
                        text "No background" style "vn_t_faint" xalign 0.5 yalign 0.5
                hbox spacing 6:
                    textbutton "Choose…" style "vn_btn_ghost":
                        action Show("vn_bg_gallery_modal", sc=sc)
                    if sc.get('bg'):
                        textbutton "o-" style "vn_btn_ghost":
                            action [
                                SetDict(sc, 'bg', None),
                                Function(vns.save),
                            ]
            vbox spacing 6:
                text "Music" style "vn_t_label"
                frame background Solid(VN_BG3) padding (12, 8):
                    xsize 200
                    if sc.get('music'):
                        text sc['music'].split('/')[-1] style "vn_t_dim" size 13
                    else:
                        text "No music" style "vn_t_faint" size 13
                hbox spacing 6:
                    textbutton "Choose…" style "vn_btn_ghost":
                        action [
                            SetField(vns, "asset_mode", "audio"),
                            SetField(vns, "asset_path", "audio"),
                            Function(_vn_pick_music, sc),
                            Function(vns.go, "assets"),
                        ]
                    if sc.get('music'):
                        textbutton "o-" style "vn_btn_ghost":
                            action [SetDict(sc, 'music', None), Function(vns.save)]

init python:
    import os
    def _vn_get_bg_assets(sort_mode="oldest_first"):
        dir_path = os.path.join(renpy.config.basedir, "game", "images", "place")
        result = []
        if os.path.exists(dir_path):
            ## To prevent PermissionError, check if it's a file
            for f in os.listdir(dir_path):
                full_path = os.path.join(dir_path, f)
                if not os.path.isfile(full_path):
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext in {'.jpg', '.png', '.webp', '.gif', '.mp4', '.webm'}:
                    mtime = os.path.getmtime(full_path)
                    result.append({"file": f, "path": "images/place/" + f, "ext": ext, "mtime": mtime})
                    
        if sort_mode == "oldest_first":
            result.sort(key=lambda x: x["mtime"])
        elif sort_mode == "newest_first":
            result.sort(key=lambda x: x["mtime"], reverse=True)
        elif sort_mode == "a_z":
            result.sort(key=lambda x: x["file"].lower())
        elif sort_mode == "z_a":
            result.sort(key=lambda x: x["file"].lower(), reverse=True)
            
        return result

transform _vn_gallery_pop:
    alpha 0.0 zoom 0.95
    easein 0.15 alpha 1.0 zoom 1.0

screen vn_bg_gallery_modal(sc):
    zorder 200
    modal True
    
    key "K_ESCAPE" action Hide("vn_bg_gallery_modal")
    
    default sort_mode = "oldest_first"
    default filter_mode = "all"
    default filter_slider = 100
    
    python:
        all_assets = _vn_get_bg_assets(sort_mode)
        
        if filter_mode == "images":
            type_assets = [a for a in all_assets if a['ext'] in {'.jpg', '.png', '.webp'}]
        elif filter_mode == "videos":
            type_assets = [a for a in all_assets if a['ext'] in {'.mp4', '.webm'}]
        elif filter_mode == "gifs":
            type_assets = [a for a in all_assets if a['ext'] == '.gif']
        else:
            type_assets = all_assets
            
        if type_assets:
            min_ts = min(a['mtime'] for a in type_assets)
            max_ts = max(a['mtime'] for a in type_assets)
            if max_ts == min_ts:
                cutoff_ts = max_ts
            else:
                cutoff_ts = min_ts + (max_ts - min_ts) * (filter_slider / 100.0)
                
            assets = [a for a in type_assets if a['mtime'] <= cutoff_ts]
            import datetime
            cutoff_year = datetime.datetime.fromtimestamp(cutoff_ts).year 
        else:
            assets = []
            cutoff_year = 2026
            
    frame background Solid("#000000dd") xfill True yfill True:
        ## Close via background click
        button action Hide("vn_bg_gallery_modal") xfill True yfill True background None
        
        frame background Solid(VN_BG0) xalign 0.5 yalign 0.5 xsize 1000 ysize 640 padding (0,0) at _vn_gallery_pop:
            hbox xfill True yfill True spacing 0:
                ## Left panel
                frame background Solid(VN_BG1) xsize 220 yfill True padding (20,20):
                    vbox spacing 12 xfill True:
                        text "ASSETS" style "vn_t_head" size 18
                        frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)
                        
                        textbutton "All Formats" style "vn_btn":
                            selected filter_mode == "all"
                            action SetScreenVariable("filter_mode", "all")
                        textbutton "PNG / Images" style "vn_btn":
                            selected filter_mode == "images"
                            action SetScreenVariable("filter_mode", "images")
                        textbutton "MP4 / Videos" style "vn_btn":
                            selected filter_mode == "videos"
                            action SetScreenVariable("filter_mode", "videos")
                        textbutton "GIF / Animated" style "vn_btn":
                            selected filter_mode == "gifs"
                            action SetScreenVariable("filter_mode", "gifs")

                        null height 16
                        text "TIME FILTER" style "vn_t_head" size 14
                        frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)
                        
                        text "Show assets up to:" style "vn_t_label" size 12
                        text f"{cutoff_year}" style "vn_t_head" size 24 color VN_ACC
                        
                        bar value ScreenVariableValue("filter_slider", 100) xfill True ysize 14

                frame background Solid(VN_BDR) xsize 1 yfill True padding (0,0)
                
                ## Right Panel
                frame background None xfill True yfill True padding (20, 20):
                    vbox xfill True yfill True spacing 16:
                        hbox xfill True yalign 0.5:
                            text "Set Background" style "vn_t_label" size 20 yalign 0.5
                            null xfill True
                        
                            text "Sort by" style "vn_t_faint" yalign 0.5 
                        
                            ## Sort buttons
                            textbutton "Oldest" style ("vn_btn_accent" if sort_mode == "oldest_first" else "vn_btn_ghost") action SetScreenVariable("sort_mode", "oldest_first")
                            textbutton "Newest" style ("vn_btn_accent" if sort_mode == "newest_first" else "vn_btn_ghost") action SetScreenVariable("sort_mode", "newest_first")
                            textbutton "A - Z" style ("vn_btn_accent" if sort_mode == "a_z" else "vn_btn_ghost") action SetScreenVariable("sort_mode", "a_z")
                            textbutton "Z - A" style ("vn_btn_accent" if sort_mode == "z_a" else "vn_btn_ghost") action SetScreenVariable("sort_mode", "z_a")
                        
                            null width 16
                            textbutton "❌" style "vn_btn_danger" action Hide("vn_bg_gallery_modal") yalign 0.5
                        
                        viewport xfill True yfill True mousewheel True scrollbars "vertical" style_prefix "vn_vscroll":
                            if not assets:
                                text "No matching assets found in game/images/place/" style "vn_t_dim" xalign 0.5 yalign 0.5
                            else:
                                vpgrid cols 3 spacing 16 xfill True:
                                    for a in assets:
                                        button xsize 230 ysize 180 padding (10,10):
                                            background Solid(VN_BG2)
                                            hover_background Solid(VN_HOVER)
                                            action [
                                                SetDict(sc, 'bg', a['path']),
                                                Function(vns.save),
                                                Hide("vn_bg_gallery_modal"),
                                                Function(renpy.restart_interaction)
                                            ]
                                            vbox xfill True yfill True spacing 6:
                                                fixed xsize 210 ysize 118 xalign 0.5:
                                                    add Transform(Solid("#000000"), xysize=(210, 118), blur=15, alpha=0.6)
                                                    if a['ext'] in {'.mp4', '.webm'}:
                                                        add Movie(play=a['path'], size=(210, 118))
                                                    else:
                                                        add Transform(a['path'], fit="contain", xysize=(210, 118))
                                            
                                                text a['file'][:24] style "vn_t" size 12 xalign 0.5
                                            
                                                python:
                                                    import datetime
                                                    _dt = datetime.datetime.fromtimestamp(a['mtime'])
                                                    _ds = _dt.strftime("%Y-%m-%d")
                                                text _ds style "vn_t_faint" size 11 xalign 0.5

screen _vn_scenes_preview(sc):
    frame style "vn_fr_card" xfill True:
        vbox spacing 8:
            if not sc.get('events'):
                text "No events yet. Click 'Enter Scene' to begin." style "vn_t_faint"
            else:
                for ev in sc['events'][:6]:
                    use vn_event_mini(ev)
                if len(sc['events']) > 6:
                    text f"⋯ and {len(sc['events'])-6} more" style "vn_t_faint"

screen vn_scene_row(sc, i):
    default confirm_del = False

    button xfill True style "vn_btn_nav":
        selected vns.scene_id == sc['id']
        action SetField(vns, "scene_id", sc['id'])

        hbox xfill True spacing 8:
            vbox xfill True yalign 0.5:
                text sc.get('label', '?') style "vn_t" size 15 yalign 0.5
                $ n = len(sc.get('events', []))
                text f"{n} event{'s' if n != 1 else ''}" style "vn_t_faint" size 12
            ## Reorder arrows
            $ _si_idx = vns.project['scenes'].index(sc) if sc in vns.project['scenes'] else 0
            $ _si_max = len(vns.project['scenes']) - 1
            hbox spacing 2 yalign 0.5:
                textbutton "\u25b2" style "vn_btn_icon" yalign 0.5:
                    action Function(_vn_move_scene, _si_idx, -1)
                    sensitive _si_idx > 0
                    padding (4, 2) text_size 10 text_color "#5577aa"
                textbutton "\u25bc" style "vn_btn_icon" yalign 0.5:
                    action Function(_vn_move_scene, _si_idx, 1)
                    sensitive _si_idx < _si_max
                    padding (4, 2) text_size 10 text_color "#5577aa"
            ## Star = set as start scene
            if vns.project.get('start') == sc['id']:
                text "\u2b50" size 14 yalign 0.5
            else:
                textbutton "\u25cb" style "vn_btn_icon" yalign 0.5:
                    action Function(_vn_set_start_scene, sc['id'])
                    padding (4, 2) text_size 11 text_color "#335577"
                    tooltip "Set as start scene"
            if not confirm_del:
                textbutton "🗑️" style "vn_btn_icon" yalign 0.5:
                    action ToggleLocalVariable("confirm_del")
            else:
                hbox spacing 4 yalign 0.5:
                    textbutton "✅" style "vn_btn_danger" padding (6,4):
                        action [
                            Function(_vn_delete_scene_undo, sc),
                            ToggleLocalVariable("confirm_del"),
                        ]
                    textbutton "❌" style "vn_btn_ghost" padding (6,4):
                        action ToggleLocalVariable("confirm_del")

screen vn_event_mini(ev):
    $ t = ev.get('type', '')
    $ icons = {"dialogue":"💬","choice":"❓","effect":"✨","jump":"➡","wait":"⏱","narration":"📝"}
    frame background Solid(VN_BG2) padding (8, 6) xfill True:
        hbox spacing 10:
            text icons.get(t, '?') size 16 yalign 0.5
            if t == 'dialogue':
                $ txt = ev.get('text','')[:60] + ('?' if len(ev.get('text',''))>60 else '')
                text txt style "vn_t" size 13 yalign 0.5
            elif t == 'choice':
                text f"Choice: {ev.get('prompt','')[:40]}" style "vn_t_dim" size 13 yalign 0.5
            elif t == 'narration':
                $ txt = ev.get('text','')[:60] + ('?' if len(ev.get('text',''))>60 else '')
                text txt style "vn_t_dim" size 13 yalign 0.5
            else:
                text f"{t.title()}" style "vn_t_dim" size 13 yalign 0.5

init python:
    def _vn_pick_bg(sc):
        def cb(path):
            sc['bg'] = path
            vns.save()
            vns.go("scenes")
            vns.notify("Background set!", "ok")
        vns.asset_cb = cb

    def _vn_pick_music(sc):
        def cb(path):
            sc['music'] = path
            vns.save()
            vns.go("scenes")
            vns.notify("Music set!", "ok")
        vns.asset_cb = cb

    def _vn_duplicate_event(sc, ev_id):
        if not sc or not ev_id: return
        import copy
        ev = vn_find_event(sc, ev_id)
        if not ev: return
        
        idx = sc['events'].index(ev)
        new_ev = copy.deepcopy(ev)
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        new_ev['id'] = f"{new_ev['type']}_{suffix}"
        
        def _do():
            sc['events'].insert(idx + 1, new_ev)
            vns.event_id = new_ev['id']
            vns.save()
            renpy.restart_interaction()
            
        def _undo():
            sc['events'].remove(new_ev)
            vns.event_id = ev_id
            vns.save()
            renpy.restart_interaction()
            
        vns.history.commit("Duplicate Event", _do, _undo)

## "?"? Dialogue Editor Panel "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?

screen vn_dialogue_panel():
    default show_add_menu = False

    if not vns.scene:
        frame background Solid(VN_BG0) xfill True yfill True:
            vbox xalign 0.5 yalign 0.5 spacing 10:
                text "No scene selected." style "vn_t_dim" xalign 0.5
                textbutton "⬅️ Back to Scenes" style "vn_btn_ghost":
                    action Function(vns.go, "scenes")
    else:
        $ sc = vns.scene
        
        ## Editor shortcuts
        key "ctrl_K_d" action Function(_vn_duplicate_event, sc, vns.event_id)
        key "ctrl_K_n" action [Function(_vn_add_event, sc, vn_new_dialogue)]

        frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
            vbox spacing 0 xfill True yfill True:
                ## Dialogue toolbar
                frame background Solid(VN_BG1) xfill True padding (14, 10):
                    hbox xfill True spacing 10 yalign 0.5:
                        textbutton "🎬 Scenes" style "vn_btn_ghost" yalign 0.5:
                            action Function(vns.go, "scenes")
                        frame background Solid(VN_BDR) xsize 1 ysize 34 yalign 0.5
                        text sc.get('label', '') style "vn_t_sub" yalign 0.5
                        null xfill True
                        textbutton "+ Add Event" style "vn_btn_accent" yalign 0.5:
                            action ToggleLocalVariable("show_add_menu")

                ## Add event menu
                if show_add_menu:
                    frame background Solid(VN_BG2) xfill True padding (14, 10):
                        hbox spacing 10:
                            text "Add:" style "vn_t_label" yalign 0.5
                            for lbl, fn in [
                                ("💬 Dialogue",   lambda: vn_new_dialogue()),
                                ("📝 Narration",  lambda: vn_new_narration()),
                                ("❓ Choice",     lambda: vn_new_choice()),
                                ("✨ Effect",     lambda: vn_new_effect()),
                                ("➡️ Jump",       lambda: vn_new_jump()),
                                ("⏱️ Wait",       lambda: vn_new_wait()),
                            ]:
                                textbutton lbl style "vn_btn_ghost":
                                    action [
                                        Function(_vn_add_event, sc, fn),
                                        ToggleLocalVariable("show_add_menu"),
                                    ]

                ## Event list + inspector
                hbox spacing 0 xfill True yfill True:
                    ## Event list
                    frame background Solid(VN_BG1) xsize 440 yfill True padding (0, 0):
                        vbox spacing 0 xfill True yfill True:
                            ## Quick Stats / Search Toolbar
                            frame background Solid(VN_BG2) xfill True padding (12, 10):
                                hbox spacing 8 yalign 0.5 xfill True:
                                    text f"{len(sc.get('events',[]))} Events" style "vn_t_dim" size 14 yalign 0.5
                                    null xfill True
                                    hbox spacing 6 yalign 0.5:
                                        text "🔍" size 14 yalign 0.5
                                        if vns.ui.get('_focus') == "vn_dialogue_search_input":
                                            button style "vn_fr_input" xsize 160:
                                                action NullAction()
                                                input id "vn_dialogue_search_input" style "vn_input" value DictInputValue(vns.ui, 'dialogue_search') length 60 size 14
                                        else:
                                            $ _fv = vns.ui.get('dialogue_search', '') or ''
                                            button style "vn_fr_input" xsize 160:
                                                action [SetDict(vns.ui, '_focus', "vn_dialogue_search_input"), Function(renpy.set_focus, None, "vn_dialogue_search_input")]
                                                text (_fv if _fv else "Search…") style "vn_input" color (VN_FAINT if not _fv else VN_TEXT) size 14

                            ## Drag hint
                            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)
                            frame background None xfill True padding (12, 6):
                                text "↕️. Drag row to reorder" style "vn_t_faint" size 12 xalign 0.5

                            ## List viewport
                            viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                                vbox xfill True spacing 2 yoffset 4:
                                    $ _q = vns.ui.get('dialogue_search', '').lower()
                                    for i, ev in enumerate(sc.get('events', [])):
                                        if not _q or _q in ev.get('text', '').lower() or _q in ev.get('prompt', '').lower():
                                            use vn_event_row(sc, ev, i)
                                    if not sc.get('events'):
                                        frame background None xfill True padding (20, 30):
                                            text "No events yet.\nClick '+ Add Event' above." style "vn_t_faint" xalign 0.5

                    ## Live preview + inspector
                    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
                        vbox xfill True yfill True spacing 0:
                            ## Preview strip
                            use vn_preview_strip(sc)
                            ## Inspector
                            viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                                vbox xfill True spacing 0:
                                    frame background Solid(VN_BG1) xfill True padding (20, 16):
                                        if vns.event_id and vn_find_event(sc, vns.event_id):
                                            $ ev = vn_find_event(sc, vns.event_id)
                                            use vn_inspector_section("EVENT PROPERTIES", "props_ev", "_vn_insp_wrapper", ev, sc)
                                        else:
                                            text "🖱️ Select an event to edit" style "vn_t_faint" xalign 0.5 yalign 0.5

screen vn_event_row(sc, ev, i):
    $ icons = {"dialogue":"💬","choice":"❓","effect":"✨","jump":"➡","wait":"⏱","narration":"📝"}
    $ t = ev.get('type','')

    button xfill True style "vn_btn":
        selected vns.event_id == ev['id']
        action SetField(vns, "event_id", ev['id'])
        padding (10, 8)

        hbox xfill True spacing 8:
            ## index
            frame background Solid(VN_BG2) xsize 28 ysize 28 padding (0,0):
                text str(i+1) style "vn_t_faint" size 12 xalign 0.5 yalign 0.5
            text icons.get(t, '?') size 18 yalign 0.5
            vbox xfill True yalign 0.5:
                if t == 'dialogue':
                    $ char = vn_find_char(vns.project, ev.get('char_id'))
                    text (char['display'] if char else "Narrator") style "vn_t" size 13 color (char['color'] if char else VN_DIM)
                    text ev.get('text','')[:50] style "vn_t_faint" size 12
                elif t == 'narration':
                    text "Narration" style "vn_t_dim" size 13
                    text ev.get('text','')[:50] style "vn_t_faint" size 12
                elif t == 'choice':
                    text "Choice" style "vn_t_dim" size 13
                    text f"{len(ev.get('opts',[]))} options" style "vn_t_faint" size 12
                else:
                    text t.title() style "vn_t_dim" size 13

            ## Move up/down
            vbox yalign 0.5 spacing 2:
                if i > 0:
                    textbutton "▲" style "vn_btn_icon" padding (4,2):
                        action Function(_vn_move_ev, sc, i, -1)
                if i < len(sc.get('events',[])) - 1:
                    textbutton "▼" style "vn_btn_icon" padding (4,2):
                        action Function(_vn_move_ev, sc, i, 1)
            textbutton "🗑️" style "vn_btn_icon" yalign 0.5:
                action Function(_vn_delete_event_undo, sc, ev)

screen vn_preview_strip(sc):
    $ ev = vn_find_event(sc, vns.event_id) if vns.event_id else None
    frame background (sc['bg'] if sc.get('bg') else Solid("#050708")) xfill True ysize 200 padding (0,0):
        
        if not sc.get('bg'):
            text "PREVIEW LAYER" style "vn_t_dim" size 12 italic True xalign 0.5 yalign 0.5

        ## Character sprite (layered on top via fixed)
        if ev and ev.get('type') == 'dialogue' and ev.get('char_id'):
            $ char = vn_find_char(vns.project, ev.get('char_id'))
            $ spr  = vn_char_sprite(vns.project, ev['char_id'], ev.get('pose','neutral'))
            $ side = ev.get('side','center')
            if char and spr:
                add spr:
                    yalign 1.0
                    xalign {"left": 0.15, "center": 0.5, "right": 0.85}.get(side, 0.5)
                    zoom 0.35

        ## Dialogue box overlay
        if ev:
            frame background Solid("#000000bb") xfill True yalign 1.0 padding (20, 14):
                vbox spacing 6:
                    if ev.get('type') == 'dialogue':
                        $ char = vn_find_char(vns.project, ev.get('char_id'))
                        if char:
                            text char['display'] style "vn_t" font VN_FONTB size 15 color char['color']
                        text ev.get('text','?') style "vn_t" size 15
                    elif ev.get('type') == 'narration':
                        text ev.get('text','?') style "vn_t_dim" size 15 italic True
                    elif ev.get('type') == 'choice':
                        text ev.get('prompt','(Choice)') style "vn_t_dim" size 13
                        for o in ev.get('opts',[]):
                            text f"  - {o.get('text','')}" style "vn_t" size 13 color VN_TEAL
                    else:
                        text f"[{ev.get('type','?').upper()}]" style "vn_t_faint" size 13

