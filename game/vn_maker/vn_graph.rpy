## ???????????????????????????????????????????????
##  VN Maker ? Twine-Style Scene Graph   (vn_graph.rpy)
## ???????????????????????????????????????????????
##
##  A visual canvas where every scene is a draggable node card.
##  Arrows are drawn between nodes based on choice / jump links.
##  Clicking a node selects it; the right-side inspector shows
##  scene details and quick-nav buttons.
##
##  New sidebar nav entry:  "??  Graph View"  ? vns.panel == "graph"
##
## ????????????????????????????????????????????????

## ?? Graph canvas Displayable ?????????????????????????????????????????????????

init python:

    import math
    import string as _str_mod
    import random as _rand_mod

    # ── Folder helpers ──────────────────────────────────────────────────────────

    def _vng_folder_scene_ids(project, folder_id):
        """Return the set of scene ids that belong to folder_id (or None = main)."""
        if not project:
            return set()
        folders = project.get('folders', [])
        if folder_id is None:
            # Main context: scenes NOT inside any folder
            in_any = set()
            for f in folders:
                in_any.update(f.get('scene_ids', []))
            return set(sc['id'] for sc in project.get('scenes', [])) - in_any
        for f in folders:
            if f['id'] == folder_id:
                return set(f.get('scene_ids', []))
        return set()

    def _vng_scene_folder(project, scene_id):
        """Return the folder id that owns scene_id, or None if it lives on main."""
        if not project:
            return None
        for f in project.get('folders', []):
            if scene_id in f.get('scene_ids', []):
                return f['id']
        return None

    def _vng_folder_cross_edges(project, folder_id):
        """
        For a folder node on the main graph, collect outgoing cross-edges:
        scenes INSIDE the folder that link OUT to scenes on the main graph.
        Returns list of (target_scene_id, label, color).
        The target_scene_id is a main-graph scene, so it WILL be in node_map.
        """
        if not project or folder_id is None:
            return []
        folder = next((f for f in project.get('folders', []) if f['id'] == folder_id), None)
        if not folder:
            return []
        inside = set(folder.get('scene_ids', []))

        # All scene ids that are NOT in any folder = main-graph scene ids
        in_any_folder = set()
        for f in project.get('folders', []):
            in_any_folder.update(f.get('scene_ids', []))
        outside = set(sc['id'] for sc in project.get('scenes', [])) - in_any_folder

        seen = set()  # deduplicate edges to same target
        edges = []
        for sc in project.get('scenes', []):
            if sc['id'] not in inside:
                continue
            for ev in sc.get('events', []):
                tid = None
                col = VN_ACC
                lbl = 'jump'
                if ev.get('type') == 'choice':
                    for opt in ev.get('opts', []):
                        ot = opt.get('scene')
                        if ot and ot in outside and ot not in seen:
                            edges.append((ot, opt.get('text', '?')[:20], VN_TEAL))
                            seen.add(ot)
                    continue
                elif ev.get('type') == 'jump':
                    tid = ev.get('scene_id')
                elif ev.get('type') == 'if':
                    for key, c in (('scene_true', VN_OK), ('scene_false', VN_ERR)):
                        ot = ev.get(key)
                        if ot and ot in outside and ot not in seen:
                            edges.append((ot, key.replace('scene_', ''), c))
                            seen.add(ot)
                    continue
                if tid and tid in outside and tid not in seen:
                    edges.append((tid, lbl, col))
                    seen.add(tid)
        return edges

    # ── Node builder ───────────────────────────────────────────────────────────

    def _vng_build_nodes(project, layout):
        """
        Return list of node dicts for the current graph context (vng.current_folder).
        Scene-nodes plus Folder-nodes (only in main context).
        """
        if not project:
            return []

        current_folder = getattr(vng, 'current_folder', None)
        visible_ids = _vng_folder_scene_ids(project, current_folder)
        scenes = project.get('scenes', []) if project else []
        nodes = []
        active_bg = None

        # Build a mapping: scene_id → folder_id for quick lookup
        scene_to_folder = {}
        for fld in project.get('folders', []):
            for sid in fld.get('scene_ids', []):
                scene_to_folder[sid] = fld['id']

        # Build scene nodes visible in this context.
        # IMPORTANT: iterate ALL scenes in order to maintain the active_bg
        # inheritance chain — even scenes in other folders still contribute
        # to the background that subsequent scenes inherit.
        for i, sc in enumerate(scenes):
            sid = sc['id']

            sc_initial_bg = sc.get('bg')
            if not sc_initial_bg:
                for ev in sc.get('events', []):
                    if ev.get('type') == 'bg' and ev.get('bg'):
                        sc_initial_bg = ev['bg']
                        break
            inherited_bg = sc_initial_bg or active_bg

            # Always advance active_bg regardless of visibility
            if sc.get('bg'):
                active_bg = sc['bg']
            for ev in sc.get('events', []):
                if ev.get('type') == 'bg' and ev.get('bg'):
                    active_bg = ev['bg']

            # Skip building a node if this scene isn't in the current context
            if sid not in visible_ids:
                continue

            pos = layout.get(sid, _vng_default_pos(i, len(scenes)))
            w, h = 200, 84  # compact height — no thumbnail on canvas

            # Build out-edges. On the main graph, if a target is INSIDE a folder,
            # redirect the edge to point at the folder node instead.
            out_edges = []
            seen_targets = set()
            for ev in sc.get('events', []):
                if ev.get('type') == 'choice':
                    for opt in ev.get('opts', []):
                        tid = opt.get('scene')
                        if not tid or tid in seen_targets:
                            continue
                        if tid in visible_ids:
                            out_edges.append((tid, opt.get('text', '?')[:20], VN_TEAL))
                            seen_targets.add(tid)
                        elif current_folder is None and tid in scene_to_folder:
                            # Redirect to the folder node
                            fid = scene_to_folder[tid]
                            if fid not in seen_targets:
                                out_edges.append((fid, '→ folder', VN_TEAL))
                                seen_targets.add(fid)
                elif ev.get('type') == 'jump' and ev.get('scene_id'):
                    tid = ev['scene_id']
                    if tid in seen_targets:
                        continue
                    if tid in visible_ids:
                        out_edges.append((tid, 'jump', VN_ACC))
                        seen_targets.add(tid)
                    elif current_folder is None and tid in scene_to_folder:
                        fid = scene_to_folder[tid]
                        if fid not in seen_targets:
                            out_edges.append((fid, '→ folder', VN_ACC))
                            seen_targets.add(fid)
                elif ev.get('type') == 'if':
                    for key, col in (('scene_true', VN_OK), ('scene_false', VN_ERR)):
                        tid = ev.get(key)
                        if not tid or tid in seen_targets:
                            continue
                        if tid in visible_ids:
                            out_edges.append((tid, key.replace('scene_', ''), col))
                            seen_targets.add(tid)
                        elif current_folder is None and tid in scene_to_folder:
                            fid = scene_to_folder[tid]
                            if fid not in seen_targets:
                                out_edges.append((fid, '→ folder', col))
                                seen_targets.add(fid)

            nodes.append({
                'id':        sid,
                'kind':      'scene',
                'label':     sc.get('label', '?'),
                'x':         pos[0],
                'y':         pos[1],
                'w':         w,
                'h':         h,
                'sc':        sc,
                'bg_path':   inherited_bg,  # kept for inspector sidebar
                'out_edges': out_edges,
            })

        # On the main graph also render folder nodes
        if current_folder is None:
            folders = project.get('folders', [])
            for fld in folders:
                fid = fld['id']
                # Use vng.layout if available; otherwise fall back to
                # the x/y stored directly in the folder dict (survives restart)
                if fid in layout:
                    pos = layout[fid]
                else:
                    pos = (fld.get('x', 200), fld.get('y', 200))
                    layout[fid] = pos  # seed into layout so drag works immediately
                sc_count = len(fld.get('scene_ids', []))
                cross = _vng_folder_cross_edges(project, fid)
                nodes.append({
                    'id':        fid,
                    'kind':      'folder',
                    'label':     fld.get('label', 'Folder'),
                    'x':         pos[0],
                    'y':         pos[1],
                    'w':         200,
                    'h':         100,
                    'sc':        None,
                    'has_bg':    False,
                    'bg_path':   None,
                    'sc_count':  sc_count,
                    'out_edges': cross,
                    'folder':    fld,
                })

        return nodes

    def _vng_default_pos(i, total):
        """Arrange nodes in a loose grid if no saved position exists."""
        cols = max(1, min(4, total))
        col  = i % cols
        row  = i // cols
        return (80 + col * 260, 60 + row * 150)

    def _vng_bezier_points(sx, sy, tx, ty, segments=24):
        """Return a list of (x,y) screen points for a cubic Bezier S-curve."""
        cp = max(60, abs(tx - sx) * 0.5)
        p0 = (sx, sy)
        p1 = (sx + cp, sy)
        p2 = (tx - cp, ty)
        p3 = (tx, ty)
        pts = []
        for i in range(segments + 1):
            t  = i / segments
            mt = 1 - t
            px = mt**3*p0[0] + 3*mt**2*t*p1[0] + 3*mt*t**2*p2[0] + t**3*p3[0]
            py = mt**3*p0[1] + 3*mt**2*t*p1[1] + 3*mt*t**2*p2[1] + t**3*p3[1]
            pts.append((int(px), int(py)))
        return pts

    def _vng_node_at(nodes, cx, cy, ox, oy, zoom=1.0):
        """Return node whose rect contains canvas point (cx,cy). Reversed for top-most first."""
        for n in reversed(nodes):
            nx = ox + n['x'] * zoom
            ny = oy + n['y'] * zoom
            nw = n['w'] * zoom
            nh = n['h'] * zoom
            pad = 12 * zoom
            if (nx - pad) <= cx <= (nx + nw + pad) and (ny - pad) <= cy <= (ny + nh + pad):
                return n
        return None

    # ??? Displayable ???????????????????????????????????????????????????????????

    class VNGraphCanvas(renpy.Displayable):
        """
        Interactive canvas that renders the scene graph.

        State kept on the _VNGraphState singleton (vng) so Ren'Py's
        screen refresh can see it without needing to persist the displayable.
        """

        def __init__(self, **kwargs):
            super(VNGraphCanvas, self).__init__(**kwargs)
            ## Interaction state lives on vng singleton so that
            ## renpy.restart_interaction() does NOT reset mid-gesture state.

        # ?? Rendering ??????????????????????????????????????????????????????????

        def render(self, width, height, st, at):
            rv = renpy.Render(width, height)
            
            # Store dimensions so event() can clip clicks outside actual bounds
            self._last_w = width
            self._last_h = height

            g = vng   # singleton
            zoom  = g.zoom
            nodes = _vng_build_nodes(vns.project, g.layout)

            # ?? background grid ????????????????????????????????????????????????
            grid_surf = renpy.render(
                Solid(VN_BG0), width, height, st, at)
            rv.blit(grid_surf, (0, 0))

            ox, oy = g.offset_x, g.offset_y

            # ?? draw grid dots (scale density and appearance with zoom) ????????
            import pygame
            cvs = rv.canvas()
            
            # Change grid detail and dot size based on zoom level
            if zoom >= 2.0:
                world_step = 40    # High detail when zoomed in
                dot_size = 3
            elif zoom >= 1.0:
                world_step = 80    # Normal detail
                dot_size = 2
            elif zoom >= 0.5:
                world_step = 160   # Sparse detail
                dot_size = 2
            else:
                world_step = 320   # Minimal detail when heavily zoomed out
                dot_size = 1
                
            step = int(world_step * zoom)
            if step < 15: step = 15 # safety clamp to prevent lag spikes
            
            gx = int(ox % step)
            gy = int(oy % step)
            x = gx
            dot_color = pygame.Color(VN_BDR)
            
            # Fast Pygame rect loop instead of renpy.render + rv.blit
            while x < width:
                y = gy
                while y < height:
                    cvs.rect(dot_color, (x, y, dot_size, dot_size), 0)
                    y += step
                x += step




            # ?? draw edges (Bezier splines) ????????????????????????????????????
            node_map = {n['id']: n for n in nodes}
            for src in nodes:
                for i_edge, (tid, elabel, ecol) in enumerate(src['out_edges']):
                    if tid in node_map:
                        tgt = node_map[tid]
                        
                        # Culling: Only draw edge if its AABB intersects the canvas
                        sx = src['x'] * zoom + ox
                        sy = src['y'] * zoom + oy
                        tx = tgt['x'] * zoom + ox
                        ty = tgt['y'] * zoom + oy
                        
                        min_x, max_x = min(sx, tx), max(sx, tx)
                        min_y, max_y = min(sy, ty), max(sy, ty)
                        
                        # Pad by the node width to account for the connection points on edges
                        pad = 400 * zoom
                        if max_x + pad >= 0 and min_x - pad <= width and max_y + pad >= 0 and min_y - pad <= height:
                            self._draw_edge(rv, src, tgt, i_edge, elabel, ecol,
                                            ox, oy, zoom, width, height, st, at)

            # ?? in-progress link line ??????????????????????????????????????????
            if g._link_from and g._link_from in node_map:
                src = node_map[g._link_from]
                import pygame
                sx = int(src['x'] * zoom + ox + src['w'] * zoom)
                sy = int(src['y'] * zoom + oy + src['h'] * zoom * 0.5)
                cvs = rv.canvas()
                pts = _vng_bezier_points(sx, sy, g._link_mx, g._link_my)
                col = pygame.Color(VN_TEAL)
                for j in range(len(pts) - 1):
                    cvs.line(col, pts[j], pts[j+1], max(2, int(3*zoom)))

            # ?? draw nodes (with ports) ????????????????????????????????????????
            for n in nodes:
                nx = n['x'] * zoom + ox
                ny = n['y'] * zoom + oy
                nw = n['w'] * zoom
                nh = n['h'] * zoom
                
                # Culling: Only draw node if it is visible on screen
                if nx + nw >= -100 and nx <= width + 100 and ny + nh >= -100 and ny <= height + 100:
                    self._draw_node(rv, n, ox, oy, zoom, width, height, st, at)

            # ?? Lasso Selection Rectangle ??????????????????????????????????????
            if g._lasso_start and g._lasso_end:
                import pygame
                lx = int(g._lasso_start[0] * zoom + ox)
                ty = int(g._lasso_start[1] * zoom + oy)
                rx = int(g._lasso_end[0] * zoom + ox)
                by = int(g._lasso_end[1] * zoom + oy)
                
                rect_x = min(lx, rx)
                rect_y = min(ty, by)
                rect_w = abs(rx - lx)
                rect_h = abs(by - ty)
                
                cvs = rv.canvas()
                lasso_fill = pygame.Color(VN_ACC)
                lasso_fill.a = 50
                cvs.rect(lasso_fill, (rect_x, rect_y, rect_w, rect_h), 0)
                cvs.rect(pygame.Color(VN_ACC), (rect_x, rect_y, rect_w, rect_h), max(1, int(2*zoom)))

            # ?? minimap overlay ????????????????????????????????????????????????
            self._draw_minimap(rv, nodes, width, height, ox, oy, zoom, st, at)

            # Clip rendering to boundaries (prevents spilling onto toolbars/sidebars when zoomed/panned)
            return rv.subsurface((0, 0, width, height))

        def _draw_node(self, rv, n, ox, oy, zoom, W, H, st, at):
            import pygame
            x  = int(n['x'] * zoom + ox)
            y  = int(n['y'] * zoom + oy)
            w  = int(n['w'] * zoom)
            h  = int(n['h'] * zoom)
            selected = (n['id'] == vng.selected_id) or (n['id'] in getattr(vng, 'selected_ids', set()))

            # ── Folder node ─────────────────────────────────────────────────────
            if n.get('kind') == 'folder':
                drop_target = (getattr(vng, '_drag_over_folder', None) == n['id'])
                border_col = "#44ff88" if drop_target else (VN_ACC if selected else "#d4961e")
                cvs = rv.canvas()

                # Dark amber body — green tint when a scene is being dragged over
                if drop_target:
                    body_col = pygame.Color("#0d2a12")
                elif selected:
                    body_col = pygame.Color("#2e1f08")
                else:
                    body_col = pygame.Color("#1f1505")
                cvs.rect(body_col, (x, y, w, h), 0)

                # Folder-tab at the top-left (wider tab for legibility)
                tab_w = max(16, int(w * 0.4))
                tab_h = max(4, int(8 * zoom))
                cvs.rect(pygame.Color("#d4961e"), (x, y - tab_h, tab_w, tab_h + 2), 0)

                # Amber border (drawn after tab so it sits on top)
                cvs.rect(pygame.Color(border_col), (x, y, w, h), 2)

                # Left accent strip
                cvs.rect(pygame.Color("#d4961e"), (x, y, 4, h), 0)

                if zoom >= 0.5:
                    text_w  = w - 14  # usable text width
                    pad_x   = x + 10

                    # Folder icon drawn with simple geometric shapes (no emoji needed)
                    icon_x  = pad_x
                    icon_y  = y + int(h * 0.10)
                    icon_w  = max(18, int(22 * zoom))
                    icon_h  = max(14, int(16 * zoom))
                    icon_tab_w = max(6, int(9 * zoom))
                    icon_tab_h = max(3, int(4 * zoom))
                    icon_col = pygame.Color("#d4961e")
                    icon_inner = pygame.Color("#3a2000")
                    # Tab
                    cvs.rect(icon_col, (icon_x, icon_y, icon_tab_w, icon_tab_h), 0)
                    # Body
                    cvs.rect(icon_col, (icon_x, icon_y + icon_tab_h - 1, icon_w, icon_h), 0)
                    cvs.rect(icon_inner, (icon_x + 2, icon_y + icon_tab_h + 1, icon_w - 4, icon_h - 4), 0)

                    # Label text next to / below the icon
                    lbl_col = VN_ACC if selected else "#f0d080"
                    lbl_d = Text(n['label'], font=VN_FONTB, size=max(10, int(14 * zoom)), color=lbl_col, outlines=[])
                    lbl_r = renpy.render(lbl_d, text_w, 26, st, at)
                    rv.blit(lbl_r, (pad_x, y + int(h * 0.46)))

                    # Scene count sub-label
                    sc_count = n.get('sc_count', 0)
                    cnt_text = f"{sc_count} scene{'s' if sc_count != 1 else ''}"
                    cnt_d = Text(cnt_text, font=VN_FONT, size=max(9, int(11 * zoom)), color=VN_FAINT, outlines=[])
                    cnt_r = renpy.render(cnt_d, text_w, 18, st, at)
                    rv.blit(cnt_r, (pad_x, y + int(h * 0.71)))

                # Ports
                if zoom >= 0.5:
                    pr = max(5, int(6 * zoom))
                    cvs.circle(pygame.Color(VN_TEAL), (x, y + h // 2), pr, 0)
                    cvs.circle(pygame.Color(VN_BG0),  (x, y + h // 2), max(2, pr - 2), 0)
                    out_edges = n['out_edges']
                    count = max(1, len(out_edges))
                    for i_p, (_, _, ecol) in enumerate(out_edges):
                        step_y = h / (count + 1)
                        opy = y + int(step_y * (i_p + 1))
                        opx = x + w
                        cvs.circle(pygame.Color(ecol), (opx, opy), pr, 0)
                        cvs.circle(pygame.Color(VN_BG0), (opx, opy), max(2, pr - 2), 0)
                return

            # ── Scene node ──────────────────────────────────────────────────────
            renaming = (vng._rename_id == n['id'])

            # DIM NOT-MATCHING NODES (Search feature)
            matched = True
            if vng.search_query:
                sq = vng.search_query.lower()
                matched = (sq in n['label'].lower())
                if not matched and n.get('sc'):
                    for ev in n['sc'].get('events', []):
                        if sq in ev.get('text', '').lower() or sq in ev.get('prompt', '').lower():
                            matched = True
                            break
            start = (n['id'] == (vns.project.get('start') if vns.project else None))
            is_end = not start and len(n.get('out_edges', [])) == 0

            # pick border colour
            if selected or renaming:
                border_col = VN_ACC
            elif start:
                border_col = VN_TEAL
            elif is_end:
                border_col = VN_ACC
            else:
                border_col = VN_BDR

            # For zoom >= 0.5 we use fast pygame rects exclusively
            if zoom >= 0.5:
                # ── Node body ──────────────────────────────────────────────
                body_col = VN_SEL if selected else VN_BG2
                body = renpy.render(Solid(body_col), w, h, st, at)
                rv.blit(body, (x, y))

                cvs = rv.canvas()

                # ── Coloured header band across top ────────────────────────
                band_h   = max(6, int(8 * zoom))
                band_col = VN_TEAL if start else (VN_ACC if is_end else (VN_ACC if (selected or renaming) else "#3a3f6e"))
                cvs.rect(pygame.Color(band_col), (x, y, w, band_h), 0)

                # ── Left accent strip ──────────────────────────────────────
                strip_col = VN_TEAL if start else (VN_ACC if is_end else (VN_ACC if (selected or renaming) else "#555a8a"))
                cvs.rect(pygame.Color(strip_col), (x, y, 4, h), 0)

                # ── Border ────────────────────────────────────────────────
                cvs.rect(pygame.Color(border_col), (x, y, w, h), 2)

                # ── Label — truncated to one line with ellipsis ────────────
                raw_label = n['label']
                MAX_CHARS = 22   # fits ~200px card at 16px bold
                display_label = (raw_label[:MAX_CHARS] + "…") if len(raw_label) > MAX_CHARS else raw_label
                lbl_size = max(12, int(16 * zoom))
                lbl_col  = "#ffffff" if (selected or renaming) else "#e8eaf6"
                lbl_d = Text(
                    display_label,
                    font    = VN_FONTB,
                    size    = lbl_size,
                    color   = lbl_col,
                    outlines= [],
                )
                lbl_r = renpy.render(lbl_d, w - 16, int(lbl_size * 1.6), st, at)
                rv.blit(lbl_r, (x + 10, y + band_h + max(4, int(6 * zoom))))

                # ── Event count — pinned to bottom of card ─────────────────
                ev_count = len(n['sc'].get('events', [])) if n.get('sc') else 0
                sub_size = max(10, int(11 * zoom))
                sub_col  = "#9fa8da" if selected else "#8888aa"
                sub_d = Text(
                    f"{ev_count} event{'s' if ev_count != 1 else ''}",
                    font    = VN_FONT,
                    size    = sub_size,
                    color   = sub_col,
                    outlines= [],
                )
                sub_r = renpy.render(sub_d, w - 16, int(sub_size * 1.4), st, at)
                # Pin to 8px above card bottom
                sub_y = y + h - int(sub_size * 1.4) - max(6, int(8 * zoom))
                rv.blit(sub_r, (x + 10, sub_y))

                # ── "START" badge ──────────────────────────────────────────
                if start:
                    badge_d  = Text("START", font=VN_FONTB, size=10, color=VN_BG0, outlines=[])
                    badge_bg = renpy.render(Solid(VN_TEAL), 46, 18, st, at)
                    badge_r  = renpy.render(badge_d, 46, 18, st, at)
                    rv.blit(badge_bg, (x + w - 50, y + 4))
                    rv.blit(badge_r,  (x + w - 48, y + 6))

                # ── "END" badge ────────────────────────────────────────────
                if is_end:
                    badge_d  = Text("END", font=VN_FONTB, size=10, color=VN_BG0, outlines=[])
                    badge_bg = renpy.render(Solid(VN_ACC), 36, 18, st, at)
                    badge_r  = renpy.render(badge_d, 36, 18, st, at)
                    rv.blit(badge_bg, (x + w - 40, y + 4))
                    rv.blit(badge_r,  (x + w - 32, y + 6))


            else:
                # FAST RENDERING FOR ZOOM < 0.5 (Pygame rects)
                cvs = rv.canvas()
                body_col = VN_SEL if selected else VN_BG2
                cvs.rect(pygame.Color(body_col), (x, y, w, h), 0)
                bthick = max(1, int(2*zoom))
                cvs.rect(pygame.Color(border_col), (x, y, w, h), bthick)

            # SEARCH HIGHLIGHT OR DIMMING
            if vng.search_query:
                cvs = rv.canvas()
                if matched:
                    cvs.rect(pygame.Color("#ffeaa7"), (x-2, y-2, w+4, h+4), max(2, int(3*zoom)))
                else:
                    dim_col = pygame.Color("#000000")
                    dim_col.a = 160
                    cvs.rect(dim_col, (x, y, w, h), 0)

            # ?? Node Ports (Godot-style)
            if zoom >= 0.5:
                cvs = rv.canvas()
                pr  = max(5, int(6 * zoom))
                in_px = x
                in_py = y + h // 2
                cvs.circle(pygame.Color(VN_TEAL), (in_px, in_py), pr, 0)
                cvs.circle(pygame.Color(VN_BG0),  (in_px, in_py), max(2, pr - 2), 0)
                out_edges = n['out_edges']
                count = max(1, len(out_edges))
                for i_p, (_, _, ecol) in enumerate(out_edges):
                    step_y = h / (count + 1)
                    opy = y + int(step_y * (i_p + 1))
                    opx = x + w
                    cvs.circle(pygame.Color(ecol), (opx, opy), pr, 0)
                    cvs.circle(pygame.Color(VN_BG0), (opx, opy), max(2, pr - 2), 0)

        def _draw_edge(self, rv, src, tgt, i_edge, label, color, ox, oy, zoom, W, H, st, at):
            import pygame
            cvs = rv.canvas()

            # ?? Port-anchored endpoints ????????????????????????????????????????
            out_count = max(1, len(src['out_edges']))
            step_y_src = src['h'] / (out_count + 1)
            sx = int(src['x'] * zoom + ox + src['w'] * zoom)
            sy = int(src['y'] * zoom + oy + step_y_src * (i_edge + 1) * zoom)
            # input port is always vertically centered on target
            tx = int(tgt['x'] * zoom + ox)
            ty = int(tgt['y'] * zoom + oy + tgt['h'] * zoom * 0.5)

            # ?? Bezier spline ??????????????????????????????????????????????????
            segments = max(4, int(24 * zoom)) # Less segments when zoomed out
            pts = _vng_bezier_points(sx, sy, tx, ty, segments=segments)
            col = pygame.Color(color)
            line_w = max(2, int(2 * zoom))
            
            if zoom < 0.5:
                # FAST RENDERING: Straight line, no arrowhead
                cvs.line(col, (sx, sy), (tx, ty), line_w)
            else:
                for j in range(len(pts) - 1):
                    cvs.line(col, pts[j], pts[j+1], line_w)

                # ?? Arrowhead - angle of last segment ?????????????????????????????
                if len(pts) >= 2:
                    dx = pts[-1][0] - pts[-2][0]
                    dy = pts[-1][1] - pts[-2][1]
                    dist = max(1, math.hypot(dx, dy))
                    ux, uy = dx / dist, dy / dist
                    arr_len = max(8, int(14 * zoom))
                    ax = tx - ux * arr_len
                    ay = ty - uy * arr_len
                    px = -uy * arr_len * 0.45
                    py =  ux * arr_len * 0.45
                    cvs.polygon(col, [
                        (tx, ty),
                        (int(ax + px), int(ay + py)),
                        (int(ax - px), int(ay - py))
                    ])

        def _draw_minimap(self, rv, nodes, W, H, ox, oy, zoom, st, at):
            """Draw a 160x120 minimap in the bottom-right corner."""
            import pygame
            if not nodes:
                return

            MM_W, MM_H = 160, 120
            MM_PAD = 12
            mm_x = W - MM_W - MM_PAD
            mm_y = H - MM_H - MM_PAD

            # semi-transparent dark background
            bg = renpy.render(Solid("#12141acc"), MM_W, MM_H, st, at)
            rv.blit(bg, (mm_x, mm_y))

            # border
            cvs = rv.canvas()
            bdr_col = pygame.Color(VN_BDR)
            cvs.rect(bdr_col, pygame.Rect(mm_x, mm_y, MM_W, MM_H), 1)

            # compute bounding box of all nodes in world-space
            xs = [n['x'] for n in nodes]
            ys = [n['y'] for n in nodes]
            ws = [n['w'] for n in nodes]
            hs = [n['h'] for n in nodes]
            min_x = min(xs) - 20
            min_y = min(ys) - 20
            max_x = max(x + w for x, w in zip(xs, ws)) + 20
            max_y = max(y + h for y, h in zip(ys, hs)) + 20
            bw = max(1, max_x - min_x)
            bh = max(1, max_y - min_y)

            def _world_to_mm(wx, wy):
                return (
                    int(mm_x + (wx - min_x) / bw * MM_W),
                    int(mm_y + (wy - min_y) / bh * MM_H)
                )

            # draw each node as a tiny block
            for n in nodes:
                nx, ny = _world_to_mm(n['x'], n['y'])
                nw = max(4, int(n['w'] / bw * MM_W))
                nh = max(3, int(n['h'] / bh * MM_H))
                selected = (n['id'] == vng.selected_id)
                nc = pygame.Color(VN_ACC if selected else VN_BG3)
                cvs.rect(nc, pygame.Rect(nx, ny, nw, nh), 0)
                if selected:
                    cvs.rect(pygame.Color(VN_ACC), pygame.Rect(nx, ny, nw, nh), 1)

            # draw edges as thin lines on minimap
            node_map = {n['id']: n for n in nodes}
            for src in nodes:
                for tid, _, ecol in src['out_edges']:
                    if tid in node_map:
                        tgt = node_map[tid]
                        sp = _world_to_mm(src['x'] + src['w'], src['y'] + src['h']//2)
                        tp = _world_to_mm(tgt['x'], tgt['y'] + tgt['h']//2)
                        cvs.line(pygame.Color(ecol), sp, tp, 1)

            # viewport rectangle - what region is currently visible
            # visible world rect: world_x = (screen_x - ox) / zoom
            vp_wx0 = (0    - ox) / zoom
            vp_wy0 = (0    - oy) / zoom
            vp_wx1 = (W    - ox) / zoom
            vp_wy1 = (H    - oy) / zoom
            vp_ax, vp_ay = _world_to_mm(vp_wx0, vp_wy0)
            vp_bx, vp_by = _world_to_mm(vp_wx1, vp_wy1)
            vp_rect = pygame.Rect(
                max(mm_x, vp_ax), max(mm_y, vp_ay),
                min(MM_W, vp_bx - vp_ax), min(MM_H, vp_by - vp_ay)
            )
            cvs.rect(pygame.Color("#ffffffaa"), vp_rect, 1)

            # store minimap bounds for click handling
            vng._mm_rect = (mm_x, mm_y, MM_W, MM_H, min_x, min_y, bw, bh)

        # ?? Input ?????????????????????????????????????????????????????????????

        def event(self, ev, x, y, st):
            import pygame
            
            # Immediately ignore mouse events that are outside our clipped canvas area
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                w = getattr(self, '_last_w', 9999)
                h = getattr(self, '_last_h', 9999)
                if not (0 <= x <= w and 0 <= y <= h):
                    return None

            g     = vng
            zoom  = g.zoom
            nodes = _vng_build_nodes(vns.project, g.layout)
            ox, oy = g.offset_x, g.offset_y

            # ?? LEFT MOUSE DOWN ??????????????????????????????????????????????
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if getattr(g, 'tool', 'pointer') == 'pan':
                    g.selected_id    = None
                    g._last_click_st = st
                    g._rename_id     = None
                    g._drag_node     = None
                    g._pan_ready     = True
                    g._pan_active    = False
                    g._pan_mx        = ev.pos[0]
                    g._pan_my        = ev.pos[1]
                    renpy.restart_interaction()
                    raise renpy.IgnoreEvent()

                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    g.selected_id  = None
                    g.selected_ids = set()
                    g._lasso_start = ((x - ox) / zoom, (y - oy) / zoom)
                    g._lasso_end   = g._lasso_start
                    renpy.restart_interaction()
                    raise renpy.IgnoreEvent()

                hit = _vng_node_at(nodes, x, y, ox, oy, zoom)
                if hit:
                    # Double-click a FOLDER ? enter it
                    if hit.get('kind') == 'folder' and hit['id'] == g.selected_id and (st - g._last_click_st) < 0.38:
                        g.current_folder = hit['id']
                        g.selected_id    = None
                        g._last_click_st = 0
                        g.offset_x = 40.0
                        g.offset_y = 40.0
                        renpy.restart_interaction()
                        raise renpy.IgnoreEvent()

                    # Double-click a SCENE ? rename mode
                    if hit.get('kind') != 'folder' and hit['id'] == g.selected_id and (st - g._last_click_st) < 0.38:
                        sc_hit = vn_find_scene(vns.project, hit['id'])
                        if sc_hit:
                            g._rename_id     = hit['id']
                            g._rename_buf    = sc_hit.get('label', '')
                            g._last_click_st = 0
                            renpy.restart_interaction()
                            raise renpy.IgnoreEvent()

                    g._last_click_st = st
                    if g.selected_id != hit['id']:
                        g.selected_id = hit['id']
                        g._rename_id  = None
                        renpy.restart_interaction()

                    g._drag_node      = hit['id']
                    g._drag_moved     = False
                    g._drag_ox        = (x - ox) / zoom - hit['x']
                    g._drag_oy        = (y - oy) / zoom - hit['y']
                    g._drag_start_pos = (hit['x'], hit['y'])
                    raise renpy.IgnoreEvent()
                else:
                    # Double-click empty space ? create scene (only valid in a folder or on main)
                    if st - g._last_click_st < 0.35:
                        sc = vn_new_scene("New Scene")
                        target_x = (x - ox) / zoom - 95
                        target_y = (y - oy) / zoom - 40
                        sc_id = sc['id']
                        cur_folder = getattr(g, 'current_folder', None)
                        def _do_add():
                            vns.project['scenes'].append(sc)
                            g.layout[sc_id] = (target_x, target_y)
                            # If inside a folder, auto-assign scene to it
                            if cur_folder is not None:
                                for f in vns.project.get('folders', []):
                                    if f['id'] == cur_folder:
                                        f.setdefault('scene_ids', []).append(sc_id)
                                        break
                            g.selected_id = sc_id
                            vns.save()
                            renpy.restart_interaction()
                        def _undo_add():
                            if sc in vns.project['scenes']:
                                vns.project['scenes'].remove(sc)
                            g.layout.pop(sc_id, None)
                            if cur_folder is not None:
                                for f in vns.project.get('folders', []):
                                    if f['id'] == cur_folder and sc_id in f.get('scene_ids', []):
                                        f['scene_ids'].remove(sc_id)
                            if g.selected_id == sc_id:
                                g.selected_id = None
                            vns.save()
                            renpy.restart_interaction()
                        vns.history.commit(f"Add Scene '{sc['label']}'", _do_add, _undo_add)
                        g._last_click_st = 0
                        renpy.redraw(self, 0)
                        raise renpy.IgnoreEvent()

                    if g.selected_id is not None or bool(getattr(g, 'selected_ids', False)):
                        g.selected_id  = None
                        g.selected_ids = set()
                        renpy.restart_interaction()

                    g._last_click_st = st
                    g._rename_id     = None
                    g._drag_node     = None
                    renpy.restart_interaction()
                    raise renpy.IgnoreEvent()

            # ?? LEFT MOUSE UP ?????????????????????????????????????????????????
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                # Check if dropped onto a folder
                if g._drag_node and g._drag_moved:
                    drop_fld_id = getattr(g, '_drag_over_folder', None)
                    if drop_fld_id and g._drag_node:
                        # The scene was dragged onto a folder — assign it
                        sc_id = g._drag_node
                        # Only assign scene nodes (not folders onto folders)
                        is_scene = bool(vn_find_scene(vns.project, sc_id))
                        if is_scene:
                            # Remove from any current folder first
                            old_folder_id = _vng_scene_folder(vns.project, sc_id)
                            def _do_assign(sid=sc_id, new_fid=drop_fld_id, old_fid=old_folder_id):
                                # Remove from old folder
                                if old_fid:
                                    for f in vns.project.get('folders', []):
                                        if f['id'] == old_fid and sid in f.get('scene_ids', []):
                                            f['scene_ids'].remove(sid)
                                # Add to new folder
                                for f in vns.project.get('folders', []):
                                    if f['id'] == new_fid:
                                        if sid not in f.get('scene_ids', []):
                                            f.setdefault('scene_ids', []).append(sid)
                                        break
                                vns.save()
                                renpy.restart_interaction()
                            def _undo_assign(sid=sc_id, new_fid=drop_fld_id, old_fid=old_folder_id):
                                # Remove from new folder
                                for f in vns.project.get('folders', []):
                                    if f['id'] == new_fid and sid in f.get('scene_ids', []):
                                        f['scene_ids'].remove(sid)
                                # Restore to old folder if there was one
                                if old_fid:
                                    for f in vns.project.get('folders', []):
                                        if f['id'] == old_fid:
                                            f.setdefault('scene_ids', []).append(sid)
                                vns.save()
                                renpy.restart_interaction()
                            fld_lbl = next((f['label'] for f in vns.project.get('folders', []) if f['id'] == drop_fld_id), 'Folder')
                            sc_lbl  = vn_find_scene(vns.project, sc_id).get('label', 'Scene')
                            vns.history.commit(f"Move '{sc_lbl}' into '{fld_lbl}'", _do_assign, _undo_assign)
                            vns.notify(f"'{sc_lbl}' moved into '{fld_lbl}'", "ok")
                            g._drag_node = None  # clear so normal move logic doesn't also fire

                g._drag_over_folder = None

                if g._drag_node and g._drag_moved:
                    node_id   = g._drag_node
                    start_pos = g._drag_start_pos
                    end_pos   = g.layout.get(node_id, (0,0))
                    if start_pos != end_pos:
                        # Find if this node is a folder so we can persist its position
                        moved_fld = next((f for f in vns.project.get('folders', []) if f['id'] == node_id), None)
                        def _do_drag(nid=node_id, ep=end_pos, fld=moved_fld):
                            g.layout[nid] = ep
                            if fld:
                                fld['x'], fld['y'] = ep
                            g.save_layout(vns.project)
                            vns.save()
                        def _undo_drag(nid=node_id, sp=start_pos, fld=moved_fld):
                            g.layout[nid] = sp
                            if fld:
                                fld['x'], fld['y'] = sp
                            g.save_layout(vns.project)
                            vns.save()
                        vns.history.commit("Move Node", _do_drag, _undo_drag)

                was_lasso      = g._lasso_start is not None
                was_dragging   = g._drag_moved
                was_panning    = g._pan_active
                g._drag_node   = None
                g._drag_moved  = False
                g._pan_ready   = False
                g._pan_active  = False
                g._lasso_start = None
                g._lasso_end   = None
                if was_dragging or was_panning or was_lasso:
                    if was_lasso:
                        renpy.restart_interaction()
                    else:
                        renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()

            # ?? RIGHT/MIDDLE MOUSE DOWN (Draw Link or Pan) ???????????????????
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (2, 3):
                hit = _vng_node_at(nodes, x, y, ox, oy, zoom) if ev.button == 3 else None
                if hit:
                    g._link_from = hit['id']
                    g._link_mx   = x
                    g._link_my   = y
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                else:
                    g._pan_ready  = True
                    g._pan_active = False
                    g._pan_mx     = ev.pos[0]
                    g._pan_my     = ev.pos[1]
                    raise renpy.IgnoreEvent()

            # ?? RIGHT/MIDDLE MOUSE UP (Finish Link or Pan) ???????????????????
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button in (2, 3):
                if g._link_from and ev.button == 3:
                    target = _vng_node_at(nodes, x, y, ox, oy, zoom)
                    if target and target['id'] != g._link_from:
                        src_sc = vn_find_scene(vns.project, g._link_from)
                        if src_sc:
                            ev_jump = vn_new_jump(scene_id=target['id'])
                            def _do_link():
                                src_sc['events'].append(ev_jump)
                                vns.save()
                            def _undo_link():
                                if ev_jump in src_sc['events']:
                                    src_sc['events'].remove(ev_jump)
                                vns.save()
                            vns.history.commit(f"Link {src_sc.get('label')} to {target.get('label')}", _do_link, _undo_link)
                            vns.notify(f"Linked {src_sc.get('label')} ➡️ {target.get('label')}", "ok")
                    ## Always clear - even on a miss - so no ghost line lingers
                    g._link_from = None
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                elif (g._pan_ready or g._pan_active) and ev.button in (2, 3):
                    was_panning = g._pan_active
                    g._pan_ready  = False
                    g._pan_active = False
                    if was_panning:
                        renpy.redraw(self, 0)
                        raise renpy.IgnoreEvent()

            # ?? MOUSE MOTION ??????????????????????????????????????????????????
            elif ev.type == pygame.MOUSEMOTION:
                hit = _vng_node_at(nodes, x, y, ox, oy, zoom)
                new_hover = hit['id'] if hit else None
                if getattr(g, '_hover_node', None) != new_hover:
                    g._hover_node = new_hover
                    renpy.restart_interaction()

                if g._lasso_start:
                    g._lasso_end = ((x - ox) / zoom, (y - oy) / zoom)
                    lx = min(g._lasso_start[0], g._lasso_end[0])
                    rx = max(g._lasso_start[0], g._lasso_end[0])
                    ty = min(g._lasso_start[1], g._lasso_end[1])
                    by = max(g._lasso_start[1], g._lasso_end[1])
                    g.selected_ids = set()
                    for n in nodes:
                        if (n['x'] < rx) and (n['x'] + n['w'] > lx) and (n['y'] < by) and (n['y'] + n['h'] > ty):
                            g.selected_ids.add(n['id'])
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                elif g._link_from:
                    g._link_mx = x
                    g._link_my = y
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                elif g._drag_node:
                    # Update drag-over-folder highlight
                    new_dof = None
                    for n in nodes:
                        if n.get('kind') == 'folder' and n['id'] != g._drag_node:
                            fx = ox + n['x'] * zoom
                            fy = oy + n['y'] * zoom
                            fw = n['w'] * zoom
                            fh = n['h'] * zoom
                            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                                new_dof = n['id']
                                break
                    if getattr(g, '_drag_over_folder', None) != new_dof:
                        g._drag_over_folder = new_dof
                        renpy.redraw(self, 0)

                    for n in nodes:
                        if n['id'] == g._drag_node:
                            new_x = (x - ox) / zoom - g._drag_ox
                            new_y = (y - oy) / zoom - g._drag_oy
                            g.layout[g._drag_node] = (new_x, new_y)
                            g._drag_moved = True
                            break
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                elif g._pan_ready or g._pan_active:
                    g._pan_active = True
                    g._pan_ready  = False
                    g.offset_x += ev.pos[0] - g._pan_mx
                    g.offset_y += ev.pos[1] - g._pan_my
                    g._pan_mx = ev.pos[0]
                    g._pan_my = ev.pos[1]
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()

            # ?? SCROLL WHEEL - zoom toward cursor ?????????????????????????????
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5):
                delta     = 0.12 if ev.button == 4 else -0.12
                old_zoom  = g.zoom
                g.zoom    = max(0.25, min(3.0, old_zoom + delta))
                # keep the point under the cursor stationary
                scale     = g.zoom / old_zoom
                g.offset_x = x - (x - g.offset_x) * scale
                g.offset_y = y - (y - g.offset_y) * scale
                renpy.redraw(self, 0)
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()

        def visit(self):
            return []

    def _vng_begin_link(node_id):
        vng._link_from = node_id
        renpy.restart_interaction()

    def _vng_auto_layout():
        """Compute a level-based (DAG) auto-layout for the graph."""
        if not vns.project:
            return
            
        scenes = vns.project.get('scenes', [])
        if not scenes:
            return
            
        # 1. Build adjacency list
        edges = {}
        for sc in scenes:
            edges[sc['id']] = []
            for ev in sc.get('events', []):
                if ev.get('type') == 'choice':
                    for opt in ev.get('opts', []):
                        if opt.get('scene') and opt['scene'] not in edges[sc['id']]:
                            edges[sc['id']].append(opt['scene'])
                elif ev.get('type') == 'jump' and ev.get('scene_id') and ev['scene_id'] not in edges[sc['id']]:
                    edges[sc['id']].append(ev['scene_id'])

        # 2. Find root nodes
        in_degrees = {sc['id']: 0 for sc in scenes}
        for u in edges:
            for v in edges[u]:
                if v in in_degrees:
                    in_degrees[v] += 1
                    
        roots = [sid for sid, deg in in_degrees.items() if deg == 0]
        start_id = vns.project.get('start')
        
        # Priority to the official start node
        if start_id in in_degrees:
            if start_id in roots:
                roots.remove(start_id)
            roots.insert(0, start_id)
            
        if not roots:
            roots = [scenes[0]['id']]

        # 3. BFS to assign levels
        levels = {}
        queue = [(r, 0) for r in roots]
        visited = set(roots)
        
        while queue:
            curr, lvl = queue.pop(0)
            if lvl not in levels:
                levels[lvl] = []
            levels[lvl].append(curr)
            
            for child in edges.get(curr, []):
                if child not in visited and child in in_degrees:
                    visited.add(child)
                    queue.append((child, lvl + 1))
                    
        # Catch any disconnected components
        unvisited = [sc['id'] for sc in scenes if sc['id'] not in visited]
        if unvisited:
            max_lvl = max(levels.keys()) + 1 if levels else 0
            levels[max_lvl] = unvisited

        # 4. Assign positions
        X_SPACING = 340
        Y_SPACING = 160
        
        vng.layout.clear()
        
        for lvl in sorted(levels.keys()):
            col_nodes = levels[lvl]
            # Vertically center the column roughly
            start_y = max(60, 200 - (len(col_nodes) * Y_SPACING) / 2)
            
            for i, sid in enumerate(col_nodes):
                x = 80 + (lvl * X_SPACING)
                y = int(start_y + (i * Y_SPACING))
                vng.layout[sid] = (x, y)
                
        # Layout folders at the bottom
        folders = vns.project.get('folders', [])
        max_y = max((pos[1] for pos in vng.layout.values()), default=0) + 300
        for i, fld in enumerate(folders):
            vng.layout[fld['id']] = (80 + i * X_SPACING, int(max_y))

        vns.project['layout'] = {k: list(v) for k, v in vng.layout.items()}
        vng.offset_x = 40.0
        vng.offset_y = 40.0
        vng.zoom = 1.0
        vns.save()
        renpy.restart_interaction()

    def _vng_add_folder():
        """Create a new empty folder on the main graph at the current viewport centre."""
        if not vns.project: return
        if getattr(vng, 'current_folder', None) is not None:
            vns.notify("Can't create folders inside a folder.", "warn")
            return
        folders = vns.project.setdefault('folders', [])
        idx = len(folders) + 1
        x = max(0, -vng.offset_x / vng.zoom) + 80
        y = max(0, -vng.offset_y / vng.zoom) + 80
        rid = ''.join(_rand_mod.choices(_str_mod.ascii_lowercase + _str_mod.digits, k=6))
        fld = {
            'id':        f"fld_{rid}",
            'label':     f"Folder {idx}",
            'x':         x,
            'y':         y,
            'scene_ids': [],
        }
        def _do():
            vns.project['folders'].append(fld)
            vng.layout[fld['id']] = (x, y)
            vns.save()
            renpy.restart_interaction()
        def _undo():
            if fld in vns.project.get('folders', []):
                vns.project['folders'].remove(fld)
            vng.layout.pop(fld['id'], None)
            vns.save()
            renpy.restart_interaction()
        vns.history.commit("Add Folder", _do, _undo)

    # ??? Graph singleton state ?????????????????????????????????????????????????

    class _VNGState:
        def __init__(self):
            self.selected_id  = None       # primary selected id (for inspector)
            self.selected_ids = set()      # multi-selected nodes
            self._lasso_start = None
            self._lasso_end   = None
            self.layout       = {}         # node_id -> (x, y)
            self.offset_x     = 40.0
            self.offset_y     = 40.0
            self.zoom         = 1.0
            self.inspector_w  = 300
            self._mm_rect     = None
            self.fold_state   = {}
            self.search_query = ""
            self._hover_node  = None
            self.current_folder = None    # None = main graph; folder_id = inside folder
            self._folder_stack  = []      # breadcrumb for future nesting (reserved)

            ## Inline rename state
            self._rename_id    = None
            self._rename_buf   = ""

            ## Canvas interaction state
            self._drag_node      = None
            self._drag_ox        = 0.0
            self._drag_oy        = 0.0
            self._drag_moved     = False
            self._drag_start_pos = (0.0, 0.0)
            self._drag_over_folder = None  # folder id currently under a dragged scene
            self._pan_ready      = False
            self._pan_active     = False
            self._pan_mx         = 0
            self._pan_my         = 0
            self._link_from      = None
            self._link_mx        = 0
            self._link_my        = 0
            self._last_click_st  = 0

        @property
        def cam_x(self):
            return 5000.0 - self.offset_x

        @cam_x.setter
        def cam_x(self, val):
            self.offset_x = 5000.0 - val
            renpy.restart_interaction()

        @property
        def cam_y(self):
            return 5000.0 - self.offset_y

        @cam_y.setter
        def cam_y(self, val):
            self.offset_y = 5000.0 - val
            renpy.restart_interaction()

        def reset_layout(self, project):
            """Load saved layout from the project, falling back to auto-positions."""
            self.layout = {}
            if project:
                saved = project.get('layout', {})
                for i, sc in enumerate(project.get('scenes', [])):
                    sid = sc['id']
                    if sid in saved:
                        self.layout[sid] = tuple(saved[sid])  # JSON stores lists, need tuples
                    else:
                        self.layout[sid] = _vng_default_pos(i, len(project['scenes']))
                # Restore folder positions from saved layout or their own x/y
                for fld in project.get('folders', []):
                    fid = fld['id']
                    if fid in saved:
                        self.layout[fid] = tuple(saved[fid])
                    else:
                        self.layout[fid] = (fld.get('x', 200), fld.get('y', 200))
            self.offset_x = 40.0
            self.offset_y = 40.0
            self.tool = "pointer"
            self.selected_id  = None
            self.selected_ids = set()
            self.search_query = ""
            self._rename_id = None
            self._rename_buf = ""

        def save_layout(self, project):
            """Flush current vng.layout into the project dict so vns.save() captures it."""
            if project is None:
                return
            project['layout'] = {k: list(v) for k, v in self.layout.items()}

        def exit_folder(self):
            """Return to the main graph from inside a folder."""
            self.current_folder = None
            self.selected_id    = None
            self.offset_x       = 40.0
            self.offset_y       = 40.0
            renpy.restart_interaction()

        @property
        def selected_scene(self):
            """The selected scene object, or None (including if a folder is selected)."""
            if vns.project and self.selected_id:
                return vn_find_scene(vns.project, self.selected_id)
            return None

        @property
        def selected_folder(self):
            """The selected folder object, or None."""
            if vns.project and self.selected_id:
                return next((f for f in vns.project.get('folders', []) if f['id'] == self.selected_id), None)
            return None

        def clear_selection(self):
            self.selected_id = None

        def center_on_node(self, scene_id):
            if scene_id in self.layout:
                nx, ny = self.layout[scene_id]
                self.offset_x = 1200 / 2 - nx * self.zoom - 100
                self.offset_y = 700 / 2 - ny * self.zoom - 50
                renpy.restart_interaction()

    vng = _VNGState()

    def _vng_commit_rename():
        """Apply the rename buffer to the selected scene and exit rename mode."""
        sc = vn_find_scene(vns.project, vng._rename_id) if vng._rename_id else None
        if sc and vng._rename_buf.strip():
            old_label = sc.get('label', '')
            new_label = vng._rename_buf.strip()
            sc_ref = sc
            def _do():
                sc_ref['label'] = new_label
                vns.save()
            def _undo():
                sc_ref['label'] = old_label
                vns.save()
            vns.history.commit(f"Rename Scene '{old_label}' ➡️ '{new_label}'", _do, _undo)
            vns.notify(f"Renamed to '{new_label}'", "ok")
        vng._rename_id  = None
        vng._rename_buf = ""
        renpy.restart_interaction()

    def _vng_start_rename():
        """Enter rename mode for the currently selected node."""
        sc = vn_find_scene(vns.project, vng.selected_id) if vng.selected_id else None
        if sc:
            vng._rename_id  = vng.selected_id
            vng._rename_buf = sc.get('label', '')
            vns.ui['_focus'] = "vn_graph_rename_input"
            renpy.set_focus(None, "vn_graph_rename_input")
        renpy.restart_interaction()

    def _vng_delete_selected():
        """Delete the currently selected scenes/folders and clean up state."""
        if not vns.project:
            return

        targets = set(getattr(vng, 'selected_ids', set()))
        if vng.selected_id:
            targets.add(vng.selected_id)
        if not targets:
            return

        to_remove_scenes  = []
        to_remove_folders = []

        for tid in targets:
            sc = vn_find_scene(vns.project, tid)
            if sc:
                sc_idx = vns.project['scenes'].index(sc)
                pos    = vng.layout.get(tid, (0,0))
                to_remove_scenes.append((sc_idx, sc, pos))
                continue
            fld = next((f for f in vns.project.get('folders', []) if f['id'] == tid), None)
            if fld:
                f_idx = vns.project['folders'].index(fld)
                to_remove_folders.append((f_idx, fld))

        if not to_remove_scenes and not to_remove_folders:
            return

        def _do_del():
            for _, sc, _ in to_remove_scenes:
                if sc in vns.project['scenes']:
                    vns.project['scenes'].remove(sc)
                # Remove from any folder
                for f in vns.project.get('folders', []):
                    if sc['id'] in f.get('scene_ids', []):
                        f['scene_ids'].remove(sc['id'])
                vng.layout.pop(sc['id'], None)
            for _, fld in to_remove_folders:
                if fld in vns.project.get('folders', []):
                    vns.project['folders'].remove(fld)
                vng.layout.pop(fld['id'], None)
            vng.selected_id  = None
            vng.selected_ids = set()
            vns.save()

        def _undo_del():
            for idx, sc, pos in sorted(to_remove_scenes, key=lambda x: x[0]):
                vns.project['scenes'].insert(idx, sc)
                vng.layout[sc['id']] = pos
            for idx, fld in sorted(to_remove_folders, key=lambda x: x[0]):
                vns.project.setdefault('folders', []).insert(idx, fld)
                vng.layout[fld['id']] = (fld.get('x', 200), fld.get('y', 200))
            vns.save()

        count = len(to_remove_scenes) + len(to_remove_folders)
        vns.history.commit(f"Delete {count} item(s)", _do_del, _undo_del)
        vns.notify(f"Deleted {count} item(s)", "warn")
        renpy.restart_interaction()

    # ??? Inspector resize splitter ?????????????????????????????????????????????

    class _VNSplitter(renpy.Displayable):
        """Invisible drag handle that resizes the inspector panel."""

        def __init__(self):
            super(_VNSplitter, self).__init__()
            self._dragging = False
            self._start_x  = 0
            self._start_w  = 0

        def render(self, width, height, st, at):
            rv = renpy.Render(width, height)
            self._last_w = width
            self._last_h = height
            return rv

        def event(self, ev, x, y, st):
            import pygame
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                w = getattr(self, '_last_w', 6)
                h = getattr(self, '_last_h', 9999)
                if 0 <= x <= w and 0 <= y <= h:
                    self._dragging = True
                    self._start_x  = ev.pos[0]
                    self._start_w  = vng.inspector_w
                    raise renpy.IgnoreEvent()
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self._dragging = False
            elif ev.type == pygame.MOUSEMOTION and getattr(self, '_dragging', False):
                delta = self._start_x - ev.pos[0]   # drag left ? wider
                vng.inspector_w = max(200, min(600, self._start_w + delta))
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()

        def visit(self):
            return []


## ?? Graph Screen ?????????????????????????????????????????????????????????????

screen vn_graph_panel():

    ## Re-sync layout keys if project scenes have changed
    python:
        if vns.project:
            for i, sc in enumerate(vns.project.get('scenes', [])):
                if sc['id'] not in vng.layout:
                    vng.layout[sc['id']] = _vng_default_pos(
                        i, len(vns.project['scenes']))

    frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
        side "c r":

            ## ?? Canvas area (Center) ???????????????????????????????????????
            frame background Solid(VN_BG0) xfill True yfill True padding (0, 0):
                vbox spacing 0 xfill True yfill True:

                    ## Twine-style Toolbar - all buttons always visible
                    ## Breadcrumb path bar (shows when inside a folder)
                    $ _in_folder = getattr(vng, 'current_folder', None) is not None
                    if _in_folder:
                        $ _cur_fld = next((f for f in (vns.project.get('folders', []) if vns.project else []) if f['id'] == vng.current_folder), None)
                        frame background Solid("#1e1508") xfill True padding (12, 0) ysize 32:
                            hbox spacing 8 yalign 0.5:
                                textbutton "🏠 Main" style "vn_btn_ghost" padding (6, 3) yalign 0.5:
                                    action Function(vng.exit_folder)
                                text "›" style "vn_t_faint" yalign 0.5
                                text (_cur_fld['label'] if _cur_fld else "Folder") style "vn_t" size 13 color "#e8c060" yalign 0.5

                    $ _sel_sc  = vn_find_scene(vns.project, vng.selected_id) if vng.selected_id and vns.project else None
                    $ _sel_fld = getattr(vng, 'selected_folder', None)
                    frame background Solid(VN_BG1) xfill True padding (16, 0) ysize 48:
                        frame background Solid(VN_BDR) xfill True ysize 1 yalign 1.0 padding (0,0)
                        
                        viewport xfill True ysize 48 mousewheel "horizontal" draggable True scrollbars None:
                            hbox spacing 8 yalign 0.5 yfill True:
                                ## ?? Tools
                                hbox spacing 4 yalign 0.5:
                                    textbutton "✅ Select" style "vn_btn":
                                        selected vng.tool == "pointer"
                                        action SetField(vng, "tool", "pointer")
                                    textbutton "✋ Pan" style "vn_btn":
                                        selected vng.tool == "pan"
                                        action SetField(vng, "tool", "pan")

                                frame background Solid(VN_BDR) xsize 1 ysize 24 padding (0,0) yalign 0.5

                                ## ?? New
                                textbutton "+ Scene" style "vn_btn_accent" yalign 0.5:
                                    action Function(_vn_add_scene, "New Scene")
                                if not _in_folder:
                                    textbutton "📁 + Folder" style "vn_btn_ghost" yalign 0.5:
                                        action Function(_vng_add_folder)

                                frame background Solid(VN_BDR) xsize 1 ysize 24 padding (0,0) yalign 0.5

                                ## ?? Edit (scene only)
                                textbutton "✏️ Edit" style "vn_btn_ghost" yalign 0.5:
                                    sensitive bool(_sel_sc)
                                    action ([SetField(vns, "scene_id", vng.selected_id), Function(vns.go, "dialogue")] if _sel_sc else NullAction())

                                ## ?? Rename
                                textbutton "✏️ Rename" style "vn_btn_ghost" yalign 0.5:
                                    sensitive bool(_sel_sc)
                                    selected bool(vng._rename_id and vng._rename_id == vng.selected_id)
                                    action (Function(_vng_start_rename) if _sel_sc else NullAction())

                                ## ?? Delete
                                textbutton "🗑️" style "vn_btn_ghost" yalign 0.5:
                                    sensitive bool(_sel_sc) or bool(getattr(vng, 'selected_ids', False)) or bool(_sel_fld)
                                    action (Function(_vng_delete_selected) if (bool(_sel_sc) or getattr(vng, 'selected_ids', False) or bool(_sel_fld)) else NullAction())

                                ## ?? Set Start
                                textbutton "🚩 Start" style "vn_btn_ghost" yalign 0.5:
                                    sensitive bool(_sel_sc)
                                    selected bool(_sel_sc) and vns.project.get('start') == vng.selected_id
                                    action ([SetDict(vns.project, 'start', vng.selected_id), Function(vns.save)] if _sel_sc else NullAction())

                                ## ?? Go To Scene
                                textbutton "➡️ Go" style "vn_btn_ghost" yalign 0.5:
                                    sensitive bool(_sel_sc)
                                    action ([SetField(vns, "scene_id", vng.selected_id), Function(vns.go, "scenes")] if _sel_sc else NullAction())

                                frame background Solid(VN_BDR) xsize 1 ysize 24 padding (0,0) yalign 0.5

                                ## ?? Auto-Layout
                                textbutton "✨ Auto-Layout" style "vn_btn_ghost" yalign 0.5:
                                    action Function(_vng_auto_layout)

                                null xfill True

                                ## ?? Search
                                hbox spacing 8 yalign 0.5:
                                    text "Ctrl+F" style "vn_t_faint" size 14 yalign 0.5
                                    if vns.ui.get('_focus') == "vn_graph_search_input":
                                        button style "vn_fr_input" padding (10, 6) ysize 32 xsize 160 yalign 0.5:
                                            action NullAction()
                                            input id "vn_graph_search_input" value FieldInputValue(vng, "search_query") style "vn_input" color VN_TEXT size 14
                                    else:
                                        $ _fv = vng.search_query or ''
                                        button style "vn_fr_input" padding (10, 6) ysize 32 xsize 160 yalign 0.5 hover_background Solid(VN_BG2):
                                            action [SetDict(vns.ui, '_focus', "vn_graph_search_input"), Function(renpy.set_focus, None, "vn_graph_search_input")]
                                            text (_fv if _fv else "Search…") style "vn_input" color (VN_FAINT if not _fv else VN_TEXT) size 14

                                if _in_folder:
                                    frame background Solid(VN_BDR) xsize 1 ysize 24 padding (0,0) yalign 0.5
                                    textbutton "⬅️ Leave Folder" style "vn_btn_accent" yalign 0.5 padding (12, 6):
                                        action Function(vng.exit_folder)

                    ## The canvas itself
                    frame background None xfill True yfill True padding (0,0):
                        viewport xfill True yfill True mousewheel False draggable False edgescroll None:
                            add VNGraphCanvas()

                        ## Canvas Floating Zoom Overlay
                        frame background Solid(VN_BG1) align (1.0, 1.0) offset (-12, -136) padding (8, 4):
                            hbox spacing 6 yalign 0.5:
                                textbutton "-" style "vn_btn_ghost" padding (6, 4) yalign 0.5:
                                    action SetField(vng, "zoom", max(0.25, vng.zoom - 0.12))
                                text f"{int(vng.zoom * 100)}%" style "vn_t_faint" yalign 0.5 xsize 50 text_align 0.5
                                textbutton "+" style "vn_btn_ghost" padding (6, 4) yalign 0.5:
                                    action SetField(vng, "zoom", min(3.0, vng.zoom + 0.12))

                    # ?? Graph Level Keyboard Shortcuts ????????????????????????
                    key "ctrl_K_z" action Function(vns.history.undo)
                    key "K_DELETE" action Function(_vng_delete_selected)
                    key "K_BACKSPACE" action Function(_vng_delete_selected)

            ## ?? Inspector Sidebar (Right) ??????????????????????????????????????
            hbox yfill True spacing 0:
                ## ?? Splitter handle ??????????????????????????????????????????
                frame background Solid(VN_BDR) xsize 6 yfill True padding (0, 0):
                    add _VNSplitter()

                ## ?? Right inspector panel ??????????????????????????????
                frame background Solid(VN_BG1) xsize vng.inspector_w yfill True padding (0, 0):
                    if vng.selected_folder:
                        use vn_folder_inspector(vng.selected_folder)
                    elif vng.selected_scene:
                        use vn_graph_inspector(vng.selected_scene)
                    else:
                        ## Empty state
                        frame background None padding (10, 10):
                            vbox spacing 16 yalign 0.5 xfill True:
                                if getattr(vng, 'current_folder', None) is not None:
                                    $ _cf = next((f for f in vns.project.get('folders', []) if f['id'] == vng.current_folder), None)
                                    text "📁" size 48 xalign 0.5
                                    text f"Inside {(_cf['label'] if _cf else 'Folder')}" style "vn_t_dim" xalign 0.5
                                    textbutton "⬅️ Leave to Main Graph" style "vn_btn_accent" xfill True padding (10, 12) text_align 0.5:
                                        action Function(vng.exit_folder)
                                    frame background Solid(VN_BDR) xfill True ysize 1
                                    text "Click a node inside to inspect it." style "vn_t_faint" xalign 0.5
                                else:
                                    text "⚠️" size 48 xalign 0.5
                                    text "Click a node" style "vn_t_dim" xalign 0.5
                                    text "to inspect its details" style "vn_t_faint" xalign 0.5
                                    frame background Solid(VN_BDR) xfill True ysize 1
                                    text "Drag nodes to arrange" style "vn_t_faint" xalign 0.5
                                    text "Pan canvas with empty drag" style "vn_t_faint" xalign 0.5


## ?? Inspector ????????????????????????????????????????????????????????????????

screen vn_graph_inspector(sc):

    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
        vbox spacing 0 xfill True:

            ## ?? Background Hero Image (top of inspector) ?????????????????
            $ _is_renaming = (vng._rename_id == sc['id'])
            $ _disp_bg = vn_get_scene_bg(sc, vns.project)
            if _disp_bg:
                frame background Solid(VN_BG0) xfill True padding (0, 0) ysize 124:
                    add Transform(_disp_bg, fit="cover", xysize=(1000, 120)) align (0.5, 0.0)
                    frame background Solid("#000000aa") xfill True ysize 24 padding (8, 4) yalign 1.0:
                        text _disp_bg.split('/')[-1] style "vn_t_faint" size 11 xalign 0.0

            ## Header strip — scene name is always clickable to rename inline
            frame background Solid(VN_BG2) xfill True padding (16, 14):
                vbox spacing 6:
                    if _is_renaming:
                        ## Inline rename: input then big Save button below
                        vbox xfill True spacing 8:
                            if vns.ui.get('_focus') == "vn_graph_rename_input":
                                button background Solid(VN_BG0) xfill True padding (10, 9):
                                    action NullAction()
                                    input id "vn_graph_rename_input" value FieldInputValue(vng, "_rename_buf") style "vn_t" color VN_TEXT size 20 copypaste True
                            else:
                                button background Solid(VN_BG0) hover_background Solid(VN_BG1) xfill True padding (10, 9):
                                    action [SetDict(vns.ui, '_focus', "vn_graph_rename_input"), Function(renpy.set_focus, None, "vn_graph_rename_input")]
                                    text (vng._rename_buf or '') style "vn_t_head" size 20 color VN_TEXT
                            hbox xfill True spacing 8:
                                textbutton "💾  Save Name" style "vn_btn_accent" xfill True:
                                    action Function(_vng_commit_rename)
                                textbutton "✕" style "vn_btn_ghost":
                                    action [SetField(vng, "_rename_id", None), SetField(vng, "_rename_buf", ""), SetDict(vns.ui, '_focus', '')]
                    else:
                        ## Single-click the name to rename
                        button background None padding (0, 0) hover_background Solid(VN_SEL):
                            action Function(_vng_start_rename)
                            hbox spacing 8 yalign 0.5:
                                text sc.get('label', '?') style "vn_t_head" size 20 yalign 0.5
                                text "✏️" style "vn_t_faint" size 14 yalign 0.5
                    $ ev_count = len(sc.get('events', []))
                    $ out_count = len([1 for ev in sc.get('events', []) if ev.get('type') in ('choice','jump')])
                    hbox spacing 10:
                        text f"{ev_count} event{'s' if ev_count != 1 else ''}" style "vn_t_dim"
                        text "|" style "vn_t_faint"
                        text f"{out_count} link{'s' if out_count != 1 else ''}" style "vn_t_faint"

            ## Action buttons
            frame background Solid(VN_BG1) xfill True padding (12, 10):
                vbox spacing 8 xfill True:
                    textbutton "▶️ Play Scene" style "vn_btn_teal" xfill True padding (8,8) text_align 0.5:
                        action Function(_vns_compile_scene, sc['id'])
                    
                    hbox spacing 8 xfill True:
                        textbutton "➡️ Enter Scene" style "vn_btn_accent" xfill True:
                            action [
                                SetField(vns, "scene_id", sc['id']),
                                Function(vns.go, "scene_editor"),
                            ]
                        textbutton "🎬 Scene" style "vn_btn_ghost" xfill True:
                            action [
                                SetField(vns, "scene_id", sc['id']),
                                Function(vns.go, "scenes"),
                            ]

                    ## Eject from Folder (if inside one)
                    $ _parent_folder = next((f for f in (vns.project.get('folders', []) if vns.project else []) if sc['id'] in f.get('scene_ids', [])), None)
                    if _parent_folder:
                        textbutton "↑ Eject from Folder" style "vn_btn_ghost" xfill True:
                            text_color "#5ccc70" text_hover_color "#7eee90"
                            action Function(_vng_eject_scene_from_folder, vns.project, _parent_folder['id'], sc['id'])

                    ## Set as start scene
                    $ is_start = vns.project.get('start') == sc['id']
                    if is_start:
                        frame background Solid(VN_TEAL + "22") xfill True padding (10, 6):
                            hbox spacing 8:
                                text "ℹ️" style "vn_t_teal" yalign 0.5
                                text "This is the START scene" style "vn_t_teal" size 13 yalign 0.5
                    else:
                        textbutton "🚩 Set as Start Scene" style "vn_btn_ghost" xfill True:
                            action [
                                Function(vns.history.commit, "Set Start Scene", 
                                    lambda: [vns.project.update({'start': sc['id']}), vns.save()],
                                    lambda: [vns.project.pop('start', None), vns.save()]),
                                Function(vns.notify, "Start scene set!", "ok"),
                            ]

            ## Background thumbnail (collapsed section)
            use vn_inspector_section("BACKGROUND", "bg_" + sc['id'], "_vn_graph_inspector_bg", sc)

            ## Events summary
            use vn_inspector_section("EVENTS", "ev_" + sc['id'], "_vn_graph_inspector_events", sc)

            ## Outbound connections
            use vn_inspector_section("CONNECTIONS OUT", "out_" + sc['id'], "_vn_graph_inspector_out", sc)

            ## Inbound connections (scenes that link TO this one)
            use vn_inspector_section("CONNECTIONS IN", "in_" + sc['id'], "_vn_graph_inspector_in", sc)

            ## Danger zone
            use vn_inspector_section("DANGER", "danger_" + sc['id'], "_vn_graph_inspector_danger", sc)

            ## History Dock (Undo Stack)
            use vn_inspector_section("HISTORY (Undo Stack)", "history", "_vn_graph_inspector_history", sc)


## ?? Inspector Sections (Godot EditorInspectorSection inspired) ???????????????

screen vn_inspector_section(title, key, content_screen, arg1=None, arg2=None):
    $ folded = vng.fold_state.get(key, False)
    vbox xfill True spacing 0:
        button xfill True padding (0,0):
            action SetDict(vng.fold_state, key, not folded)
            background Solid(VN_BG3)
            hover_background Solid(VN_SEL)
            frame background None xfill True padding (12, 8):
                hbox xfill True spacing 8:
                    text ("▶️" if folded else "⬇️") style "vn_t_faint" size 11 yalign 0.5
                    text title style "vn_t_label" yalign 0.5
        if not folded:
            if arg2 is not None:
                use expression content_screen pass (arg1, arg2)
            else:
                use expression content_screen pass (arg1,)


screen _vn_graph_inspector_bg(sc):
    $ _disp_bg = vn_get_scene_bg(sc, vns.project)
    frame background Solid(VN_BG2) xfill True padding (12, 10):
        vbox spacing 8:
            if _disp_bg:
                add _disp_bg xsize 276 ysize 110 fit "cover" xalign 0.5
            else:
                frame background Solid(VN_BG3) xfill True ysize 60 padding (0,0):
                    text "No background" style "vn_t_faint" xalign 0.5 yalign 0.5

screen _vn_graph_inspector_events(sc):
    frame background Solid(VN_BG2) xfill True padding (12, 10):
        vbox spacing 6 xfill True:
            if not sc.get('events'):
                text "No events yet." style "vn_t_faint"
            else:
                for ev in sc['events'][:8]:
                    use vn_event_mini(ev)
                if len(sc['events']) > 8:
                    text f". {len(sc['events'])-8} more" style "vn_t_faint"

screen _vn_graph_inspector_out(sc):
    frame background Solid(VN_BG2) xfill True padding (12, 10):
        vbox spacing 6 xfill True:
            python:
                _edges = []
                for ev in sc.get('events', []):
                    if ev.get('type') == 'choice':
                        for opt in ev.get('opts', []):
                            if opt.get('scene'):
                                ts = vn_find_scene(vns.project, opt['scene'])
                                if ts:
                                    _edges.append((
                                        opt.get('text','?')[:22],
                                        ts.get('label','?'),
                                        VN_TEAL,
                                    ))
                    elif ev.get('type') == 'jump' and ev.get('scene_id'):
                        ts = vn_find_scene(vns.project, ev['scene_id'])
                        if ts:
                            _edges.append((
                                'jump',
                                ts.get('label','?'),
                                VN_ACC,
                            ))
            if not _edges:
                text "No outgoing links." style "vn_t_faint"
            else:
                for (elbl, etgt, ecol) in _edges:
                    frame background Solid(VN_BG3) xfill True padding (8, 6):
                        hbox spacing 8:
                            text "➕" style "vn_t_faint" yalign 0.5
                            vbox xfill True yalign 0.5:
                                text elbl style "vn_t_faint" size 12
                                text etgt style "vn_t" size 14 color ecol


screen _vn_graph_inspector_in(sc):
    frame background Solid(VN_BG2) xfill True padding (12, 10):
        vbox spacing 6 xfill True:
            python:
                _in_edges = []
                for other in vns.project.get('scenes', []):
                    if other['id'] == sc['id']:
                        continue
                    for ev in other.get('events', []):
                        if ev['type'] == 'choice':
                            for opt in ev.get('opts', []):
                                if opt.get('scene') == sc['id']:
                                    _in_edges.append(other.get('label','?'))
                                    break
                        elif ev['type'] == 'jump' and ev.get('scene_id') == sc['id']:
                            _in_edges.append(other.get('label','?'))
            if not _in_edges:
                text "No incoming links." style "vn_t_faint"
            else:
                for src_lbl in _in_edges:
                    frame background Solid(VN_BG3) xfill True padding (8, 6):
                        hbox spacing 8:
                            text "➕" style "vn_t_faint" yalign 0.5
                            text src_lbl style "vn_t" size 14

screen _vn_graph_inspector_danger(sc):
    frame background Solid(VN_BG2) xfill True padding (12, 10):
        vbox spacing 6 xfill True:
            textbutton "🗑️ Delete this Scene" style "vn_btn_danger" xfill True:
                action Function(_vng_delete_selected)


## ?? History Dock (Godot HistoryDock inspired) ????????????????????????????????

screen _vn_graph_inspector_history(sc):
    frame background Solid(VN_BG2) xfill True padding (12, 10):
        vbox spacing 6 xfill True:
            if not vns.history.can_undo() and not vns.history.can_redo():
                text "No history recorded yet." style "vn_t_faint" size 13
            else:
                ## Show redo stack (faded out, above current)
                for item in reversed(vns.history._redo_stack):
                    hbox spacing 8:
                        text "⚙️" style "vn_t_faint" size 12 yalign 0.5
                        text item[0] style "vn_t_faint" size 13 yalign 0.5

                ## Current tip of the undo stack
                if vns.history._undo_stack:
                    hbox spacing 8:
                        text "➕" style "vn_t_teal" size 12 yalign 0.5
                        text vns.history._undo_stack[-1][0] style "vn_t" size 13 font VN_FONTB color VN_TEXT yalign 0.5

                ## Older items in the undo stack
                for item in reversed(vns.history._undo_stack[:-1]):
                    hbox spacing 8:
                        text "🗑️" style "vn_t_dim" size 12 yalign 0.5
                        text item[0] style "vn_t_dim" size 13 yalign 0.5

                frame background None padding (0, 8) xfill True:
                    hbox spacing 8 xalign 0.5:
                        textbutton "↩️ Undo" style "vn_btn_ghost":
                            sensitive vns.history.can_undo()
                            action Function(vns.history.undo)
                        textbutton "↪️ Redo" style "vn_btn_ghost":
                            sensitive vns.history.can_redo()
                            action Function(vns.history.redo)


## ── Folder inspector helper ────────────────────────────────────────────────
init python:
    def _vng_eject_scene_from_folder(project, folder_id, scene_id):
        """Remove scene_id from folder's scene_ids list, placing it back on the main graph."""
        for fld in project.get('folders', []):
            if fld['id'] == folder_id:
                try:
                    fld.setdefault('scene_ids', []).remove(scene_id)
                    if folder_id in store.vng.layout:
                        fx, fy = store.vng.layout[folder_id]
                        store.vng.layout[scene_id] = (fx, fy - 160)
                except ValueError:
                    pass
                break
        vn_save(project)
        renpy.restart_interaction()

    def _vng_dragged_scene(project, folder_id, scene_id, drags, drop):
        """Called when a scene card drag is released.
        Ejects the scene if dropped over the graph area (left of inspector panel)."""
        mx, _my = renpy.get_mouse_pos()
        graph_right = renpy.config.screen_width - store.vng.inspector_w - 6
        if mx < graph_right:
            _vng_eject_scene_from_folder(project, folder_id, scene_id)
        else:
            renpy.restart_interaction()


## ── Folder inspector screen ────────────────────────────────────────────────
screen vn_folder_inspector(fld):
    $ fid     = fld['id']
    $ sc_ids  = fld.get('scene_ids', [])
    $ scenes  = [s for s in vns.project.get('scenes', []) if s['id'] in sc_ids] if vns.project else []

    viewport xfill True yfill True scrollbars "vertical" mousewheel True style_prefix "vn_vscroll":
        vbox spacing 0 xfill True:

            ## ── Header ──────────────────────────────────────────────────
            frame background Solid("#1a1505") xfill True padding (16, 16):
                vbox spacing 8 xfill True:
                    hbox spacing 10 yalign 0.5:
                        text "📁" size 28 yalign 0.5
                        vbox yalign 0.5 spacing 2:
                            text fld.get('label', 'Folder') style "vn_t_sub" size 16
                            text f"{len(sc_ids)} scene{'s' if len(sc_ids) != 1 else ''}" style "vn_t_faint" size 11

            ## ── Actions ─────────────────────────────────────────────────
            frame background Solid(VN_BG1) xfill True padding (12, 10):
                textbutton "➡️ Enter Folder" style "vn_btn_accent" xfill True padding (8, 8) text_align 0.5:
                    action [
                        SetField(vng, "current_folder", fid),
                        SetField(vng, "selected_id", None)
                    ]

            ## ── Rename ──────────────────────────────────────────────────
            frame background Solid(VN_BG2) xfill True padding (16, 12):
                vbox spacing 6 xfill True:
                    hbox spacing 6 yalign 0.5:
                        frame background Solid(VN_ACC) xsize 3 ysize 14 padding (0,0) yalign 0.5
                        text "RENAME" style "vn_t_label" yalign 0.5
                    frame background Solid(VN_BG3) xfill True padding (8, 6):
                        input id "vn_folder_rename" value DictInputValue(fld, 'label') length 60 size 15 color VN_TEXT style "vn_input"
                    textbutton "✓  Save Name" style "vn_btn_teal" xfill True:
                        action Function(vns.save)
                        text_size 12

            ## ── Scenes inside ───────────────────────────────────────────
            frame background Solid(VN_BG1) xfill True padding (0, 0):
                vbox spacing 0 xfill True:
                    frame background Solid(VN_BG2) xfill True padding (16, 10):
                        hbox spacing 6 xfill True yalign 0.5:
                            frame background Solid(VN_TEAL) xsize 3 ysize 14 padding (0,0) yalign 0.5
                            text "SCENES IN FOLDER" style "vn_t_label" yalign 0.5
                            null xfill True
                            text "← drag to graph" style "vn_t_faint" size 10 color VN_FAINT yalign 0.5

                    if not scenes:
                        frame background None xfill True padding (16, 16):
                            text "No scenes inside yet.\nDrag a scene onto this folder to add it." style "vn_t_faint" size 12
                    else:
                        for _sc in scenes:
                            frame background Solid(VN_BG2) xfill True padding (0, 0):
                                vbox spacing 0 xfill True:
                                    hbox spacing 0 xfill True yalign 0.5:
                                        ## Scene info (clickable to select)
                                        button background None xfill True padding (12, 12):
                                            hover_background Solid(VN_SEL)
                                            action SetField(vng, 'selected_id', _sc['id'])
                                            vbox spacing 3:
                                                text _sc.get('label', '?') style "vn_t" size 14 color VN_TEXT
                                                $ _ev_c = len(_sc.get('events', []))
                                                text f"{_ev_c} event{'s' if _ev_c != 1 else ''}" style "vn_t_faint" size 11
                                        
                                        ## Eject button
                                        button padding (12, 0) yfill True:
                                            background Solid("#1a2a1a")
                                            hover_background Solid("#2a441a")
                                            action Function(_vng_eject_scene_from_folder, vns.project, fid, _sc['id'])
                                            vbox xalign 0.5 yalign 0.5 spacing 2:
                                                text "↑" size 16 color "#5ccc70" xalign 0.5
                                                text "Eject" style "vn_t_dim" size 9 color "#5ccc70" xalign 0.5
                                    ## Divider
                                    frame background Solid(VN_BDR) xfill True ysize 1 padding (0,0)

            ## ── Danger zone ─────────────────────────────────────────────
            frame background Solid("#1a0505") xfill True padding (16, 12):
                vbox spacing 8 xfill True:
                    hbox spacing 6 yalign 0.5:
                        frame background Solid(VN_ERR) xsize 3 ysize 14 padding (0,0) yalign 0.5
                        text "DANGER" style "vn_t_label" color VN_ERR yalign 0.5
                    textbutton "🗑  Delete Folder" style "vn_btn_ghost" xfill True:
                        text_color VN_ERR text_hover_color "#ff8888"
                        action Function(_vng_delete_selected)
                        text_size 12
