## ───────────────────────────────────────────────
##  VN Maker - Event Inspector Panel
## ───────────────────────────────────────────────

screen _vn_insp_wrapper(ev, sc):
    use vn_event_inspector(ev, sc)

screen vn_event_inspector(ev, sc):
    $ t = ev.get('type', '')
    vbox spacing 16 xfill True:
        if t in ('dialogue', 'narration', 'effect'):
            vbox spacing 6 xfill True:
                text "Event Type:" style "vn_t_sub"
                hbox spacing 8 box_wrap True xfill True:
                    textbutton "Dialogue" style "vn_btn":
                        selected t == 'dialogue'
                        action [SetDict(ev, 'type', 'dialogue'), Function(vns.save)]
                    textbutton "Narration" style "vn_btn":
                        selected t == 'narration'
                        action [SetDict(ev, 'type', 'narration'), SetDict(ev, 'char_id', None), Function(vns.save)]
                    textbutton "Effect" style "vn_btn":
                        selected t == 'effect'
                        action [SetDict(ev, 'type', 'effect'), Function(vns.save)]
        elif t in ('image', 'bg'):
            vbox spacing 6 xfill True:
                text "Event Type:" style "vn_t_sub"
                hbox spacing 8 box_wrap True xfill True:
                    textbutton "Background" style "vn_btn":
                        selected t == 'bg'
                        action [SetDict(ev, 'type', 'bg'), Function(vns.save)]
                    textbutton "Image" style "vn_btn":
                        selected t == 'image'
                        action [SetDict(ev, 'type', 'image'), Function(vns.save)]
        elif t in ('setvar', 'if'):
            vbox spacing 6 xfill True:
                text "Event Type:" style "vn_t_sub"
                hbox spacing 8 xfill True:
                    textbutton "Variable" style "vn_btn":
                        selected t == 'setvar'
                        action [SetDict(ev, 'type', 'setvar'), Function(vns.save)]
                    textbutton "Logic If" style "vn_btn":
                        selected t == 'if'
                        action [SetDict(ev, 'type', 'if'), Function(vns.save)]
        else:
            text f"Edit: {t.title()}" style "vn_t_sub"

        if t == 'dialogue':
            use vn_insp_dialogue(ev)
        elif t == 'narration':
            use vn_insp_narration(ev)
        elif t == 'choice':
            use vn_insp_choice(ev, sc)
        elif t == 'menu':
            use vn_insp_menu(ev, sc)
        elif t == 'effect':
            use vn_insp_effect(ev)
        elif t == 'jump':
            use vn_insp_jump(ev)
        elif t == 'wait':
            use vn_insp_wait(ev)
        elif t in ('music', 'sfx'):
            use vn_insp_audio(ev)
        elif t in ('image', 'bg'):
            use vn_insp_image(ev)
        elif t == 'setvar':
            use vn_insp_setvar(ev)
        elif t == 'if':
            use vn_insp_if(ev, sc)

        textbutton "Y' Apply" style "vn_btn_teal":
            action [
                Function(lambda: store.vns.ui['_live_ed'].commit_history() if store.vns.ui.get('_live_ed') else None),
                Function(lambda: store.vns.ui['_dlg_ed'].commit_history() if store.vns.ui.get('_dlg_ed') else None),
                SetDict(store.vns.ui, '_ted_focused', False),
                SetDict(store.vns.ui, '_ted_live_focused', False),
                Function(vns.save)
            ]

## "?"? Dialogue inspector "?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?"?

screen vn_insp_dialogue(ev):
    vbox spacing 14 xfill True:
        ## Speaker
        vbox spacing 6 xfill True:
            text "Speaker" style "vn_t_label"
            hbox spacing 8 box_wrap True xfill True:
                ## Narrator
                textbutton "Narrator" style "vn_btn":
                    selected ev.get('char_id') is None
                    action [SetDict(ev, 'char_id', None), Function(vns.save)]
                for c in vns.project.get('characters', []):
                    button style "vn_btn" padding (10, 8):
                        selected ev.get('char_id') == c['id']
                        action [SetDict(ev, 'char_id', c['id']), Function(vns.save)]
                        text c['display'] style "vn_t" size 14 color c['color']

        ## Pose
        if ev.get('char_id'):
            $ _char = vn_find_char(vns.project, ev.get('char_id'))
            $ _poses = _char.get('poses', VN_POSES) if _char else VN_POSES
            vbox spacing 6 xfill True:
                text "Pose" style "vn_t_label"
                hbox spacing 6 box_wrap True xfill True:
                    for pose in _poses:
                        textbutton pose style "vn_btn":
                            selected ev.get('pose') == pose
                            action [SetDict(ev, 'pose', pose), Function(vns.save)]
                            text_size 13

        ## Position
        vbox spacing 6 xfill True:
            text "Position" style "vn_t_label"
            hbox spacing 8 box_wrap True xfill True:
                for side in VN_SIDES:
                    textbutton side.title() style "vn_btn":
                        selected ev.get('side') == side
                        action [SetDict(ev, 'side', side), Function(vns.save)]

        ## Dialogue text ?" multi-line editor
        vbox spacing 6:
            text "Dialogue Text" style "vn_t_label"
            $ _dlg_ed = vns.ui.get('_dlg_ed')
            if not _dlg_ed or _dlg_ed.ev.get('id') != ev.get('id'):
                if _dlg_ed:
                    $ _dlg_ed.commit_history()
                $ _dlg_ed = store.VNTextEditor(ev, 'text')
                $ vns.ui['_dlg_ed'] = _dlg_ed
            use vn_texteditor(_dlg_ed)

## ── Audio Data inspector ──────────────────────────────────────────────────

screen vn_insp_audio(ev):
    $ _atype = ev.get('type', 'music')
    $ _ = vns.ui.setdefault('aud_search', '')
    vbox spacing 10 xfill True:
        text "Select Audio File" style "vn_t_label"

        ## Current selection display
        $ _cur_audio = ev.get(_atype, "")
        if _cur_audio:
            frame background Solid("#0a1e10") xfill True padding (10, 8):
                hbox spacing 8 yalign 0.5:
                    text "🎵" size 14 yalign 0.5
                    vbox yalign 0.5 xfill True spacing 1:
                        text _cur_audio.split('/')[-1] style "vn_t" size 11 bold True color "#44cc88"
                        text _cur_audio style "vn_t" size 9 color "#334455"
                    textbutton "■ Stop" style "vn_btn_ghost" padding (6, 3):
                        action Function(renpy.music.stop, channel="preview")
                        text_size 10
        else:
            frame background Solid("#0a0e16") xfill True padding (10, 8):
                text "No file selected" style "vn_t_faint" size 11

        ## Search - backed by vns.ui so it works in use'd screens
        hbox spacing 6 xfill True:
            text "🔍" size 13 yalign 0.5
            frame background Solid("#0a1020") xfill True padding (6, 4):
                input id "vn_aud_search" value DictInputValue(vns.ui, 'aud_search') length 80 size 12 style "vn_input" color "#aabbcc"

        ## Clear
        textbutton "✕ Clear" style "vn_btn_ghost" padding (8, 4):
            action [SetDict(ev, _atype, ""), SetDict(vns.ui, 'aud_search', ''), Function(renpy.music.stop, channel="preview"), Function(vns.save)]
            text_size 11

        ## File list with play button
        $ _adq = vns.ui.get('aud_search', '')
        $ _alist = [f for f in _vn_list_audio() if _adq.lower() in f.lower()] if _adq else _vn_list_audio()
        if not _alist:
            text "No audio files found." style "vn_t_faint" size 12
        else:
            viewport xfill True ysize 260 scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                vbox spacing 1 xfill True:
                    for _af in _alist:
                        $ _afn = _af.split('/')[-1]
                        $ _af_sel = ev.get(_atype) == _af
                        hbox spacing 0 xfill True:
                            ## ▶ Play button
                            button xsize 28 yfill True padding (0,0):
                                background Solid("#0a1e0a" if _af_sel else "#06090f")
                                hover_background Solid("#1a441a")
                                action Function(renpy.music.play, _af, channel="preview")
                                text "▶" size 11 color "#44cc44" xalign 0.5 yalign 0.5
                            ## Filename button — click to assign
                            button xfill True yfill True padding (8, 5):
                                background Solid("#0e2218" if _af_sel else "#05090f")
                                hover_background Solid("#122818")
                                action [SetDict(ev, _atype, _af), Function(vns.save)]
                                hbox spacing 0 xfill True:
                                    if _af_sel:
                                        text "✓ " style "vn_t" size 11 color "#44cc88" yalign 0.5
                                    text _afn style "vn_t" size 11 color ("#44cc88" if _af_sel else "#88aabb") yalign 0.5

## ── Image Data inspector ──────────────────────────────────────────────────

screen vn_insp_image(ev):
    $ _itype = ev.get('type', 'image')
    $ _ = vns.ui.setdefault('img_search', '')
    $ _ = vns.ui.setdefault('img_hov', '')
    vbox spacing 10 xfill True:
        text "Select Image" style "vn_t_label"

        ## Live preview of hovered or selected image
        $ _prev_path = vns.ui.get('img_hov') or ev.get(_itype, "")
        if _prev_path:
            frame background Solid("#050810") xfill True ysize 110 padding (2, 2):
                fixed xfill True yfill True:
                    add Transform(_prev_path, fit="contain", align=(0.5, 0.5))
        else:
            frame background Solid("#050810") xfill True ysize 60 padding (10, 0):
                text "Hover an image to preview" style "vn_t_faint" size 11 xalign 0.5 yalign 0.5

        ## Current selection name
        $ _cur_img = ev.get(_itype, "")
        if _cur_img:
            text _cur_img.split('/')[-1] style "vn_t" size 10 color "#8899cc"

        ## Search - backed by vns.ui
        hbox spacing 6 xfill True:
            text "🔍" size 13 yalign 0.5
            frame background Solid("#0a1020") xfill True padding (6, 4):
                input id "vn_img_search" value DictInputValue(vns.ui, 'img_search') length 80 size 12 style "vn_input" color "#aabbcc"

        ## Clear button
        textbutton "✕ Clear" style "vn_btn_ghost" padding (8, 4):
            action [SetDict(ev, _itype, ""), SetDict(vns.ui, 'img_search', ''), Function(vns.save)]
            text_size 11

        ## File list with hover preview
        $ _idq = vns.ui.get('img_search', '')
        $ _ilist = [f for f in _vn_list_images() if _idq.lower() in f.lower()] if _idq else _vn_list_images()
        if not _ilist:
            text "No image files found." style "vn_t_faint" size 12
        else:
            viewport xfill True ysize 220 scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                vbox spacing 1 xfill True:
                    for _imf in _ilist:
                        $ _imfn = _imf.split('/')[-1]
                        $ _imsel = ev.get(_itype) == _imf
                        button xfill True padding (8, 5):
                            background Solid("#0e1828" if _imsel else "#05090f")
                            hover_background Solid("#121e30")
                            action [SetDict(ev, _itype, _imf), Function(vns.save)]
                            hovered SetDict(vns.ui, 'img_hov', _imf)
                            unhovered SetDict(vns.ui, 'img_hov', '')
                            hbox spacing 4 xfill True:
                                if _imsel:
                                    text "✓ " style "vn_t" size 11 color "#4488ff" yalign 0.5
                                text _imfn style "vn_t" size 11 color ("#4488ff" if _imsel else "#667799") yalign 0.5



## ── Ren'Py Menu inspector ──────────────────────────────────────────────────

screen vn_insp_menu(ev, sc):
    $ ev.setdefault('opts', [])
    vbox spacing 12 xfill True:
        vbox spacing 6 xfill True:
            text "Prompt (optional)" style "vn_t_label"
            use vn_text_input(f"vn_menu_prompt_{ev.get('id', 'new')}", ev, "prompt", "(none)", 200, None, 40)

        vbox spacing 6:
            text "Menu Options" style "vn_t_label"
            for _oi, _o in enumerate(ev.get('opts', [])):
                hbox spacing 6 xfill True yalign 0.5:
                    text f"{_oi+1}." style "vn_t_dim" size 12 yalign 0.5 xsize 16
                    use vn_text_input(f"vn_menu_opt_{ev.get('id', 'new')}_{_oi}", _o, "text", "(empty)", 180, None, 40)
                    ## Jump target scene picker
                    button style "vn_btn" padding (6, 4):
                        action SetDict(_o, 'scene', None)
                        text "✕" size 11 color "#774444"

        ## Add option button
        textbutton "+ Add Option" style "vn_btn_ghost":
            action [Function(ev['opts'].append, {'id': str(renpy.random.randint(0,999999)), 'text': 'New Option', 'scene': None}), Function(vns.save)]

screen vn_insp_narration(ev):
    vbox spacing 6 xfill True:
        text "Narration Text" style "vn_t_label"
        $ _dlg_ed = vns.ui.get('_dlg_ed')
        if not _dlg_ed or _dlg_ed.ev.get('id') != ev.get('id'):
            if _dlg_ed:
                $ _dlg_ed.commit_history()
            $ _dlg_ed = store.VNTextEditor(ev, 'text')
            $ vns.ui['_dlg_ed'] = _dlg_ed
        use vn_texteditor(_dlg_ed)

screen vn_insp_choice(ev, sc):
    $ ev.setdefault('opts', [])
    vbox spacing 12 xfill True:
        vbox spacing 6:
            text "Prompt (optional)" style "vn_t_label"
            use vn_text_input(f"vn_choice_prompt_{ev.get('id', 'new')}", ev, "prompt", "Choice prompt...", 180, None, 40)

        text "Options" style "vn_t_label"
        for opt in ev.get('opts', []):
            frame style "vn_fr_card" xfill True:
                hbox spacing 12 xfill True:
                    vbox xfill True spacing 6:
                        use vn_text_input(f"vn_choice_opt_{opt['id']}", opt, "text", "Option text...", 180, None, 40)
                        ## scene target
                        hbox spacing 8 box_wrap True xfill True:
                            text "➡️" style "vn_t_faint" yalign 0.5
                            textbutton "(no target)" style "vn_btn_ghost":
                                selected opt.get('scene') is None
                                action SetDict(opt, 'scene', None)
                            for ts in vns.project.get('scenes', []):
                                textbutton ts['label'] style "vn_btn_ghost":
                                    selected opt.get('scene') == ts['id']
                                    action SetDict(opt, 'scene', ts['id'])
                    textbutton "o-" style "vn_btn_icon" yalign 0.5:
                        action Function(ev['opts'].remove, opt)

        textbutton "+ Add Option" style "vn_btn_ghost":
            action Function(ev['opts'].append,
                            {'id': str(renpy.random.Random().random()), 'text': 'Option', 'scene': None})

screen vn_insp_effect(ev):
    vbox spacing 12 xfill True:
        vbox spacing 6 xfill True:
            text "Dialogue Text (Optional)" style "vn_t_label"
            $ _dlg_ed = vns.ui.get('_dlg_ed')
            if not _dlg_ed or _dlg_ed.ev.get('id') != ev.get('id'):
                if _dlg_ed:
                    $ _dlg_ed.commit_history()
                $ _dlg_ed = store.VNTextEditor(ev, 'text')
                $ vns.ui['_dlg_ed'] = _dlg_ed
            use vn_texteditor(_dlg_ed)

        text "Effect Type" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            for eff in VN_EFFECTS:
                textbutton eff style "vn_btn":
                    selected ev.get('kind') == eff
                    action [SetDict(ev, 'kind', eff), Function(vns.save)]
        text "Duration (seconds)" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            for d in [0.2, 0.5, 1.0, 1.5, 2.0]:
                textbutton str(d) + "s" style "vn_btn":
                    selected ev.get('dur') == d
                    action [SetDict(ev, 'dur', d), Function(vns.save)]

screen vn_insp_jump(ev):
    vbox spacing 12 xfill True:
        text "Jump to Scene" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            textbutton "(end)" style "vn_btn":
                selected ev.get('scene_id') is None
                action SetDict(ev, 'scene_id', None)
            for ts in vns.project.get('scenes', []):
                textbutton ts['label'] style "vn_btn":
                    selected ev.get('scene_id') == ts['id']
                    action SetDict(ev, 'scene_id', ts['id'])
        text "Transition" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            for tr in VN_TRANSITIONS:
                textbutton tr style "vn_btn":
                    selected ev.get('transition') == tr
                    action [SetDict(ev, 'transition', tr), Function(vns.save)]

screen vn_insp_wait(ev):
    vbox spacing 10 xfill True:
        text "Wait Duration" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            for d in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
                textbutton str(d) + "s" style "vn_btn":
                    selected ev.get('dur') == d
                    action [SetDict(ev, 'dur', d), Function(vns.save)]

screen vn_insp_setvar(ev):
    vbox spacing 12 xfill True:
        vbox spacing 6 xfill True:
            text "Variable Name" style "vn_t_label"
            use vn_text_input(f"vn_var_name_{ev.get('id', 'new')}", ev, "var_name", "book...", 200)
        vbox spacing 6 xfill True:
            text "Value Expression" style "vn_t_label"
            text "Python expression (e.g. True, False, 1, 'string')" style "vn_t_faint" size 11
            use vn_text_input(f"vn_var_val_{ev.get('id', 'new')}", ev, "var_val", "True...", 300)

screen vn_insp_if(ev, sc):
    vbox spacing 12 xfill True:
        vbox spacing 6 xfill True:
            text "Condition" style "vn_t_label"
            text "Python condition (e.g. book == True)" style "vn_t_faint" size 11
            use vn_text_input(f"vn_if_cond_{ev.get('id', 'new')}", ev, "condition", "book == True...", 300)
            
        text "True Target" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            textbutton "(no target)" style "vn_btn_ghost":
                selected ev.get('scene_true') is None
                action SetDict(ev, 'scene_true', None)
            for ts in vns.project.get('scenes', []):
                textbutton ts['label'] style "vn_btn_ghost":
                    selected ev.get('scene_true') == ts['id']
                    action [SetDict(ev, 'scene_true', ts['id']), Function(vns.save)]

        text "False Target" style "vn_t_label"
        hbox spacing 8 box_wrap True xfill True:
            textbutton "(no target)" style "vn_btn_ghost":
                selected ev.get('scene_false') is None
                action SetDict(ev, 'scene_false', None)
            for ts in vns.project.get('scenes', []):
                textbutton ts['label'] style "vn_btn_ghost":
                    selected ev.get('scene_false') == ts['id']
                    action [SetDict(ev, 'scene_false', ts['id']), Function(vns.save)]

