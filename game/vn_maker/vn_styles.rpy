## ???????????????????????????????????????????????
##  VN Maker ? Style System          init -10
## ???????????????????????????????????????????????

init -10 python:
    ## ?? Palette ??????????????????????????????????
    VN_BG0   = "#07091a"   ## deepest bg
    VN_BG1   = "#0d1023"   ## sidebar / panels
    VN_BG2   = "#141830"   ## cards level 1
    VN_BG3   = "#1a2040"   ## cards level 2
    VN_BG4   = "#202750"   ## cards level 3 (new)
    VN_HOVER = "#252d5a"
    VN_SEL   = "#2b3470"
    VN_BDR   = "#252e58"
    VN_BDR2  = "#313d74"   ## brighter divider (new)

    ## ?? Accent colours ???????????????????????????
    VN_ACC   = "#8b7fff"   ## purple (slightly brighter)
    VN_ACC2  = "#b3aaff"   ## light purple tint (new)
    VN_TEAL  = "#00e5d4"
    VN_TEAL2 = "#00b8aa"   ## darker teal (new)
    VN_PINK  = "#ff6bba"   ## new accent (new)

    ## ?? Status colours ???????????????????????????
    VN_OK    = "#2ee87a"
    VN_WARN  = "#ffb830"
    VN_ERR   = "#ff4d4d"
    VN_INFO  = "#5ab0ff"

    ## ?? Typography ???????????????????????????????
    VN_TEXT  = "#eceffe"
    VN_DIM   = "#8d9ac5"
    VN_FAINT = "#4d5a88"
    VN_FONT  = "DejaVuSans.ttf"
    VN_FONTB = "DejaVuSans-Bold.ttf"
    VN_FONTI = "DejaVuSans-Oblique.ttf"

## ?? Text styles ??????????????????????????????????
style vn_t:
    font VN_FONT
    color VN_TEXT
    size 17
    outlines []

style vn_t_dim is vn_t:
    color VN_DIM
    size 15

style vn_t_faint is vn_t:
    color VN_FAINT
    size 13

style vn_t_head is vn_t:
    font VN_FONTB
    size 28
    color VN_TEXT

style vn_t_sub is vn_t:
    font VN_FONTB
    size 18
    color VN_DIM

style vn_t_label is vn_t:
    font VN_FONTB
    size 10
    color VN_FAINT
    ## letter_spacing 1  (Ren'Py doesn't support this, but keep the visual idea)

style vn_t_acc is vn_t:
    color VN_ACC
    font VN_FONTB
    size 15

style vn_t_teal is vn_t:
    color VN_TEAL
    size 15

style vn_t_pink is vn_t:
    color VN_PINK
    size 15

## ?? Frame / Container styles ??????????????????????
style vn_fr:
    background Solid(VN_BG1)
    padding (0, 0)

style vn_fr_panel:
    background Solid(VN_BG2)
    padding (20, 18)

style vn_fr_card:
    background Solid(VN_BG3)
    padding (16, 14)

style vn_fr_card2:
    background Solid(VN_BG4)
    padding (14, 10)

style vn_fr_toolbar:
    background Solid(VN_BG0)
    padding (14, 0)

style vn_fr_input:
    background Solid("#141724")
    hover_background Solid("#1c2030")
    padding (12, 8)

style vn_fr_input_focus:
    background Solid("#1c2030")
    padding (12, 8)

style vn_fr_sidebar:
    background Solid(VN_BG1)
    padding (0, 0)

style vn_fr_section:
    background Solid(VN_BG2)
    padding (12, 8)

## ?? Button styles ?????????????????????????????????

style vn_btn:
    background Solid(VN_BG3)
    hover_background Solid(VN_HOVER)
    selected_background Solid(VN_SEL)
    insensitive_background Solid(VN_BG2)
    padding (14, 10)
    xsize None

style vn_btn_text is vn_t:
    size 15
style vn_btn_text_hover is vn_btn_text:
    color VN_TEAL
style vn_btn_text_selected is vn_btn_text:
    color VN_ACC
    font VN_FONTB
style vn_btn_text_insensitive is vn_btn_text:
    color VN_FAINT

## Accent (purple)
style vn_btn_accent:
    background Solid(VN_ACC)
    hover_background Solid("#7a6eef")
    insensitive_background Solid(VN_BG3)
    padding (20, 12)
style vn_btn_accent_text is vn_t:
    size 15
    font VN_FONTB
    color "#fff"
style vn_btn_accent_text_insensitive is vn_btn_accent_text:
    color VN_FAINT

## Teal
style vn_btn_teal:
    background Solid(VN_TEAL2)
    hover_background Solid(VN_TEAL)
    padding (18, 12)
style vn_btn_teal_text is vn_t:
    size 15
    color "#fff"
    font VN_FONTB

## Danger (red)
style vn_btn_danger:
    background Solid("#7a1a1a")
    hover_background Solid(VN_ERR)
    padding (14, 10)
style vn_btn_danger_text is vn_t:
    size 14
    color "#fff"
    font VN_FONTB

## Ghost (transparent with subtle border feel)
style vn_btn_ghost:
    background Solid("#ffffff0a")
    hover_background Solid("#ffffff18")
    padding (12, 8)
style vn_btn_ghost_text is vn_t:
    size 14
    color VN_DIM
style vn_btn_ghost_text_hover is vn_btn_ghost_text:
    color VN_TEAL

## Icon-only button
style vn_btn_icon:
    background Solid("#00000000")
    hover_background Solid(VN_HOVER)
    padding (8, 8)
style vn_btn_icon_text is vn_t:
    size 18
    color VN_DIM
style vn_btn_icon_text_hover is vn_btn_icon_text:
    color VN_TEAL

## Sidebar nav
style vn_btn_nav:
    background Solid("#00000000")
    hover_background Solid(VN_BG3)
    selected_background Solid(VN_SEL)
    padding (18, 4)
style vn_btn_nav_text is vn_t:
    size 15
style vn_btn_nav_text_hover is vn_btn_nav_text:
    color VN_TEAL
style vn_btn_nav_text_selected is vn_btn_nav_text:
    color VN_ACC
    font VN_FONTB

## Small chip / tag button
style vn_btn_chip:
    background Solid(VN_BG4)
    hover_background Solid(VN_HOVER)
    selected_background Solid(VN_ACC + "44")
    padding (10, 6)
style vn_btn_chip_text is vn_t:
    size 13
    color VN_DIM
style vn_btn_chip_text_hover is vn_btn_chip_text:
    color VN_TEXT
style vn_btn_chip_text_selected is vn_btn_chip_text:
    color VN_ACC

## ?? Scrollbars ????????????????????????????????????
style vn_vscroll:
    bar_vertical True
    xsize 4
    base_bar Frame(Solid(VN_BG0), 2, 0)
    thumb Frame(Solid(VN_ACC), 2, 0)
    bar_resizing True

style vn_layer_vscroll:
    bar_vertical True
    bar_invert True
    xsize 14
    base_bar Solid("#060a12")
    thumb Solid(VN_ACC)

style vn_hscroll:
    bar_vertical False
    ysize 4
    base_bar Frame(Solid(VN_BG0), 0, 2)
    thumb Frame(Solid(VN_ACC), 0, 2)
    bar_resizing True

## ?? Input ?????????????????????????????????????????
style vn_input:
    color VN_TEXT
    font VN_FONT
    size 16

## ?? Multi-line text editor ?????????????????????????????????????
style vn_ted_text:
    font VN_FONT
    color VN_TEXT
    size 15
    line_spacing 4

style vn_ted_cursor:
    font VN_FONT
    color VN_TEAL
    size 15
    line_spacing 4

## ?? Bare button ???????????????????????????????????
style vn_bare_btn:
    background Solid("#00000000")
    hover_background Solid("#00000000")
    padding (0, 0)
style vn_bare_btn_text is vn_t:
    size 15

style vn_btn_player:
    background Solid("#00000000")
    hover_background Solid("#ffffff14")
    padding (10, 6)
style vn_btn_player_text is vn_t:
    size 22
    color VN_TEXT
style vn_btn_player_text_hover is vn_btn_player_text:
    color VN_TEAL

## ── Reusable UI Components ──────────────────────────────────────────────────

screen vn_text_input(id_str, target_dict, target_key, placeholder="Enter text...", max_len=60, btn_xsize=None, btn_ysize=40):
    if vns.ui.get('_focus') == id_str:
        button style "vn_fr_input" xsize btn_xsize xfill (btn_xsize is None) ysize btn_ysize:
            action NullAction()
            input id id_str style "vn_input" yalign 0.5 length max_len:
                value DictInputValue(target_dict, target_key, default=True)
    else:
        $ _fv = target_dict.get(target_key, '') or ''
        button style "vn_fr_input" xsize btn_xsize xfill (btn_xsize is None) ysize btn_ysize:
            action [SetDict(vns.ui, '_focus', id_str), Function(renpy.set_focus, None, id_str)]
            text (_fv if _fv else placeholder) style "vn_input" yalign 0.5 color (VN_FAINT if not _fv else VN_TEXT) size 14
