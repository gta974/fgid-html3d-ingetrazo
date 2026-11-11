# SPDX-License-Identifier: GPL-3.0-or-later
import base64,gzip,html,json,tempfile
from pathlib import Path
from . import adapter, scenes
from .glb_writer import save_glb
from .render_modes import initial_mode
ROOT=Path(__file__).parent

def visible_cloud(scene, viewport):
    cloud = getattr(viewport, '_fgid_pointcloud', None)
    if (cloud is not None and cloud.scene is scene and cloud.data is not None
            and len(cloud.data) and getattr(cloud, 'visible', True)
            and getattr(cloud, 'opacity', 1) > 0 and not getattr(cloud, 'error', None)):
        return cloud
    return None


def loaded_cloud(scene, viewport):
    cloud = getattr(viewport, '_fgid_pointcloud', None)
    if (cloud is not None and cloud.scene is scene and cloud.data is not None
            and len(cloud.data) and not getattr(cloud, 'error', None)):
        return cloud
    return None


def cloud_record(cloud, state=None):
    """Use loaded cloud coordinates. Saved scenes without cloud data inherit current state."""
    import numpy as np
    from PySide6.QtGui import QMatrix4x4
    state = state or {}
    translation = state.get('translation', cloud.translation)
    rotation = state.get('rotation', cloud.rotation)
    matrix = QMatrix4x4()
    matrix.translate(*translation)
    for angle, axis in zip(rotation, [(1,0,0), (0,1,0), (0,0,1)]):
        matrix.rotate(angle, *axis)
    return dict(
        visible=bool(state.get('visible', cloud.visible)),
        clipLo=list(map(float, state.get('clip_lo', cloud.clip_lo))),
        clipHi=list(map(float, state.get('clip_hi', cloud.clip_hi))),
        size=float(state.get('point_size', cloud.point_size)),
        opacity=float(state.get('opacity', cloud.opacity)),
        matrix=np.asarray(matrix.data()).reshape(4,4).T.reshape(-1).tolist(),
        hiddenScans=list(state.get('hidden_scans', cloud.hidden_scans)),
    )


def saved_cloud_record(cloud, view, viewport):
    state = getattr(view, 'fgid_cloud_state', None)
    if not state:
        return cloud_record(cloud)
    source = Path(state.get('path', ''))
    if state.get('relative'):
        api = getattr(viewport, '_fgid_api', None)
        project = getattr(getattr(api, 'window', None), '_current_path', None)
        if project:
            source = Path(project).parent / source
        else:
            source = Path(cloud.meta['path']) if source.name == Path(cloud.meta['path']).name else source
    if source.resolve() != Path(cloud.meta['path']).resolve():
        result = cloud_record(cloud)
        result['visible'] = False
        return result
    result = cloud_record(cloud, state)
    # Rebase saved local clipping and transformations when placement differs.
    import numpy as np
    lo = np.asarray(cloud.meta.get('bounds_min', [0,0,0]), dtype=float)
    hi = np.asarray(cloud.meta.get('bounds_max', [0,0,0]), dtype=float)
    placement = state.get('placement', cloud.meta.get('placement', 'none'))
    origin = np.zeros(3) if placement == 'none' else (lo + hi) / 2
    if placement == 'ground':
        origin[2] = lo[2]
    delta = np.asarray(cloud.meta.get('origin', [0,0,0])) - origin
    result['clipLo'] = (np.asarray(result['clipLo']) - delta).tolist()
    result['clipHi'] = (np.asarray(result['clipHi']) - delta).tolist()
    matrix = np.asarray(result['matrix']).reshape(4,4)
    matrix[:3,3] += matrix[:3,:3] @ delta
    result['matrix'] = matrix.reshape(-1).tolist()
    return result


def export_html(scene,path,options=None,viewport=None):
    if getattr(scene,'edit_group',None) is not None:raise ValueError('Quittez l’édition du groupe avant d’exporter le modèle complet.')
    options=options or {};path=Path(path)
    render_mode = initial_mode(scene, options.get('render_mode'))
    indices = options.get("scenes", [])
    current_view = options.get('current_view', bool(indices))
    records, rules = scenes.scene_records(scene, indices) if indices or current_view else ([], [])
    live_camera = getattr(viewport, 'camera', None)
    if records and current_view and live_camera is not None:
        records[0]['camera'] = scenes.camera_record(live_camera)

    with tempfile.TemporaryDirectory(prefix='fgid_html3d_') as tmp:
        glb=Path(tmp)/'model.glb';save_glb(scene,glb,scene_rules=rules);data=glb.read_bytes()
    b64=lambda b:base64.b64encode(b).decode('ascii')
    js=lambda x:json.dumps(x,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e')
    edges=adapter.loose_edges(scene, rules) if options.get('loose','No')!='No' else []
    anns=adapter.annotations(scene) if options.get('annotations',True) else []
    vals=dict(title=html.escape(path.stem),glb_base64=b64(gzip.compress(data, compresslevel=6, mtime=0)),glb_bytes_json=str(len(data)),camera_json='{}',dark_default_json=js(options.get('theme','Light')=='Dark'),edges_default_json=js(options.get('edges',True)),loose_edges_json='[]',annotations_json=js(anns),ply_base64='',ply_name_json='""',ply_present_json='false',ply_transform_mode_json='"none"',ply_transform_matrix_json='[]',ply_manual_transform_json='{}',ply_point_size_json='0.015',three_module_base64=b64((ROOT/'vendor/three.module.min.js').read_bytes()),orbit_controls_base64=b64((ROOT/'vendor/OrbitControls.js').read_bytes()))
    c=loaded_cloud(scene, viewport) if options.get('cloud') else None
    if c is not None:
        import numpy as np
        points = c.data
        xyz = points[:, :3]
        packed=np.empty(len(points),dtype=[('x','<f4'),('y','<f4'),('z','<f4'),('red','u1'),('green','u1'),('blue','u1')])
        for j,k in enumerate(('x','y','z')):packed[k]=xyz[:,j]
        for j,k in enumerate(('red','green','blue')):packed[k]=np.clip(points[:,3+j]*255,0,255).astype('u1')
        header=('ply\nformat binary_little_endian 1.0\nelement vertex '+str(len(points))+'\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n').encode()
        vals.update(ply_base64=b64(header+packed.tobytes()),ply_present_json='true',ply_name_json=js(Path(c.meta['path']).name))
    vals['escape_js(title)']=path.stem.replace('\\','\\\\').replace("'","\\'").replace('<','').replace('\n',' ')
    template=(ROOT/'viewer.html').read_text(encoding='utf-8')
    for key,value in vals.items():template=template.replace('@@'+key+'@@',value)
    menu_order = list(range(1, len(records)))
    if current_view:
        menu_order.insert(options.get('current_view_position', 0), 0)
    cloud_metadata = None
    if c is not None:
        cloud_metadata = dict(current=cloud_record(c), scans=[
            dict(id=scan['id'], start=int(scan['start']), count=int(scan['count']))
            for scan in c.meta.get('scans', [])
        ])
        if records:
            records[0]['cloud'] = cloud_record(c)
            for record, index in zip(records[1:], indices):
                record['cloud'] = saved_cloud_record(c, scene.saved_views[index], viewport)
    metadata=dict(initialRenderMode=render_mode,cloud=cloud_metadata,layers=adapter.layers(scene),loose=edges,scenes=records,sceneMenuOrder=menu_order,looseMode=options.get('loose','No'))
    template=template.replace('const ANNOTATIONS =', 'const FGID_META = '+js(metadata)+';\n        const ANNOTATIONS =',1)
    if '@@' in template:raise ValueError('Unresolved viewer placeholder')
    license_text=(ROOT/'vendor/THREE_LICENSE.txt').read_text(encoding='utf-8')
    template=template.replace('<head>','<!-- HTML3D viewer adapted from the user-provided Tarnus HTML3D Exporter. GLB writer: IngeTrazo contributors, GPL-3.0-or-later. Three.js / OrbitControls license:\n'+license_text.replace('--','—')+'\n-->\n<head>',1)
    path.write_text(template,encoding='utf-8')
    return dict(html=str(path),bytes=path.stat().st_size,glb_bytes=len(data),annotations=len(anns),loose_edges=len(edges))
