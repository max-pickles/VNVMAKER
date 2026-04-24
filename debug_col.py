path = r'game\vn_maker\vn_scene_editor.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Find the col_title line and show context
idx = src.find('_col_title = "START"')
if idx == -1:
    print("Pattern not found at all!")
else:
    print("Found at index", idx)
    print(repr(src[idx-60:idx+300]))
