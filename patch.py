import sys

with open("c:/Users/maxcm/OneDrive/Desktop/MEME KING/renpy-8.5.2-sdk/McMax_editor/game/vn_maker/vn_scenes.rpy", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if i == 1916:
        new_lines.append(line)
        new_lines.append('''                        ## ── VIRTUAL GAME SCREEN (Always perfectly 16:9) ──
                        fixed xfill True yfill True clipping True:
                            fixed xsize renpy.config.screen_width ysize renpy.config.screen_height:
                                at Transform(fit="contain", align=(0.5, 0.5))

                                ## The "Gray Block" actual game canvas bounds
                                frame background Solid("#04060b") xfill True yfill True padding (0,0)

                                ## Layer 1: Panned/Zoomed camera contents
                                fixed xfill True yfill True:
                                    at transform:
                                        function store._vn_se_cam_fn
                                    
                                    ## Background image scales perfectly into 16:9 canvas
                                    if _eval_bg:
                                        add Transform(_eval_bg, fit="contain", align=(0.5, 0.5))
                                    
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

                                ## Layer 2: Safe-area guides (un-panned, but locked to 16:9 screen)
                                if vns.ui.get('show_guides', True):
                                    frame background Solid("#ffffff09") xfill True yfill True padding (int(renpy.config.screen_width*0.05), int(renpy.config.screen_height*0.05)):
                                        frame background Solid("#ffffff14") xfill True yfill True padding (0, 0):
                                            pass

                            ## Layer 3: Invisible interaction catchers (Fills preview window)
                            fixed xfill True yfill True:
                                add SceneCanvasEvents()

''')
        skip = True
    elif skip and i >= 1943:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open("c:/Users/maxcm/OneDrive/Desktop/MEME KING/renpy-8.5.2-sdk/McMax_editor/game/vn_maker/vn_scenes.rpy", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
