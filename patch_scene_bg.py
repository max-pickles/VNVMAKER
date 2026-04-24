path = r'game\vn_maker\vn_compile.rpy'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# The three places that emit a bare scene expression for scene-level bg
old = '    scene expression \\"{s[\'bg\']}\\\"'
new = '    scene expression Transform(\\"{s[\'bg\']}\\\", fit=\\"cover\\", xsize=config.screen_width, ysize=config.screen_height)'

old2 = '    scene expression \\"{sc[\'bg\']}\\\"'
new2 = '    scene expression Transform(\\"{sc[\'bg\']}\\\", fit=\\"cover\\", xsize=config.screen_width, ysize=config.screen_height)'

count = src.count(old) + src.count(old2)

src = src.replace(old, new)
src = src.replace(old2, new2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"Replaced {count} bare scene expression(s) with Transform fit=cover.")
