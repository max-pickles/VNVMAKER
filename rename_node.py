path = r'game\vn_maker\vn_graph.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace('textbutton "+ Node"', 'textbutton "+ Scene"', 1)
with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print('Done')
