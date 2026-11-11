"""Display-mode choices shared by the export dialog and exporter."""
MODES = (
    ("textures", "Textures"),
    ("colors", "Couleurs seules"),
    ("monochrome", "Monochrome"),
    ("hiddenline", "Lignes cachées"),
    ("wireframe", "Filaire"),
    ("xray", "Rayons X"),
    ("clay", "Argile"),
    ("normals", "Normales"),
)
NATIVE_MODES = {
    "textures": "textures",
    "shaded": "colors",
    "hidden_line": "hiddenline",
    "monochrome": "monochrome",
    "wireframe": "wireframe",
    "xray": "xray",
}


def initial_mode(scene, requested=None):
    if requested is None:
        style = getattr(scene, "display_style", None)
        return NATIVE_MODES.get(getattr(style, "face_mode", "textures"), "textures")
    if requested not in dict(MODES):
        raise ValueError("Mode de rendu inconnu : " + str(requested))
    return requested
