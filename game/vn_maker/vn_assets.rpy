## ???????????????????????????????????????????????
##  VN Maker ? Asset Browser
## ???????????????????????????????????????????????

## Flat folder list builder (no recursive screens)
init python:
    def vn_flat_folders(root):
        """Return list of (rel_path, depth, name) tuples (no recursion in screen)."""
        result = []
        def _walk(path, depth):
            dirs, _ = vn_ls(path)
            for d in dirs:
                child = path + "/" + d
                result.append((child, depth, d))
                _walk(child, depth + 1)
        result.append((root, 0, root.split("/")[-1]))
        _walk(root, 1)
        return result

screen vn_assets_panel():
    default browse_path = ("audio" if vns.asset_mode == "audio" else "images")
    ## Repeating timer: keeps focus on whichever input box was last clicked

    ## new_folder and search_q are now in vns.ui dict (DictInputValue)

    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
        vbox spacing 0 xfill True yfill True:

            ## Toolbar
            frame background Solid(VN_BG1) xfill True padding (14, 10):
                hbox xfill True spacing 12:
                    ## Tab buttons grouped tightly
                    hbox spacing 2:
                        textbutton "🖼️ Images" style "vn_btn":
                            selected vns.asset_mode == "images"
                            action [SetField(vns, "asset_mode", "images"),
                                    SetLocalVariable("browse_path", "images"),
                                    SetDict(vns.ui, "asset_search", "")]

                        textbutton "🎵 Audio" style "vn_btn":
                            selected vns.asset_mode == "audio"
                            action [SetField(vns, "asset_mode", "audio"),
                                    SetLocalVariable("browse_path", "audio"),
                                    SetDict(vns.ui, "asset_search", "")]

                    frame background Solid(VN_BDR) xsize 1 ysize 34 yalign 0.5
                    ## Path label + search + folder inputs — grouped tightly left of divider
                    text browse_path style "vn_t_dim" yalign 0.5

                    ## Search
                    hbox spacing 6 yalign 0.5:
                        text "🔍" size 14 yalign 0.5
                        if vns.ui.get('_focus') == "vn_asset_search_input":
                            button style "vn_fr_input" xsize 200:
                                action NullAction()
                                input id "vn_asset_search_input" style "vn_input" value DictInputValue(vns.ui, 'asset_search') length 60 size 14
                        else:
                            $ _fv = vns.ui.get('asset_search', '') or ''
                            button style "vn_fr_input" xsize 200:
                                action [SetDict(vns.ui, '_focus', "vn_asset_search_input"), Function(renpy.set_focus, None, "vn_asset_search_input")]
                                text (_fv if _fv else "Search…") style "vn_input" color (VN_FAINT if not _fv else VN_TEXT) size 14

                    ## New folder: [Create Folder] [input box]
                    hbox spacing 6 yalign 0.5:
                        textbutton "🗂️ Create Folder" style "vn_btn_ghost":
                            action Function(_vn_create_folder, browse_path, vns.ui.get('asset_folder',''))
                        if vns.ui.get('_focus') == "vn_asset_folder_input":
                            button style "vn_fr_input" xsize 220:
                                action NullAction()
                                input id "vn_asset_folder_input" style "vn_input" value DictInputValue(vns.ui, 'asset_folder') length 40 size 14
                        else:
                            $ _fv = vns.ui.get('asset_folder', '') or ''
                            button style "vn_fr_input" xsize 220:
                                action [SetDict(vns.ui, '_focus', "vn_asset_folder_input"), Function(renpy.set_focus, None, "vn_asset_folder_input")]
                                text (_fv if _fv else "New folder name...") style "vn_input" color (VN_FAINT if not _fv else VN_TEXT) size 14

                    ## Push everything above to the left
                    null xfill True

                    if vns.asset_cb:
                        frame background Solid(VN_BDR) xsize 1 ysize 34 yalign 0.5
                        text "Picking for project" style "vn_t_label" yalign 0.5
                        textbutton "❌ Cancel" style "vn_btn_danger":
                            action [SetField(vns, "asset_cb", None), Function(vns.go, vns.ui.get('_asset_prev_panel', 'hub'))]

            ## Content
            hbox spacing 0 xfill True yfill True:

                ## Folder tree sidebar (LEFT) - flat list, no recursion
                frame background Solid(VN_BG1) xsize 220 yfill True padding (0,0):
                    $ _root = "images" if vns.asset_mode == "images" else "audio"
                    $ _folders = vn_flat_folders(_root)
                    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                        vbox xfill True spacing 0 yoffset 4:
                            for _fp, _fd, _fn in _folders:
                                button xfill True style "vn_btn_nav":
                                    padding (max(14, 14 + _fd * 10), 9)
                                    selected browse_path == _fp
                                    action [SetLocalVariable("browse_path", _fp), SetDict(vns.ui, "asset_search", "")]
                                    hbox spacing 6:
                                        text ("📂" if browse_path == _fp else "📁") size 14 yalign 0.5
                                        text _fn style "vn_t_dim" size 14 yalign 0.5

                ## File grid (CENTER)
                frame background Solid(VN_BG0) xfill True yfill True padding (14, 10):
                    $ dirs, files = vn_ls(browse_path)
                    $ sq = vns.ui.get('asset_search','').lower()
                    $ filtered = [f for f in files if sq in f.lower()] if sq else files
                    $ is_img   = vns.asset_mode == "images"
                    $ _img_exts   = {'.png','.jpg','.jpeg','.webp','.gif','.bmp'}
                    $ _audio_exts = {'.ogg','.mp3','.wav','.opus','.flac'}
                    $ _valid_ext  = _img_exts if is_img else _audio_exts
                    $ _valid_files = [f for f in filtered if os.path.splitext(f.lower())[1] in _valid_ext]

                    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                        vbox spacing 16 xfill True:

                            ## Subfolders in current dir
                            if dirs:
                                vbox spacing 6:
                                    text "Folders" style "vn_t_label"
                                    hbox spacing 10 box_wrap True:
                                        for d in dirs:
                                            button xsize 90 ysize 90 padding (6,6):
                                                background Solid(VN_BG3)
                                                hover_background Solid(VN_HOVER)
                                                action SetLocalVariable("browse_path", browse_path + "/" + d)
                                                vbox xalign 0.5 yalign 0.5 spacing 6:
                                                    text "📁" size 32 xalign 0.5
                                                    text d style "vn_t_faint" size 12 xalign 0.5

                            ## Files
                            if _valid_files:
                                if is_img:
                                    vbox spacing 6:
                                        text f"{len(_valid_files)} image(s)" style "vn_t_label"
                                        hbox spacing 10 box_wrap True:
                                            for f in _valid_files:
                                                $ _full_rel = browse_path + "/" + f
                                                use vn_image_tile(_full_rel, f)

                                else:
                                    vbox spacing 6 xfill True:
                                        text f"{len(_valid_files)} audio file(s)" style "vn_t_label"

                                        ## Timer keeps this panel in sync with the music player
                                        ## so the highlight moves when ?/? skip tracks.
                                        timer 0.5 action renpy.restart_interaction repeat True

                                        for f in _valid_files:
                                            $ _full_rel = browse_path + "/" + f
                                            ## Strip any seek prefix before comparing paths
                                            $ import re as _re
                                            $ _now_raw  = renpy.music.get_playing("music") or ""
                                            $ _now      = _re.sub(r'^<from [0-9.]+>', '', _now_raw)
                                            $ _is_now   = (_now == _full_rel)

                                            ## Single click on row plays. ? drag handle + Select on right.
                                            button background (Solid("#0d2a2a") if _is_now else Solid(VN_BG3)) hover_background Solid("#0a2020") xsize (config.screen_width - 500) ysize 60 padding (0, 0, 0, 0):
                                                action Play("music", _full_rel)

                                                ## Active track: teal left border
                                                if _is_now:
                                                    frame background Solid(VN_TEAL) xsize 4 yfill True padding (0,0)

                                                ## Left: status icon + filename
                                                hbox spacing 12 yalign 0.5 xalign 0.0 xoffset (20 if not _is_now else 16):
                                                    text ("🔇" if not _is_now else "🔊") size 20 yalign 0.5 color (VN_TEXT if not _is_now else VN_TEAL)
                                                    text f style "vn_t" size 15 yalign 0.5 color (VN_TEXT if not _is_now else VN_TEAL)

                                                ## Right: drag handle + Select
                                                hbox spacing 6 yalign 0.5 xalign 1.0 xoffset -16:
                                                    ## ? Drag handle - click/drag to assign song to a scene
                                                    button background Solid(VN_BG2) hover_background Solid(VN_HOVER) padding (10, 4) yalign 0.5:
                                                        action Function(_vn_asset_select, _full_rel)
                                                        text "🎵" size 18 color VN_ACC2 yalign 0.5
                                                    textbutton "✅ Select" style "vn_btn_teal" yalign 0.5:
                                                        action Function(_vn_asset_select, _full_rel)
                            else:
                                if not dirs:
                                    text "No files here.\nAdd images to game/images/ or audio to game/audio/" style "vn_t_faint"

## ?? Image tile ???????????????????????????????????????????????????????????????

screen vn_image_tile(rel_path, filename):
    button xsize 120 ysize 130 padding (6, 6):
        background Solid(VN_BG3)
        hover_background Solid(VN_HOVER)
        action Function(_vn_asset_select, rel_path)
        vbox xalign 0.5 yalign 0.5 spacing 4:
            if _vn_safe_loadable(rel_path):
                add rel_path xsize 108 ysize 90 fit "contain" xalign 0.5
            else:
                frame background Solid(VN_ERR) xsize 108 ysize 90:
                    text "Error" xalign 0.5 yalign 0.5
            text filename[:18] style "vn_t_faint" size 11 xalign 0.5

## ?? Python helpers ???????????????????????????????????????????????????????????

init python:
    def _vn_safe_loadable(path):
        try:
            return renpy.loader.loadable(path)
        except:
            return False

    def _vn_asset_select(path):
        if vns.asset_cb:
            cb = vns.asset_cb
            vns.asset_cb = None
            vns.go(vns.ui.get('_asset_prev_panel', 'hub'))
            cb(path)
        else:
            vns.notify(f"Selected: {path.split('/')[-1]}", "info")

    def _vn_create_folder(path, name):
        if not name:
            vns.notify("Enter a folder name first.", "warn")
            return
        ok, msg = vn_mkdir(path + "/" + name)
        vns.notify(msg, "ok" if ok else "err")
        renpy.restart_interaction()

