## ???????????????????????????????????????????????
##  VN Maker : Theme Settings
## ???????????????????????????????????????????????

init -9 python:
    import json
    import os

    # Fallback default theme (Classic VNV)
    VNV_THEME_BGS = {
        "classic": {"name": "Classic VNV", "bg0": "#07091a", "bg1": "#0d1023", "bg2": "#141830", "bg3": "#1a2040", "bg4": "#202750"},
        "gray":    {"name": "Dark Gray",   "bg0": "#111111", "bg1": "#181818", "bg2": "#222222", "bg3": "#2b2b2b", "bg4": "#333333"},
        "blue":    {"name": "Deep Blue",   "bg0": "#0a1128", "bg1": "#121b36", "bg2": "#1a2645", "bg3": "#223154", "bg4": "#2b3d66"},
    }
    
    VNV_THEME_ACCS = {
        "purple": "#8b7fff",
        "blue":   "#3498db",
        "cyan":   "#00e5d4",
        "green":  "#2ecc71",
        "yellow": "#f1c40f",
        "red":    "#e74c3c",
        "pink":   "#ff6bba",
        "white":  "#ffffff",
    }

    def _vns_apply_theme(bg_id=None, acc_id=None):
        if bg_id is None:
            bg_id = persistent.vnv_bg if getattr(persistent, 'vnv_bg', None) else "classic"
        if acc_id is None:
            acc_id = persistent.vnv_acc if getattr(persistent, 'vnv_acc', None) else "purple"

        if bg_id not in VNV_THEME_BGS: bg_id = "classic"
        if acc_id not in VNV_THEME_ACCS: acc_id = "purple"

        bg  = VNV_THEME_BGS[bg_id]
        acc = VNV_THEME_ACCS[acc_id]

        persistent.vnv_bg  = bg_id
        persistent.vnv_acc = acc_id

        # -- Update global constants (safe any time) --
        store.VN_BG0 = bg["bg0"]
        store.VN_BG1 = bg["bg1"]
        store.VN_BG2 = bg["bg2"]
        store.VN_BG3 = bg["bg3"]
        store.VN_BG4 = bg["bg4"]
        store.VN_ACC = acc

        acc_hov = acc + "cc"
        acc_sel = acc + "44"

        # -- Patch style objects (only safe after init finishes) --
        try:
            style.vn_t_acc.color = acc

            style.vn_fr.background           = Solid(bg["bg1"])
            style.vn_fr_panel.background      = Solid(bg["bg2"])
            style.vn_fr_card.background       = Solid(bg["bg3"])
            style.vn_fr_card2.background      = Solid(bg["bg4"])
            style.vn_fr_toolbar.background    = Solid(bg["bg0"])
            style.vn_fr_input.background      = Solid(bg["bg2"])
            style.vn_fr_input.hover_background = Solid(bg["bg3"])
            style.vn_fr_input_focus.background = Solid(bg["bg4"])
            style.vn_fr_sidebar.background    = Solid(bg["bg1"])
            style.vn_fr_section.background    = Solid(bg["bg0"])

            style.vn_btn.background           = Solid(bg["bg2"])
            style.vn_btn.hover_background     = Solid(bg["bg3"])
            style.vn_btn.selected_background  = Solid(bg["bg4"])

            style.vn_btn_nav.background        = Solid(bg["bg1"])
            style.vn_btn_nav.hover_background  = Solid(bg["bg2"])
            style.vn_btn_nav.selected_background = Solid(bg["bg3"])

            style.vn_btn_chip.background       = Solid(bg["bg4"])
            style.vn_btn_chip.hover_background = Solid(bg["bg3"])
            style.vn_btn_chip.selected_background = Solid(acc_sel)

            style.vn_btn_accent.background          = Solid(acc)
            style.vn_btn_accent.hover_background    = Solid(acc_hov)
            style.vn_btn_accent.insensitive_background = Solid(bg["bg3"])

            style.vn_vscroll.thumb     = Frame(Solid(acc), 2, 0)
            style.vn_layer_vscroll.thumb = Solid(acc)
            style.vn_hscroll.thumb     = Frame(Solid(acc), 0, 2)
            style.vn_hscroll.base_bar  = Frame(Solid(bg["bg0"]), 0, 2)

            style.rebuild()
            renpy.restart_interaction()
        except Exception:
            pass  ## styles not yet registered – constants already updated above


## Apply store constants during init (styles deferred to start)
init 10 python:
    _vns_apply_theme()


## Re-apply full style patches once the game has fully loaded
init python:
    config.start_callbacks.append(lambda: _vns_apply_theme())


## ?? Settings Screen ??????????????????????????????????????????????????????????

screen vn_settings_panel():
    frame background Solid(VN_BG0) xfill True yfill True padding (0,0):
        vbox spacing 0 xfill True yfill True:
            ## Toolbar
            frame background Solid(VN_BG1) xfill True padding (14, 10):
                hbox xfill True spacing 14:
                    textbutton "⬅️ Back" style "vn_btn_ghost":
                        action Function(vns.go, "hub")
                    frame background Solid(VN_BDR) xsize 1 yfill True
                    text "Settings & Appearance" style "vn_t_sub" yalign 0.5 xfill True

            ## Content area
            viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                frame background None xfill True padding (40, 40):
                    vbox spacing 32 xfill True:
                    
                        text "Accent Colors" style "vn_t_head"
                        hbox spacing 12:
                            for a_id, a_hex in VNV_THEME_ACCS.items():
                                $ _is_sel = (getattr(persistent, 'vnv_acc', 'purple') == a_id)
                                button xsize 100 ysize 100 padding (0,0):
                                    action Function(_vns_apply_theme, getattr(persistent, 'vnv_bg', 'classic'), a_id)
                                    background Solid(VN_BG3 if not _is_sel else VN_BG4)
                                    hover_background Solid(VN_BG4)
                                    
                                    frame background None xfill True yfill True padding (8,8):
                                        vbox xfill True yfill True spacing 8:
                                            frame background Solid(a_hex) xfill True yfill True
                                            
                                    if _is_sel:
                                        frame background Solid(VN_TEXT) xfill True ysize 4 yalign 1.0 padding (0,0)


                        text "Background Shades" style "vn_t_head"
                        hbox spacing 12:
                            for b_id, b_data in VNV_THEME_BGS.items():
                                $ _is_sel = (getattr(persistent, 'vnv_bg', 'classic') == b_id)
                                button xsize 220 ysize 140 padding (0,0):
                                    action Function(_vns_apply_theme, b_id, getattr(persistent, 'vnv_acc', 'purple'))
                                    background Solid(VN_BG3 if not _is_sel else VN_BG4)
                                    hover_background Solid(VN_BG4)
                                    
                                    frame background None xfill True yfill True padding (12,12):
                                        vbox xfill True yfill True spacing 0:
                                            frame background Solid(b_data['bg1']) xfill True ysize 30 padding (10, 0):
                                                text b_data['name'] style "vn_t" size 14 yalign 0.5 color VN_TEXT
                                            frame background Solid(b_data['bg0']) xfill True yfill True padding (10, 10):
                                                frame background Solid(b_data['bg2']) xfill True ysize 20
                                                
                                    if _is_sel:
                                        frame background Solid(VN_TEXT) xfill True ysize 4 yalign 1.0 padding (0,0)
