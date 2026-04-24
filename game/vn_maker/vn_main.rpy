## ???????????????????????????????????????????????
##  VN Maker ? Root Screen + Home Panel
## ???????????????????????????????????????????????
## ???????????????????????????????????????????????

init python:
    import sys
    import subprocess
    import re
    
    def _vns_play_external():
        """Launch the generated IDE project in a new detached window."""
        vn_compile_project(vns.project)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', vns.project.get('title', 'compiled_project')).lower()
        start_label = f"vns_build_{safe_name}_start"
        args = [sys.executable, sys.argv[0], renpy.config.basedir, "--warp", start_label]
        subprocess.Popen(args)

    def _vn_do_import():
        """Run the .rpy importer and open the resulting project on success."""
        ip = vns.import_proj
        folder = (ip.get('path') or '').strip()
        title  = (ip.get('title') or 'Imported Project').strip()
        author = (ip.get('author') or 'Author').strip()

        if not folder:
            vns.notify("Please enter a folder path to import from.", "err")
            return

        proj, warnings = vn_import_rpy(folder, title, author)

        if proj is None:
            ip['warnings'] = warnings
            vns.notify("Import failed — check the path.", "err")
            renpy.restart_interaction()
            return

        # Save and open
        vn_save(proj)
        ip['warnings'] = warnings
        ip['show'] = False
        vns.open_project(proj)
        vns.notify("Imported {} scenes!".format(len(proj['scenes'])), "ok")
        renpy.restart_interaction()


## ?? Entry label ??????????????????????????????????????????????????????????????

label vn_maker_entry:
    window hide
    python:
        vns.panel = "home"
        quick_menu = False
        renpy.hide_screen('quick_menu')
        ## Disable Ren'Py's built-in Ctrl-skip while the IDE is open
        _vn_prev_skipping  = config.allow_skipping
        config.allow_skipping = False
    call screen vn_maker_root
    python:
        quick_menu = True
        ## Restore skip settings when leaving the IDE
        config.allow_skipping = _vn_prev_skipping
    return

## ?? Root screen ??????????????????????????????????????????????????????????????

screen vn_maker_root():
    tag vn_root
    style_prefix "vn"
    zorder 100
    modal (not vns.ui.get('live_mode', False))

    ## Disable right-click opening the game menu
    key "game_menu" action NullAction()
    ## Block Ren'Py's skip overlay (triggered by holding Ctrl normally)
    key "skip"      action NullAction()

    ## Undo/Redo shortcuts
    key "ctrl_K_z" action Function(vns.history.undo)
    key "ctrl_K_y" action Function(vns.history.redo)
    key "ctrl_K_s" action Function(vns.save)

    frame style "vn_fr" background (None if vns.ui.get('live_mode') else Solid("#05080f")):
        ## Scene editor is full-screen (no sidebar)
        if vns.panel == "scene_editor":
            if not vns.ui.get('live_mode'):
                vbox spacing 0 xfill True yfill True:
                    use vn_toolbar
                    use vn_scene_editor
        else:
            vbox spacing 0:
                use vn_toolbar

                hbox spacing 0 xfill True yfill True:
                    use vn_sidebar

                    frame style "vn_fr":
                        background Solid(VN_BG0)
                        xfill True yfill True
                        padding (0, 0)

                        if vns.panel == "home":
                            use vn_home_panel
                        elif vns.panel == "hub":
                            use vn_hub_panel
                        elif vns.panel == "scenes":
                            use vn_scenes_panel
                        elif vns.panel == "dialogue":
                            use vn_dialogue_panel
                        elif vns.panel == "characters":
                            use vn_characters_panel
                        elif vns.panel == "assets":
                            use vn_assets_panel
                        elif vns.panel == "graph":
                            use vn_graph_panel
                        elif vns.panel == "player":
                            use vn_player_panel
                        elif vns.panel == "export":
                            use vn_export_panel
                        elif vns.panel == "settings":
                            use vn_settings_panel

    use vn_notifications
    use vn_tween_picker
    use vn_music_player

transform vn_anim_music_player:
    on show:
        yoffset 80 alpha 0.0
        easein 0.35 yoffset 0 alpha 1.0
    on hide:
        easeout 0.25 yoffset 80 alpha 0.0

init python:
    def vn_seek_music(delta):
        """
        Seek the music channel by +/- delta seconds.
        Strips any existing <from X> seek prefix from the filename so
        we never produce nested <from A><from B>file.mp3 strings.
        """
        import re
        raw      = renpy.music.get_playing("music") or ""
        filename = re.sub(r'^<from [0-9.]+>', '', raw)
        pos      = renpy.music.get_pos("music")      or 0.0
        dur      = renpy.music.get_duration("music") or 0.0
        target   = max(0.0, min(pos + delta, dur - 0.1))
        renpy.music.play("<from {:.2f}>{}".format(target, filename), channel="music", fadeout=0)

    def vn_playlist_nav(direction):
        """
        Skip to the previous (-1) or next (+1) audio file in the same
        folder as the currently playing track. Wraps around at both ends
        so pressing Next on the last track returns to the first.
        """
        import re
        AUDIO_EXT = (".mp3", ".ogg", ".wav", ".opus", ".flac")

        raw = renpy.music.get_playing("music") or ""
        cur = re.sub(r'^<from [0-9.]+>', '', raw)
        if not cur:
            return

        depth  = cur.count("/")
        folder = cur.rsplit("/", 1)[0] if "/" in cur else ""

        files = sorted([
            f for f in renpy.list_files()
            if f.startswith(folder + "/")
            and f.count("/") == depth
            and f.lower().endswith(AUDIO_EXT)
        ])

        if not files or cur not in files:
            return

        new_idx = (files.index(cur) + direction) % len(files)
        renpy.music.play(files[new_idx], channel="music", fadeout=0.4)

    ## ?? Music player position state ??????????????????????????????????????????
    ## Ren'Py's drag widget is reset by restart_interaction (fired by the
    ## 0.25 s timer), so we track position manually instead.

    _vn_ps = {
        "x": None, "y": None,          ## frame top-left on screen
        "grab": False,                  ## True while user is repositioning
        "ox": 0,  "oy": 0,             ## mouse-to-frame offset at grab start
    }

    def vn_player_snap(px, py):
        """Snap the player to one of 9 screen sectors."""
        w = 780
        h = 130
        pad_x = 20
        pad_y = 20
        min_x = pad_x
        max_x = config.screen_width - w - pad_x
        min_y = pad_y
        max_y = config.screen_height - h - pad_y
        
        cx = (min_x + max_x) // 2
        cy = (min_y + max_y) // 2
        
        if px == 0: nx = min_x
        elif px == 1: nx = cx
        else: nx = max_x
        
        if py == 0: ny = min_y
        elif py == 1: ny = cy
        else: ny = max_y
        
        _vn_ps["x"] = nx
        _vn_ps["y"] = ny
        renpy.restart_interaction()

screen vn_music_player():
    default vn_tick = False
    ## AudioPositionValue created ONCE so scrubber state survives re-renders
    default vn_apv = AudioPositionValue(channel="music")
    $ cur_track = renpy.music.get_playing("music")
    if cur_track:
        $ track_name = cur_track.split("/")[-1]
        $ track_short = (track_name[:40] + ".") if len(track_name) > 40 else track_name
        $ is_paused = renpy.music.get_pause("music")
        $ pos = renpy.music.get_pos("music") or 0.0
        $ dur = max(renpy.music.get_duration("music") or 1.0, 1.0)
        $ pm, ps = divmod(int(pos), 60)
        $ dm, ds = divmod(int(dur), 60)

        ## Initialise position once (None = first render)
        if _vn_ps["x"] is None:
            $ _vn_ps["x"] = 210 + (config.screen_width - 210) // 2 - 390
            $ _vn_ps["y"] = config.screen_height - 142

        ## Timer: refreshes the scrubber bar and timestamp display.
        timer 0.25 action SetScreenVariable("vn_tick", not vn_tick) repeat True

        frame at vn_anim_music_player:
            xpos _vn_ps["x"]
            ypos _vn_ps["y"]
            background Solid("#0b0e1f")
            xsize 780
            ysize 130
            padding (0, 0)

            ## Click blocker (first child = lowest z-layer).
            ## Absorbs any click that falls through the controls above it.
            button background None xfill True yfill True action NullAction()

            ## Teal top accent line
            frame background Solid(VN_TEAL) xfill True ysize 3 yalign 0.0 padding (0,0)

            frame background None xfill True yfill True padding (20, 12, 20, 10) clipping True:
                vbox spacing 0 xfill True yfill True:

                    ## ?? ROW 1 (top): name left, timestamp right ??????????????
                    ## Total inner width = 760 - 40 (padding) = 720 px
                    ## Layout: icon(26) + gap(10) + name(580) + gap(10) + time(94) = 720
                    frame background None xfill True ysize 36 padding (0,0) clipping True:
                        hbox xfill True yalign 0.5 spacing 10:
                            frame background Solid(VN_BG3) xsize 26 ysize 26 padding (0,0):
                                text "🎵" size 13 xalign 0.5 yalign 0.5
                            frame background None xsize 580 ysize 26 padding (0,0) clipping True:
                                text track_short style "vn_t" color VN_TEXT size 13 layout "nobreak" yalign 0.5
                            frame background None xsize 94 ysize 26 padding (0,0) clipping True:
                                text f"{pm}:{ps:02d} / {dm}:{ds:02d}" style "vn_t_dim" size 12 yalign 0.5 xalign 1.0 text_align 1.0

                    ## ?? ROW 2 (middle): scrubber ????????????????????????????
                    frame background None xfill True ysize 28 padding (0, 9):
                        ## Visual: dark track + teal fill calculated from pos/dur
                        frame background Solid(VN_BG3) xfill True ysize 10 yalign 0.5 padding (0,0):
                            frame background Solid(VN_TEAL) xsize int(pos / dur * 720) ysize 10 xalign 0.0 padding (0,0)
                        ## Interactive: one bar with only thumb visible, handles all events
                        bar value vn_apv left_bar Solid("#00000000") right_bar Solid("#00000000") thumb Solid("#ffffff") xfill True ysize 10 yalign 0.5

                    ## ?? ROW 3 (bottom): controls + volume + grab handle ??????
                    ## [spacer] [?] [?15] [?/?] [?] [15?] [?] [spacer] [?? vol] [snap grid]
                    frame background None xfill True ysize 42 padding (0,0) clipping True:
                        hbox xfill True yalign 0.5:
                            null xfill True
                            hbox spacing 6 yalign 0.5:

                                ## ? Previous track
                                textbutton "⏮️" style "vn_btn_player" yalign 0.5 text_color VN_ACC2:
                                    action Function(vn_playlist_nav, -1)

                                ## ? Seek back 15 s
                                hbox spacing 2 yalign 0.5:
                                    textbutton "⏪" style "vn_btn_player" yalign 0.5 text_color VN_ACC2:
                                        action Function(vn_seek_music, -15)
                                    text "15" style "vn_t_faint" size 10 yalign 1.0

                                ## Play / Pause toggle
                                if is_paused:
                                    textbutton "▶️" style "vn_btn_player" yalign 0.5:
                                        action Function(renpy.music.set_pause, False, channel="music")
                                else:
                                    textbutton "⏸️" style "vn_btn_player" yalign 0.5:
                                        action Function(renpy.music.set_pause, True, channel="music")

                                ## Stop
                                textbutton "⏹️" style "vn_btn_player" yalign 0.5 text_color VN_ERR:
                                    action Stop("music")

                                ## ? Seek forward 15 s
                                hbox spacing 2 yalign 0.5:
                                    text "15" style "vn_t_faint" size 10 yalign 1.0
                                    textbutton "⏩" style "vn_btn_player" yalign 0.5 text_color VN_ACC2:
                                        action Function(vn_seek_music, 15)

                                ## ? Next track
                                textbutton "⏭️" style "vn_btn_player" yalign 0.5 text_color VN_ACC2:
                                    action Function(vn_playlist_nav, 1)

                            null xfill True
                            ## Volume control
                            hbox spacing 8 yalign 0.5 xsize 136:
                                text "🔊" style "vn_t_dim" size 13 yalign 0.5
                                bar value MixerValue("music") left_bar Solid(VN_ACC) right_bar Solid(VN_BG3) thumb Solid(VN_ACC2) xsize 100 ysize 12 yalign 0.5

                            ## ?? Position Snap Grid ???????????????????????????
                            ## Replaces the drag mechanism entirely. A 3x3 grid that snaps
                            ## the player to 9 possible screen positions.
                            grid 3 3 spacing 2 yalign 0.5:
                                for py in range(3):
                                    for px in range(3):
                                        button padding (0,0) xsize 8 ysize 8:
                                            background Solid(VN_ACC2)
                                            hover_background Solid(VN_TEAL)
                                            action Function(vn_player_snap, px, py)



## ── Ren'Py Preferences popup ──────────────────────────────────────────────────
## Wraps the built-in 'preferences' screen in our own modal so that right-click
## is intercepted here and cannot open the game-menu Save/Load screen.

screen vn_prefs_popup():
    zorder 600
    modal True

    ## Block right-click entirely while this popup is open
    key "game_menu"  action NullAction()
    key "K_ESCAPE"   action Hide("vn_prefs_popup")

    ## Semi-transparent backdrop — clicking it closes the popup
    button xfill True yfill True background Solid("#000000bb") padding (0,0):
        action Hide("vn_prefs_popup")

    ## Centred panel
    frame xalign 0.5 yalign 0.5 xsize 720 background Solid("#0b0e1a") padding (0,0):
        vbox spacing 0 xfill True:
            ## Header bar
            frame background Solid("#111827") xfill True padding (20,14):
                hbox xfill True yalign 0.5:
                    hbox spacing 10 yalign 0.5:
                        text "⚙️" size 18 yalign 0.5
                        text "Ren'Py Preferences" style "vn_t_sub" yalign 0.5
                    null xfill True
                    textbutton "✕  Close" style "vn_btn_ghost":
                        action Hide("vn_prefs_popup")
            frame background Solid("#1a2540") xfill True ysize 1 padding (0,0)
            ## The built-in preferences screen embedded inline
            frame background None xfill True padding (0,0):
                use preferences

## ── Top toolbar ────────────────────────────────────────────────────────────────

screen vn_toolbar():
    frame background Solid(VN_BG0) xfill True ysize 58 padding (0, 0):
        vbox spacing 0 xfill True:
            hbox xfill True yalign 0.5 spacing 0 ysize 57:

                ## ?? Logo block ????????????????????????????????????????????
                frame background Solid(VN_BG1) padding (20, 0) ysize 57:
                    hbox spacing 10 yalign 0.5:
                        frame background Solid(VN_TEAL) xsize 8 ysize 8 padding (0,0) yalign 0.5
                        frame background Solid(VN_ACC) xsize 8 ysize 8 padding (0,0) yalign 0.5
                        text "VNV MAKER" style "vn_t_head" size 18 yalign 0.5 color VN_TEXT

                frame background Solid(VN_BDR) xsize 1 ysize 57 padding (0,0)

                ## ?? Breadcrumb ???????????????????????????????????????????????
                frame background None xfill True padding (24, 0) yoffset 5:
                    if vns.project:
                        hbox yalign 0.5 spacing 12:
                            ## Panel pill
                            $ _panel_label = {"hub":"Overview","scenes":"Scenes","dialogue":"Dialogue","scene_editor":"Scene Editor","characters":"Characters","assets":"Assets","graph":"Graph","player":"Test Play","export":"Export"}.get(vns.panel, "Home")
                            frame background Solid("#1a2540") padding (14, 6) yalign 0.5:
                                text _panel_label style "vn_t" size 15 color VN_ACC2 yalign 0.5
                            ## Separator
                            text ">" style "vn_t_faint" size 22 yalign 0.5 color VN_BDR
                            ## Project title
                            text vns.project.get('title', 'Untitled') style "vn_t" size 19 font VN_FONTB yalign 0.5 color VN_TEXT
                            ## Author
                            if vns.project.get('author'):
                                text "by" style "vn_t_faint" size 14 yalign 0.5
                                text vns.project.get('author', '') style "vn_t" size 14 yalign 0.5 color VN_ACC
                    else:
                        text "No project open" style "vn_t_faint" size 13 yalign 0.5

                ## ?? Right buttons ????????????????????????????????????????????
                frame background None padding (12, 0):
                    hbox spacing 8 yalign 0.5:
                        if vns.project:
                            textbutton "↩️ Undo" style "vn_btn_ghost":
                                sensitive vns.history.can_undo()
                                action Function(vns.history.undo)
                                tooltip vns.history.undo_name()
                            textbutton "↪️ Redo" style "vn_btn_ghost":
                                sensitive vns.history.can_redo()
                                action Function(vns.history.redo)
                                tooltip vns.history.redo_name()

                            frame background Solid(VN_BDR) xsize 1 ysize 24 padding (0,0) yalign 0.5

                            textbutton "💾  Save" style "vn_btn_ghost":
                                action Function(vns.save)
                            textbutton "▶️  Test" style "vn_btn_teal":
                                action (Function(_vns_play_external) if vns.test_external else Function(vns.go, "player"))
                            textbutton ("🌐" if vns.test_external else "💻") style "vn_btn_ghost":
                                action ToggleField(vns, "test_external")
                                tooltip "Toggle External Window/Native IDE testing"
                            textbutton "📦  Export" style "vn_btn_accent":
                                action Function(vns.go, "export")
                            frame background Solid(VN_BDR) xsize 1 ysize 24 padding (0,0) yalign 0.5
                            textbutton "?" style "vn_btn_ghost":
                                action ShowMenu("vn_shortcuts_panel")
                                tooltip "Keyboard Shortcuts"

            ## Bottom separator
            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)

## ?? Left sidebar ?????????????????????????????????????????????????????????????

screen vn_sidebar():
    frame style "vn_fr_sidebar":
        xsize 210 yfill True

        vbox spacing 0 xfill True:

            ## ?? App section ?????????????????????????????????????????????????
            frame background Solid(VN_BG2) xfill True padding (14, 6):
                text "WORKSPACE" style "vn_t_label"

            textbutton "🏠  Home" style "vn_btn_nav" xfill True:
                action Function(vns.go, "home")
                selected vns.panel == "home"

            ## Divider
            frame background Solid(VN_BDR) ysize 1 xfill True padding (0,0)

            ## ?? Project section ??????????????????????????????????????????????
            if vns.project:
                frame background Solid(VN_BG2) xfill True padding (14, 6):
                    text "PROJECT" style "vn_t_label"

                textbutton "📊  Overview" style "vn_btn_nav" xfill True:
                    action Function(vns.go, "hub")
                    selected vns.panel == "hub"

                textbutton "🗺️  Graph" style "vn_btn_nav" xfill True:
                    action Function(vns.go, "graph")
                    selected vns.panel == "graph"



                textbutton "👥  Characters" style "vn_btn_nav" xfill True:
                    action Function(vns.go, "characters")
                    selected vns.panel == "characters"

                ## ?? Assets section ???????????????????????????????????????????
                frame background Solid(VN_BDR) ysize 1 xfill True padding (0,0)

                frame background Solid(VN_BG2) xfill True padding (14, 6):
                    text "ASSETS" style "vn_t_label"

                textbutton "🖼️  Images & Audio" style "vn_btn_nav" xfill True:
                    action Function(vns.go, "assets")
                    selected vns.panel == "assets"

        if vns.project:
            ## ?? Footer ???????????????????????????????????????????????????
            vbox yalign 1.0 spacing 0 xfill True:
                frame background Solid(VN_BDR) ysize 1 xfill True padding (0,0)

                textbutton "❌  Close Project" style "vn_btn_ghost" xfill True:
                    action [Function(vns.save), Function(vns.close_project)]
                    text_style "vn_btn_ghost_text"

## ?? Home / Project Browser ???????????????????????????????????????????????????

screen vn_home_panel():

    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
        vbox spacing 0 xfill True:

            ## ?? Hero header bar ???????????????????????????????????????????
            frame background Solid(VN_BG1) xfill True padding (0, 0) ysize 80:
                frame background Solid(VN_BDR) xfill True ysize 1 yalign 1.0 padding (0,0)
                frame background None xalign 0.0 yalign 0.5 padding (40, 0):
                    ## Group title, subtitle, and New Project button closely
                    hbox spacing 32 yalign 0.5:
                        vbox spacing 6 yalign 0.5:
                            hbox spacing 10 yalign 0.5:
                                frame background Solid(VN_ACC) xsize 4 ysize 24 padding (0,0) yalign 0.5
                                text "Your Projects" style "vn_t_head"
                            text "Create, open, and manage your visual novels" style "vn_t_dim"
                        
                        textbutton "+ New Project" style "vn_btn_accent" yalign 0.5:
                            action [
                                SetDict(vns.new_proj, 'show', not vns.new_proj.get('show', False)),
                                SetDict(vns.new_proj, 'title', ''),
                                SetDict(vns.new_proj, 'author', ''),
                                SetDict(vns.new_proj, 'resolution', [1920, 1080]),
                            ]

                        textbutton "📥 Import Project" style "vn_btn_accent" yalign 0.5:
                            action [
                                SetDict(vns.new_proj, 'show', False),
                                SetDict(vns.import_proj, 'show', not vns.import_proj.get('show', False)),
                                SetDict(vns.import_proj, 'path', ''),
                                SetDict(vns.import_proj, 'title', ''),
                                SetDict(vns.import_proj, 'author', ''),
                                SetDict(vns.import_proj, 'result', None),
                                SetDict(vns.import_proj, 'warnings', []),
                            ]

            ## ?? Import project form ???????????????????????????????????????
            if vns.import_proj.get('show'):
                frame background Solid(VN_BG2) xfill True padding (40, 40):
                    vbox spacing 16:
                        ## Header
                        hbox spacing 6 yalign 0.5:
                            frame background Solid(VN_ACC) xsize 3 ysize 18 padding (0,0) yalign 0.5
                            text "Import Ren'Py Project" style "vn_t_sub"

                        text "Point to a Ren'Py game folder (must contain .rpy files). Scripts will be parsed into scenes." style "vn_t_dim" size 13

                        ## Path input
                        hbox spacing 16 xsize 720:
                            vbox spacing 6 xsize 460:
                                text "GAME FOLDER PATH" style "vn_t_label"
                                use vn_text_input("vn_import_path", vns.import_proj, "path", "e.g. C:/Users/You/MyGame/game", 512)
                            vbox spacing 6 xsize 240:
                                text "PROJECT TITLE" style "vn_t_label"
                                use vn_text_input("vn_import_title", vns.import_proj, "title", "Imported Project", 80)

                        ## Author row
                        hbox spacing 16 xsize 360:
                            vbox spacing 6 xsize 220:
                                text "AUTHOR" style "vn_t_label"
                                use vn_text_input("vn_import_author", vns.import_proj, "author", "Author", 60)

                        ## Result/warning display
                        if vns.import_proj.get('warnings'):
                            frame background Solid(VN_BG3) xsize 700 padding (14, 10):
                                vbox spacing 4:
                                    for _w in vns.import_proj['warnings']:
                                        text _w style "vn_t_faint" size 12

                        ## Action buttons
                        hbox spacing 10:
                            textbutton "📥  Import" style "vn_btn_accent":
                                action Function(_vn_do_import)
                            textbutton "Cancel" style "vn_btn_ghost":
                                action SetDict(vns.import_proj, 'show', False)

            ## ?? New project form ?????????????????????????????????????????
            if vns.new_proj.get('show'):
                frame background Solid(VN_BG2) xfill True padding (40, 40):
                    vbox spacing 16:
                        ## Header
                        hbox spacing 6 yalign 0.5:
                            frame background Solid(VN_TEAL) xsize 3 ysize 18 padding (0,0) yalign 0.5
                            text "New Project" style "vn_t_sub"

                        ## Row 1: Title + Author
                        hbox spacing 16 xsize 640:
                            vbox spacing 6 xsize 380:
                                text "TITLE" style "vn_t_label"
                                use vn_text_input("vn_new_proj_title", vns.new_proj, "title", "Project title...", 80)
                            vbox spacing 6 xsize 220:
                                text "AUTHOR" style "vn_t_label"
                                use vn_text_input("vn_new_proj_author", vns.new_proj, "author", "Author name...", 60)

                        ## Row 2: Resolution picker
                        vbox spacing 8:
                            hbox spacing 8 yalign 0.5:
                                text "RESOLUTION" style "vn_t_label" yalign 0.5
                                text "(applies to exported game)" style "vn_t_faint" size 11 yalign 0.5
                            $ _cur_res = vns.new_proj.get('resolution', [1920, 1080])
                            hbox spacing 6:
                                for _rw, _rh, _rlbl, _rdesc in [
                                    (1280,  720,  "720p",  "1280×720"),
                                    (1920, 1080,  "1080p", "1920×1080"),
                                    (2560, 1440,  "1440p", "2560×1440"),
                                    (3840, 2160,  "4K",    "3840×2160"),
                                ]:
                                    $ _is_sel = (_cur_res == [_rw, _rh])
                                    button padding (0,0) xsize 140 ysize 52:
                                        action SetDict(vns.new_proj, 'resolution', [_rw, _rh])
                                        background Solid(VN_TEAL + "33" if _is_sel else VN_BG3)
                                        hover_background Solid(VN_TEAL + "22")
                                        frame background None xfill True yfill True padding (14, 6):
                                            vbox spacing 2 xalign 0.5 yalign 0.5:
                                                hbox spacing 6 xalign 0.5 yalign 0.5:
                                                    if _is_sel:
                                                        frame background Solid(VN_TEAL) xsize 7 ysize 7 padding (0,0) yalign 0.5
                                                    else:
                                                        frame background Solid(VN_BDR) xsize 7 ysize 7 padding (0,0) yalign 0.5
                                                    text _rlbl style "vn_t" size 15 font VN_FONTB color (VN_TEAL if _is_sel else VN_TEXT) yalign 0.5
                                                text _rdesc style "vn_t_faint" size 10 xalign 0.5

                        ## Row 3: Action buttons
                        hbox spacing 10:
                            $ _np_res = vns.new_proj.get('resolution', [1920, 1080])
                            textbutton "✨  Create Project" style "vn_btn_accent":
                                action [
                                    Function(vns.open_project,
                                        vn_new_project(
                                            vns.new_proj.get('title') or 'Untitled',
                                            vns.new_proj.get('author') or 'Author',
                                            tuple(_np_res))),
                                    Function(vns.save),
                                    SetDict(vns.new_proj, 'show', False),
                                ]
                            textbutton "Cancel" style "vn_btn_ghost":
                                action SetDict(vns.new_proj, 'show', False)

            ## ?? Project list ?????????????????????????????????????????????????
            $ projects = vn_all()
            if not projects:
                frame background None xfill True yfill True padding (0,0):
                    vbox xalign 0.5 yalign 0.5 spacing 20:
                        text "🚧" size 64 xalign 0.5
                        vbox spacing 8 xalign 0.5:
                            text "No projects yet" style "vn_t_sub" xalign 0.5
                            text "Click \"+ New Project\" above to get started." style "vn_t_dim" xalign 0.5
            else:
                viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                    vbox spacing 2 xfill True:
                        for proj in projects:
                            use vn_project_card(proj)

screen vn_project_card(proj):
    default confirm_del = False

    if not confirm_del:
        ## Outer vbox: button row + thin divider below
        vbox xfill True spacing 0:
            button xfill True padding (0,0) ysize 80:
                action Function(vns.open_project, proj)
                background Solid(VN_BG1)
                hover_background Solid(VN_BG2)

                ## Fixed container to precisely place left & right elements
                fixed xfill True yfill True:
                    ## Left accent strip
                    frame background Solid(VN_ACC + "88") xpos 0 ypos 0 xsize 4 yfill True padding (0,0)

                    ## Left content (Thumbnail + Info)
                    hbox spacing 16 yalign 0.5 xpos 20:
                        frame background Solid(VN_ACC + "22") xsize 56 ysize 56 padding (0,0) yalign 0.5:
                            text "📁" xalign 0.5 yalign 0.5 size 26
                        
                        vbox yalign 0.5 spacing 6:
                            text proj.get('title', 'Untitled') style "vn_t" size 18 font VN_FONTB
                            hbox spacing 8:
                                text ("by " + proj.get('author', '?')) style "vn_t_dim" size 13
                                text "" style "vn_t_faint" size 13
                                $ sc = len(proj.get('scenes', []))
                                $ ch = len(proj.get('characters', []))
                                text f"{sc} scene{'s' if sc!=1 else ''}" style "vn_t_faint" size 13
                                text "" style "vn_t_faint" size 13
                                text f"{ch} char{'s' if ch!=1 else ''}" style "vn_t_faint" size 13
                                $ _pres = proj.get('resolution')
                                if _pres:
                                    text "" style "vn_t_faint" size 13
                                    text f"{_pres[0]}x{_pres[1]}" style "vn_t_faint" size 13

                    ## Right actions (Open / Delete)
                    hbox spacing 6 yalign 0.5 xalign 1.0 xoffset -24:
                        textbutton "Open" style "vn_btn_ghost":
                            action Function(vns.open_project, proj)
                        textbutton "🗑️" style "vn_btn_icon":
                            action ToggleLocalVariable("confirm_del")

            ## Divider below the card
            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)


    else:
        frame background Solid(VN_BG2) xfill True padding (20, 14):
            hbox spacing 16 xfill True yalign 0.5:
                frame background Solid(VN_ERR + "33") padding (10, 8):
                    text f"Are you sure you want to delete \"{proj.get('title','?')}\"?" style "vn_t_dim" yalign 0.5
                textbutton "✅ Yes" style "vn_btn_danger":
                    action [
                        Function(vn_delete, proj['id']),
                        Function(vns.notify, "Project deleted.", "warn"),
                    ]
                textbutton "❌ No" style "vn_btn_ghost":
                    action ToggleLocalVariable("confirm_del")

## ?? Project Hub ??????????????????????????????????????????????????????????????

screen vn_hub_panel():
    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
        vbox spacing 0 xfill True yfill True:

            ## Hero strip
            frame background Solid(VN_BG1) xfill True padding (48, 28):
                $ _st = _vn_hub_stats(vns.project)
                vbox spacing 12:
                    hbox spacing 10 yalign 0.5:
                        frame background Solid(VN_ACC) xsize 4 ysize 28 padding (0,0) yalign 0.5
                        text vns.project.get('title', 'Untitled') style "vn_t_head" yalign 0.5
                        if vns.project.get('author'):
                            text "by " + vns.project.get('author','') style "vn_t_faint" size 14 yalign 0.5
                    ## Stats row
                    hbox spacing 28 xfill True:
                        for _s_icon, _s_label, _s_key in [
                            ("🎬", "Scenes",     "scenes"),
                            ("👥", "Characters", "characters"),
                            ("⚡", "Events",     "events"),
                            ("📖", "Words",      "words"),
                            ("⏱", "~Read Time", "read_min"),
                        ]:
                            frame background Solid(VN_BG2) padding (16, 10):
                                vbox spacing 4:
                                    hbox spacing 6 yalign 0.5:
                                        text _s_icon size 14 yalign 0.5
                                        text _s_label style "vn_t_label" yalign 0.5
                                    $ _sv = str(_st.get(_s_key, 0))
                                    $ _sv = _sv + " min" if _s_key == "read_min" else _sv
                                    text _sv style "vn_t" size 20 font VN_FONTB color VN_TEXT
                        null xfill True
                        vbox yalign 0.5 spacing 2:
                            text "💾 Last saved" style "vn_t_label"
                            text _st.get('last_saved', '?') style "vn_t" size 12 color VN_DIM

            ## Bottom border under hero
            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)

            ## Quick action buttons
            frame background Solid(VN_BG0) xfill True padding (48, 14):
                hbox spacing 12 yalign 0.5:
                    textbutton "▶️  Test Play" style "vn_btn_teal":
                        action (Function(_vns_play_external) if vns.test_external else Function(vns.go, "player"))
                    textbutton ("🌐" if vns.test_external else "💻") style "vn_btn_ghost":
                        action ToggleField(vns, "test_external")
                        tooltip "Toggle External Window/Native IDE testing"
                    textbutton "⚙️ Settings" style "vn_btn_ghost":
                        action Function(vns.go, "settings")
                    textbutton "📦  Export Game" style "vn_btn_accent":
                        action Function(vns.go, "export")
                    if not vns.project.get('start'):
                        frame background Solid(VN_WARN + "22") padding (10, 6):
                            text "⚠️ No start scene set - go to Graph View to set one." style "vn_t_faint" size 13 yalign 0.5

            ## Bottom border under actions
            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)

            ## Tool cards grid - fills remaining height
            viewport xfill True yfill True mousewheel True style_prefix "vn_vscroll":
                frame background Solid(VN_BG0) xfill True padding (48, 32):
                    vbox spacing 16 xfill True:
                        ## Row 1
                        hbox spacing 16 xfill True:
                            for lbl, icon, panel, desc, col in [
                                ("Scene Graph",  "🗺️", "graph",      "Visual story map",      VN_ACC),
                                ("Scenes",       "🎬", "scenes",     "Scenes & dialogue",     VN_TEAL),
                                ("Characters",   "👥", "characters", "Create & style chars",  VN_PINK),
                            ]:
                                use vn_hub_card(lbl, icon, panel, desc, col)

                        ## Row 2
                        hbox spacing 16 xfill True:
                            for lbl, icon, panel, desc, col in [
                                ("Assets",    "🖼️", "assets",    "Images & audio",       VN_INFO),
                            ]:
                                use vn_hub_card(lbl, icon, panel, desc, col)

screen vn_hub_card(lbl, icon, panel, desc, col):
    button xfill True ysize 130 padding (0,0):
        action Function(vns.go, panel)
        background Solid(VN_BG2)
        hover_background Solid(VN_BG3)

        hbox xfill True yfill True spacing 0:
            ## Left colour accent bar
            frame background Solid(col) xsize 4 yfill True padding (0,0)
            ## Content
            frame background None xfill True yfill True padding (20, 0):
                hbox xfill True yalign 0.5 spacing 20:
                    text icon size 36 yalign 0.5
                    vbox xfill True yalign 0.5 spacing 6:
                        text lbl style "vn_t" font VN_FONTB size 17
                        text desc style "vn_t_faint" size 13
                    text ">" style "vn_t_faint" size 22 yalign 0.5


## ══ Keyboard Shortcuts Overlay ═══════════════════════════════════════════════════════════════════════════
screen vn_shortcuts_panel():
    zorder 500
    modal True
    ## Backdrop — clicking it closes the panel
    button background Solid("#000000bb") xfill True yfill True padding (0, 0):
        action Return()
    ## Panel
    frame background Solid(VN_BG1) xsize 660 padding (0, 0) xalign 0.5 yalign 0.5:
        vbox spacing 0 xfill True:
            ## Header
            frame background Solid(VN_BG2) xfill True padding (24, 16):
                hbox xfill True yalign 0.5:
                    vbox spacing 4 yalign 0.5:
                        hbox spacing 10 yalign 0.5:
                            frame background Solid(VN_ACC) xsize 4 ysize 20 padding (0,0) yalign 0.5
                            text "⌨️  Keyboard Shortcuts" style "vn_t_head" size 20
                        text "All shortcuts are global unless noted." style "vn_t_faint" size 12
                    null xfill True
                    textbutton "✕  Close" style "vn_btn_ghost":
                        action Return()
            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)
            ## Two-column grid of shortcuts
            frame background None xfill True padding (24, 20):
                hbox spacing 32 xfill True:
                    vbox spacing 12 xfill True:
                        text "PROJECT" style "vn_t_label"
                        for _k, _desc in [
                            ("Ctrl + Z",        "Undo last action"),
                            ("Ctrl + Y",        "Redo"),
                            ("Ctrl + S",        "Save project"),
                            ("Ctrl + D",        "Duplicate selected event"),
                            ("Ctrl + N",        "New dialogue event"),
                        ]:
                            hbox spacing 12 xfill True yalign 0.5:
                                frame background Solid(VN_BG3) padding (10, 4):
                                    text _k style "vn_t" size 12 font VN_FONTB color VN_ACC
                                text _desc style "vn_t_dim" size 13 yalign 0.5 xfill True
                    frame background Solid(VN_BDR) xsize 1 yfill True padding (0,0)
                    vbox spacing 12 xfill True:
                        text "SCENE EDITOR" style "vn_t_label"
                        for _k, _desc in [
                            ("Space + Drag",    "Pan the canvas"),
                            ("Ctrl + Scroll",   "Zoom in / out"),
                            ("0",               "Reset zoom to 100%"),
                            ("Ctrl+K Delete",   "Clear selected cell"),
                            ("Ctrl+K Backspace","Delete event"),
                        ]:
                            hbox spacing 12 xfill True yalign 0.5:
                                frame background Solid(VN_BG3) padding (10, 4):
                                    text _k style "vn_t" size 12 font VN_FONTB color VN_TEAL
                                text _desc style "vn_t_dim" size 13 yalign 0.5 xfill True
            frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)
            frame background Solid(VN_BG2) xfill True padding (16, 12):
                textbutton "✕  Close" style "vn_btn_ghost" xalign 0.5:
                    action Return()
