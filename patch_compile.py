path = r'game\vn_maker\vn_compile.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Find and replace the image event block
old_block = "                elif t == 'image':\n                    img_path = ev.get('image', '').replace('\"', '\\\\\"')\n                    if img_path:\n                        if ev.get('atl_code'):\n                            lines.append(f\"{prefix}show expression \\\"{img_path}\\\":\")\n                            for atl_line in ev['atl_code'].split('\\n'):\n                                if atl_line.strip():\n                                    lines.append(f\"{prefix}    {atl_line}\")\n                            if preview_zoom != 1.0:\n                                lines.append(f\"{prefix}    zoom {preview_zoom}\")\n                        else:\n                            if preview_zoom != 1.0:\n                                lines.append(f\"{prefix}show expression \\\"{img_path}\\\":\")\n                                lines.append(f\"{prefix}    zoom {preview_zoom}\")\n                            else:\n                                lines.append(f\"{prefix}show expression \\\"{img_path}\\\"\")"

new_block = "                elif t == 'image':\n                    img_path = ev.get('image', '').replace('\"', '\\\\\"')\n                    if img_path:\n                        side = ev.get('side', 'left')\n                        at_clause = f\" at {side}\" if side in ('left', 'center', 'right') else \"\"\n                        if ev.get('atl_code'):\n                            lines.append(f\"{prefix}show expression \\\"{img_path}\\\" at {side}:\")\n                            for atl_line in ev['atl_code'].split('\\n'):\n                                if atl_line.strip():\n                                    lines.append(f\"{prefix}    {atl_line}\")\n                            if preview_zoom != 1.0:\n                                lines.append(f\"{prefix}    zoom {preview_zoom}\")\n                        else:\n                            if preview_zoom != 1.0:\n                                lines.append(f\"{prefix}show expression \\\"{img_path}\\\"{at_clause}:\")\n                                lines.append(f\"{prefix}    zoom {preview_zoom}\")\n                            else:\n                                lines.append(f\"{prefix}show expression \\\"{img_path}\\\"{at_clause}\")"

if old_block in src:
    src = src.replace(old_block, new_block, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print("Patched successfully.")
else:
    # Show what's actually there to debug
    idx = src.find("elif t == 'image'")
    print("NOT FOUND. Actual content at image block:")
    print(repr(src[idx:idx+600]))
