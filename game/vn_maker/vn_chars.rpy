## ???????????????????????????????????????????????
##  VN Maker ? Character Editor
## ???????????????????????????????????????????????

screen vn_characters_panel():

    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
        hbox spacing 0 xfill True yfill True:

            ## Left: Character list
            frame background Solid(VN_BG1) xsize 260 yfill True padding (0, 0):
                vbox xfill True yfill True spacing 0:
                    frame background Solid(VN_BG2) xfill True padding (14, 12):
                        vbox spacing 10:
                            text "Characters" style "vn_t_sub"
                            textbutton "+ New Character" style "vn_btn_accent" xfill True:
                                action [
                                    Function(_vn_add_char),
                                ]
                    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
                        vbox xfill True spacing 2 yoffset 4:
                            for c in vns.project.get('characters', []):
                                use vn_char_list_row(c)

            ## Right: Inspector
            frame background Solid(VN_BG0) xfill True yfill True padding (28, 24):
                if vns.char_id and vns.char:
                    $ c = vns.char
                    vbox spacing 20 xfill True:
                        ## Name + color header
                        hbox spacing 20 xfill True:
                            frame background Solid(c.get('color','#6c63ff') + "44") xsize 72 ysize 72 padding (0,0):
                                text "👤" size 36 xalign 0.5 yalign 0.5

                            vbox xfill True yalign 0.5 spacing 8:
                                hbox spacing 10:
                                    text "Name" style "vn_t_label" yalign 0.5
                                    use vn_text_input(f"vn_char_name_{c['id']}", c, "name", "Name...", 60, 200, 40)
                                hbox spacing 10:
                                    text "Display Name" style "vn_t_label" yalign 0.5
                                    use vn_text_input(f"vn_char_disp_{c['id']}", c, "display", "Display name...", 60, 200, 40)

                        ## Name color
                        vbox spacing 8:
                            hbox spacing 12:
                                text "Name Color" style "vn_t_label" yalign 0.5
                                frame background Solid(c.get('color','#fff')) xsize 28 ysize 28 padding (0,0)
                                text c.get('color','') style "vn_t_faint" yalign 0.5
                            viewport xfill True ysize 72 scrollbars "horizontal" mousewheel True style_prefix "vn_hscroll":
                                hbox spacing 6:
                                    for col in VN_PALETTE:
                                        button xsize 32 ysize 32 padding (2,2):
                                            background Solid(col)
                                            hover_background Solid(VN_TEXT)
                                            selected c.get('color') == col
                                            action [SetDict(c, 'color', col), Function(vns.save)]
                                            if c.get('color') == col:
                                                frame background Solid("#ffffff44") xfill True yfill True padding (0,0):
                                                    text "⚙️" size 14 xalign 0.5 yalign 0.5 color "#fff"

                        ## Sprite slots
                        vbox spacing 10:
                            hbox spacing 10 yalign 0.5:
                                text "Sprites" style "vn_t_label" yalign 0.5
                                textbutton "+ Add Slot" style "vn_btn_ghost" padding (4,2) yalign 0.5:
                                    action Function(_vn_add_pose, c)
                                    text_size 12
                            text "Click a slot image to assign an asset. Edit the name below it." style "vn_t_faint" size 13
                            
                            $ _poses = c.get('poses', VN_POSES)
                            viewport xfill True ysize 180 scrollbars "horizontal" mousewheel True style_prefix "vn_hscroll":
                                hbox spacing 14:
                                    for pose in _poses:
                                        use vn_sprite_slot(c, pose)

                        ## Delete
                        hbox:
                            textbutton "🗑️ Delete Character" style "vn_btn_danger":
                                action [
                                    Function(vns.project['characters'].remove, c),
                                    SetField(vns, 'char_id', None),
                                    Function(vns.save),
                                    Function(vns.notify, "Character deleted.", "warn"),
                                ]
                else:
                    vbox xalign 0.5 yalign 0.5 spacing 12:
                        text "👥" size 56 xalign 0.5
                        text "🖱️ Select or create a character" style "vn_t_dim" xalign 0.5

screen vn_char_list_row(c):
    button xfill True style "vn_btn_nav":
        selected vns.char_id == c['id']
        action SetField(vns, "char_id", c['id'])
        hbox spacing 12:
            frame background Solid(c.get('color','#6c63ff') + "55") xsize 36 ysize 36 padding (0,0):
                text c.get('display','?')[:1] size 20 xalign 0.5 yalign 0.5 color c.get('color','#fff')
            vbox yalign 0.5:
                text c.get('display', c.get('name','')) style "vn_t" size 15 color c.get('color','#fff')
                $ filled = sum(1 for v in c.get('sprites',{}).values() if v)
                text f"{filled} sprites" style "vn_t_faint" size 12

screen vn_sprite_slot(c, pose):
    $ has_sprite = bool(c.get('sprites', {}).get(pose))
    $ _pose_dict = vns.ui.setdefault(f"pose_edit_{c['id']}_{pose}", {'name': pose})
    
    if _pose_dict['name'] != pose and vns.ui.get('_focus') != f"vn_pose_input_{c['id']}_{pose}":
        timer 0.01 action Function(_vn_rename_pose, c, pose, _pose_dict['name'])

    frame background Solid(VN_BG3) xsize 110 ysize 150 padding (6,6):
        vbox xalign 0.5 yalign 0.0 spacing 4:
            ## Sprite Picker Button
            button xsize 98 ysize 94 padding (0,0):
                background Solid(VN_BG3)
                hover_background Solid(VN_HOVER)
                action Function(_vn_pick_sprite, c, pose)
                if has_sprite:
                    add c['sprites'][pose] xsize 98 ysize 94 fit "contain" xalign 0.5
                else:
                    frame background Solid(VN_BG2) xsize 98 ysize 94 padding (0,0):
                        text "+" size 28 xalign 0.5 yalign 0.5 color VN_FAINT

            ## Rename & Delete Row
            hbox spacing 2 xfill True:
                # Rename input
                $ _f_id = f"vn_pose_input_{c['id']}_{pose}"
                button background Solid(VN_BG0) hover_background Solid(VN_BG1) xfill True padding (4, 4) yalign 0.5:
                    action [SetDict(vns.ui, '_focus', _f_id), Function(renpy.set_focus, None, _f_id)]
                    if vns.ui.get('_focus') == _f_id:
                        input id _f_id value DictInputValue(_pose_dict, 'name') style "vn_t_label" size 11 color VN_TEXT
                    else:
                        text pose style "vn_t_label" size 11 color VN_TEXT text_align 0.5

                # Delete button
                textbutton "✕" style "vn_btn_ghost" padding (4, 4) yalign 0.5:
                    action Function(_vn_delete_pose, c, pose)
                    text_size 11 text_color "#ff5555"

init python:
    def _vn_add_pose(c):
        poses = c.setdefault('poses', list(VN_POSES))
        new_pose = "custom" + str(len(poses) + 1)
        while new_pose in poses:
            new_pose += "_"
        poses.append(new_pose)
        vns.save()
        renpy.restart_interaction()

    def _vn_delete_pose(c, pose):
        poses = c.setdefault('poses', list(VN_POSES))
        if pose in poses:
            poses.remove(pose)
        if pose in c.get('sprites', {}):
            del c['sprites'][pose]
        vns.save()
        renpy.restart_interaction()

    def _vn_rename_pose(c, old_pose, new_pose):
        vns.ui.pop(f"pose_edit_{c['id']}_{old_pose}", None)
        new_pose = new_pose.strip()
        if not new_pose or new_pose == old_pose:
            return
        poses = c.setdefault('poses', list(VN_POSES))
        if new_pose in poses:
            return
        idx = poses.index(old_pose)
        poses[idx] = new_pose
        if 'sprites' in c and old_pose in c['sprites']:
            c['sprites'][new_pose] = c['sprites'].pop(old_pose)
        
        # update all events that use this pose
        for s in vns.project.get('scenes', []):
            for ev in s.get('events', []):
                if ev.get('char_id') == c['id'] and ev.get('pose') == old_pose:
                    ev['pose'] = new_pose
        vns.save()
        renpy.restart_interaction()
    def _vn_add_char():
        c = vn_new_character("Character " + str(len(vns.project.get('characters',[])) + 1))
        vns.project['characters'].append(c)
        vns.char_id = c['id']
        vns.save()
        vns.notify("Character created!", "ok")

    def _vn_pick_sprite(char, pose):
        def cb(path):
            char['sprites'][pose] = path
            vns.save()
            vns.go("characters")
            vns.notify(f"Sprite set for '{pose}'!", "ok")
        vns.asset_mode = "images"
        vns.asset_path = "images"
        vns.asset_cb = cb
        vns.go("assets")
