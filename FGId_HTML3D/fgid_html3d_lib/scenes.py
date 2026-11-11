"""Presentation data for the HTML viewer. The source document is read-only."""
import math
from PySide6.QtGui import QVector3D
from core.camera import OrbitCamera
from .adapter import yup


def camera_record(camera):
    return dict(eye=yup(camera.eye()), target=yup(camera.target),
                up=yup(camera.up_vector()), fov=camera.fov_deg,
                parallel=not camera.perspective,
                halfHeight=camera.distance * math.tan(math.radians(camera.fov_deg) / 2))


def scene_records(scene, indices):
    planes = {plane.uid: plane for plane in scene.section_planes}

    def cut(uid):
        plane = planes.get(uid)
        if plane is None:
            return []
        return [dict(normal=yup(plane.normal), point=yup(plane.point))]

    model_planes = {}
    initial = None
    def collect(groups):
        nonlocal initial
        for group in groups:
            model = (getattr(group, 'ext', None) or {}).get('fgid_skp_model')
            if model:
                initial = model.get('initial') or initial
                for plane in model.get('planes', []):
                    if plane['context'] != 'ROOT':
                        model_planes[plane['id']] = plane
            collect(group.children or ())
    collect(scene.groups)

    def scoped_cuts(state):
        result = []
        for identifier in state.get('active_planes', []):
            plane = model_planes.get(identifier)
            if not plane:
                continue
            a, b, c, d = plane['equation']
            norm = math.sqrt(a*a + b*b + c*c)
            if norm < 1e-9:
                continue
            result.append(dict(context=plane['context'],
                               normal=[-a/norm, -c/norm, b/norm],
                               point=[-d*a*.0254/norm**2, -d*c*.0254/norm**2, d*b*.0254/norm**2]))
        return result

    active = scene.active_section()
    records = [dict(name='Current view', cuts=cut(active.uid) if
                    active and scene.show_section_cuts else [])]
    if initial and scene.show_section_cuts:
        records[0]['cuts'].extend(scoped_cuts(initial))
    rules = [{}]
    for index in indices:
        view = scene.saved_views[index]
        section = view.section or {}
        imported = section.get('fgid_skp_state')
        use = imported.get('use', {}) if imported is not None else {}
        record = dict(name=view.name)
        if imported is None or (use.get('camera') and imported.get('camera')):
            camera = OrbitCamera()
            camera.target = QVector3D(*view.target)
            for key in ('distance', 'pitch', 'yaw', 'fov_deg', 'perspective'):
                setattr(camera, key, getattr(view, key))
            record['camera'] = camera_record(camera)
        if imported is None or use.get('tags'):
            record['hiddenLayers'] = view.hidden_layers if imported is None else imported.get('hidden_layers', [])
        if imported is None and section:
            record['cuts'] = cut(section.get('active')) if section.get('cuts_shown', True) else []
        if imported is not None and use.get('cuts'):
            rendering = imported.get('rendering', {})
            record['cuts'] = cut(imported.get('active_root_uid'))  + scoped_cuts(imported) if rendering.get('DisplaySectionCuts', True) else []
        if imported is not None and use.get('style'):
            rendering = imported.get('rendering', {})
            color = rendering.get('BackgroundColor')
            if isinstance(color, (list, tuple)) and len(color) >= 3:
                record['background'] = color[:3]
            if 'EdgeDisplayMode' in rendering:
                record['edges'] = rendering['EdgeDisplayMode'] != 0
        elif imported is None and view.style:
            record['background'] = view.style.get('background')
            record['edges'] = view.style.get('edges')
        records.append(record)
        rules.append(dict(
            native=set(view.hidden_objects) if imported is None and view.hidden_objects is not None else None,
            imported_objects=bool(use.get('hidden_objects')),
            imported_geometry=bool(use.get('hidden_geometry')),
            ids=set(imported.get('hidden_ids', [])) if imported is not None else set(),
        ))
    return records, rules


def hidden_in(rules, default, uid=None, entity_id=None, geometry=False):
    result = []
    for index, rule in enumerate(rules):
        hidden = default
        if geometry:
            if entity_id is not None and rule.get('imported_geometry'):
                hidden = entity_id in rule['ids']
        elif rule.get('native') is not None:
            hidden = uid in rule['native']
        elif entity_id is not None and rule.get('imported_objects'):
            hidden = entity_id in rule['ids']
        if hidden:
            result.append(index)
    return tuple(result)
