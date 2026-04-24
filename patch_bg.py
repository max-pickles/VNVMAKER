path = r'game\vn_maker\vn_compile.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# The old bg block (lines 39-54)
old = """                if t == 'bg':
                    bg_path = ev.get('bg', '').replace('\"', '\\\\\"')
                    if bg_path:
                        if ev.get('atl_code'):
                            lines.append(f\"{prefix}scene expression \\\"{bg_path}\\\":\")\n                            for atl_line in ev['atl_code'].split('\\n'):
                                if atl_line.strip():
                                    lines.append(f\"{prefix}    {atl_line}\")
                            if preview_zoom != 1.0:
                                lines.append(f\"{prefix}    zoom {preview_zoom}\")
                        else:
                            if preview_zoom != 1.0:
                                lines.append(f\"{prefix}scene expression \\\"{bg_path}\\\":\")\n                                lines.append(f\"{prefix}    zoom {preview_zoom}\")
                            else:
                                lines.append(f\"{prefix}scene expression \\\"{bg_path}\\\"\")"""

new = """                if t == 'bg':
                    bg_path = ev.get('bg', '').replace('\"', '\\\\\"')
                    if bg_path:
                        # Always scale bg to fill screen using Transform fit=cover
                        fill = f'Transform(\"{bg_path}\", fit=\"cover\", xsize=config.screen_width, ysize=config.screen_height)'
                        if ev.get('atl_code'):
                            lines.append(f\"{prefix}scene expression {fill}:\")
                            for atl_line in ev['atl_code'].split('\\n'):
                                if atl_line.strip():
                                    lines.append(f\"{prefix}    {atl_line}\")
                        else:
                            lines.append(f\"{prefix}scene expression {fill}\")"""

if old in src:
    src = src.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print("Patched bg block successfully.")
else:
    # Debug: show the actual content
    idx = src.find("if t == 'bg':")
    print("NOT FOUND. Actual content:")
    print(repr(src[idx:idx+700]))
