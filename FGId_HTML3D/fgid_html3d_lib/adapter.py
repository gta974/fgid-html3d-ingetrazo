# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only scene adapter; hierarchy and material paint follow IngeTrazo's exporter."""
from core.layers import layer_of, DEFAULT_LAYER
from formats.meshexport import SmoothNormals, _add_face, _shown, _piece_paint, _resolve_finishes

from math import cos, radians
from PySide6.QtGui import QVector3D


class AngleSmoothNormals(SmoothNormals):
    """Smooth connected face fans below 30 degrees without editing edges."""

    def __init__(self):
        super().__init__()
        self._joins = {}

    def _fan(self, vertex):
        if vertex in self._at:
            return self._at[vertex]
        neighbors = {}
        for edge in vertex.edges:
            if len(edge.faces) != 2:
                continue
            first, second = edge.faces
            if edge not in self._joins:
                dot = QVector3D.dotProduct(self.flat(first), self.flat(second))
                self._joins[edge] = dot > cos(radians(30)) + 1e-7
            if self._joins[edge]:
                neighbors.setdefault(first, []).append(second)
                neighbors.setdefault(second, []).append(first)
        normals = {}
        visited = set()
        for face in neighbors:
            if face in visited:
                continue
            stack = [face]
            visited.add(face)
            fan = []
            average = QVector3D()
            while stack:
                member = stack.pop()
                fan.append(member)
                average += self.flat(member)
                for neighbor in neighbors[member]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            if average.lengthSquared() > 1e-12:
                average.normalize()
                normals.update((member, average) for member in fan)
        self._at[vertex] = normals
        return normals


def tagpath(entity, inherited):
    tag=layer_of(entity)
    return inherited if tag==DEFAULT_LAYER else tuple(dict.fromkeys((*inherited,tag)))

def hierarchy(scene, only=None, scene_rules=()):
    from .scenes import hidden_in
    materials={};meshes={};roots=[];smooth=AngleSmoothNormals()
    def pieces(mesh, path, paint, root_geometry=False):
        bins={}
        for face in mesh.faces:
            hidden = bool(face.attrs.get('hidden'))
            entity_id = face.attrs.get('fgid_skp_face_id') if root_geometry else None
            mask = hidden_in(scene_rules, hidden, entity_id=entity_id, geometry=True)
            if len(mask) == len(scene_rules) and (scene_rules or hidden):
                continue
            tags=tagpath(face,path) or (DEFAULT_LAYER,)
            bins.setdefault((tags, mask),[]).append(face)
        nodes=[]
        for (tags, mask),faces in bins.items():
            from core.materials import material_sig
            key=(id(mesh),material_sig(paint),tags,mask)
            if key not in meshes:
                prims={}
                for f in faces:_add_face(f,materials,prims,_shown(f,paint),smooth)
                meshes[key]=prims
            nodes.append(dict(name=tags[-1],matrix=None,mesh=key,children=[],extras={'fgid_tags':list(tags), 'fgid_hidden_in':mask}))
        return nodes
    roots.extend(pieces(scene.loose_mesh,(),None))
    def part(g, inherited, top, inherited_paint=None):
        ext = (getattr(g, 'ext', None) or {}).get('fgid_skp', {})
        hidden = getattr(g, 'hidden', False)
        mask = hidden_in(scene_rules, hidden, g.uid if scene_rules else None, ext.get('entity_id'))
        if len(mask) == len(scene_rules) and (scene_rules or hidden):
            return None
        tags=tagpath(g,inherited)
        if (getattr(top, 'ext', None) or {}).get('fgid_skp'):
            paint = getattr(g, 'material', None) or inherited_paint
        else:
            paint = _piece_paint(g, top)
        node=dict(name=g.name or 'Group',matrix=g.xform,mesh=None,children=pieces(g.mesh,tags,paint,ext.get('definition')=='ROOT'),extras={'fgid_container':True,'fgid_hidden_in':mask, 'fgid_scope':g.uid if scene_rules else None, 'fgid_context':ext.get('definition') if scene_rules else None})
        for child in g.children or ():
            sub=part(child,tags,top,paint)
            if sub:node['children'].append(sub)
        return node
    for g in scene.groups:
        if only is not None and g not in only:continue
        n=part(g,(),g)
        if n:roots.append(n)
    _resolve_finishes(scene,materials)
    return materials,meshes,roots

def yup(p):return [p.x(),p.z(),-p.y()]

def annotations(scene):
    result=[]
    for a in scene.text_labels:
        result.append(dict(type='text',tag=layer_of(a),text=a.text,anchor=yup(a.anchor),text_position=yup(a.position()),leader=True))
    for d in scene.dimensions:
        a,b=d.a,d.b;o=d.offset
        measurement=f'{(b-a).length():.3f} m'
        text=(getattr(d,'text',None) or measurement).replace('<>',measurement)
        result.append(dict(type='dimension_linear',tag=layer_of(d),text=text,start=yup(a),end=yup(b),dim_start=yup(a+o),dim_end=yup(b+o),anchor=yup(a),text_position=yup((a+b)*.5+o)))
    return result

def layers(scene):
    return {l.name:dict(visible=l.visible,color=getattr(l,'color',None)) for l in scene.layers}

def loose_edges(scene, scene_rules=()):
    from .scenes import hidden_in
    result=[]
    def visit(mesh,m,path, group_mask=(), edge_ids=None, scope=None):
        for index, e in enumerate(mesh.edges):
            if e.faces:
                continue
            hidden = getattr(e, 'hidden', False)
            mask = set(group_mask).union(hidden_in(scene_rules, hidden, entity_id=(edge_ids or {}).get(index), geometry=True))
            if len(mask) == len(scene_rules) and (scene_rules or hidden):
                continue
            tags=tagpath(e,path) or (DEFAULT_LAYER,)
            pts=[e.v0.position,e.v1.position]
            result.append(dict(tags=list(tags), hiddenIn=sorted(mask), scope=scope, positions=[v for p in pts for v in yup(m.map(p) if m else p)]))
    visit(scene.loose_mesh,None,())
    def group(g,base,path,parent_mask=()):
        ext = getattr(g, 'ext', None) or {}
        hidden = getattr(g, 'hidden', False)
        mask = set(parent_mask).union(hidden_in(scene_rules, hidden, g.uid if scene_rules else None, ext.get('fgid_skp', {}).get('entity_id')))
        if len(mask) == len(scene_rules) and (scene_rules or hidden):
            return
        m=g.xform if base is None else (base*g.xform if g.xform is not None else base)
        tags=tagpath(g,path);visit(g.mesh,m,tags,mask,dict(ext.get("fgid_skp_root_edges", [])), g.uid if scene_rules else None)
        for c in g.children or ():group(c,m,tags,mask)
    for g in scene.groups:group(g,None,())
    return result
