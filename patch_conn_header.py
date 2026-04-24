path = r'game\vn_maker\vn_scene_editor.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

old = (
    '                                                        $ _col_title = "START" if _ci == 0 else ("FINISH" if _ci == _ec + 1 else str(_ci))\n'
    '                                                        $ _col_size = 11 if _col_title in ("START", "FINISH") else 13\n'
    '                                                        text _col_title style "vn_t" size _col_size bold True xalign 0.5 color ("#ff6644" if _is_ph else ("#7788cc" if _csel else "#2e3d6a"))\n'
    '                                                        if _cev:\n'
    '                                                            text _tc_lbl style "vn_t_faint" size 8 bold True xalign 0.5 color ("#ffaa88" if _is_ph else "#445577")'
)

new = (
    '                                                        $ _col_title = "START" if _ci == 0 else ("FINISH" if _ci == _ec + 1 else ("\u2192" if _is_conn_col else str(_ci)))\n'
    '                                                        $ _col_size = 8 if _is_conn_col else (11 if _col_title in ("START", "FINISH") else 13)\n'
    '                                                        $ _col_color = "#2db354" if _is_conn_col else ("#ff6644" if _is_ph else ("#7788cc" if _csel else "#2e3d6a"))\n'
    '                                                        text _col_title style "vn_t" size _col_size bold True xalign 0.5 color _col_color\n'
    '                                                        if _cev and not _is_conn_col:\n'
    '                                                            text _tc_lbl style "vn_t_faint" size 8 bold True xalign 0.5 color ("#ffaa88" if _is_ph else "#445577")'
)

if old in src:
    src = src.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print("Patched OK.")
else:
    print("NOT FOUND.")
