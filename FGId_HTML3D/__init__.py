# SPDX-License-Identifier: GPL-3.0-or-later
"""FGId HTML3D Exporter for IngeTrazo, release 0.17.2."""
import traceback
from PySide6.QtWidgets import QDialog,QFormLayout,QComboBox,QCheckBox,QDialogButtonBox,QFileDialog,QMessageBox,QLabel,QListWidget,QListWidgetItem,QPushButton,QWidget,QVBoxLayout,QHBoxLayout
from PySide6.QtGui import QAction,QDesktopServices
from PySide6.QtCore import QUrl,Qt
from .fgid_html3d_lib.exporter import export_html, loaded_cloud
from .fgid_html3d_lib.render_modes import MODES, initial_mode

def show_export(app):
    dlg=QDialog(app.window);dlg.setWindowTitle('Export HTML3D');form=QFormLayout(dlg)
    theme=QComboBox();theme.addItems(['Light','Dark']);form.addRow('Thème',theme)
    render = QComboBox()
    render.setObjectName('initialRenderMode')
    for key, title in MODES:
        render.addItem(title, key)
    render.setCurrentIndex(render.findData(initial_mode(app.scene)))
    render.setToolTip("Mode affiché à l’ouverture du HTML, modifiable ensuite dans la barre d’outils.")
    form.addRow('Mode de rendu initial', render)
    edges=QCheckBox();edges.setChecked(True);edges.setObjectName('displayEdgesAtOpening');form.addRow('Display edges at opening',edges)
    loose=QComboBox();loose.addItems(['Non','Oui, couleur unique','Oui, couleurs des Tags disponibles']);form.addRow('Arêtes libres',loose)
    note=QLabel('Les couleurs de Tags absentes du modèle utilisent la couleur du thème.');note.setWordWrap(True);form.addRow(note)
    anns=QCheckBox();anns.setChecked(True);form.addRow('Annotations',anns)
    cloud = QCheckBox()
    if loaded_cloud(app.scene, app.viewport) is not None:
        form.addRow('Inclure le nuage FGId chargé (états des scènes)', cloud)
    views = list(getattr(app.scene, 'saved_views', []))
    include_scenes = QCheckBox('Exporter les scènes')
    form.addRow(include_scenes)
    scene_panel = QWidget()
    layout = QVBoxLayout(scene_panel)
    scene_list = QListWidget()
    scene_list.setMaximumHeight(180)
    current = QListWidgetItem('Current view', scene_list)
    current.setData(Qt.UserRole, -1)
    current.setCheckState(Qt.Checked)
    for index, view in enumerate(views):
        item = QListWidgetItem(view.name, scene_list)
        item.setData(Qt.UserRole, index)
        item.setCheckState(Qt.Unchecked)
    layout.addWidget(scene_list)
    shortcuts = QHBoxLayout()
    for title, state in [('Tout sélectionner', Qt.Checked), ('Tout désélectionner', Qt.Unchecked)]:
        button = QPushButton(title)
        def select_all(checked=False, check_state=state):
            for row in range(scene_list.count()):
                scene_list.item(row).setCheckState(check_state)
        button.clicked.connect(select_all)
        shortcuts.addWidget(button)
    layout.addLayout(shortcuts)
    order_controls = QHBoxLayout()
    up = QPushButton('↑ Monter')
    down = QPushButton('↓ Descendre')
    order_controls.addWidget(up)
    order_controls.addWidget(down)
    layout.addLayout(order_controls)

    def update_order_buttons(row):
        up.setEnabled(row > 0)
        down.setEnabled(0 <= row < scene_list.count() - 1)

    def move_scene(step):
        row = scene_list.currentRow()
        destination = row + step
        if row >= 0 and 0 <= destination < scene_list.count():
            item = scene_list.takeItem(row)
            scene_list.insertItem(destination, item)
            scene_list.setCurrentRow(destination)

    up.clicked.connect(lambda: move_scene(-1))
    down.clicked.connect(lambda: move_scene(1))
    scene_list.currentRowChanged.connect(update_order_buttons)
    scene_list.setCurrentRow(0)
    update_order_buttons(0)
    form.addRow(scene_panel)
    scene_panel.hide()
    include_scenes.toggled.connect(scene_panel.setVisible)
    opening=QCheckBox();opening.setChecked(True);form.addRow('Ouvrir dans le navigateur',opening)
    buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dlg.accept);buttons.rejected.connect(dlg.reject);form.addRow(buttons)
    if dlg.exec()!=QDialog.Accepted:return
    filename,_=QFileDialog.getSaveFileName(app.window,'Export HTML3D','modele_HTML3D.html','HTML (*.html)')
    if not filename:return
    try:
        selected = []
        if include_scenes.isChecked():
            for row in range(scene_list.count()):
                item = scene_list.item(row)
                if item.checkState() == Qt.Checked:
                    selected.append(item.data(Qt.UserRole))
        options = dict(
            theme=theme.currentText(), edges=edges.isChecked(),
            render_mode=render.currentData(),
            loose=['No','Mono','Tags'][loose.currentIndex()],
            annotations=anns.isChecked(), cloud=cloud.isChecked(),
            current_view=-1 in selected,
            current_view_position=selected.index(-1) if -1 in selected else 0,
            scenes=[index for index in selected if index >= 0],
        )
        result = export_html(app.scene, filename, options, app.viewport)
        app.viewport.flash_status(f"HTML3D exporté : {result['bytes']/1048576:.1f} Mo",10000)
        if opening.isChecked():QDesktopServices.openUrl(QUrl.fromLocalFile(filename))
    except Exception as exc:QMessageBox.critical(app.window,'Export HTML3D',str(exc));traceback.print_exc()

def setup(app):
    action=QAction('FGId Export HTML3D',app.window);action.triggered.connect(lambda:show_export(app))
    old=getattr(app.window,'_fgid_html3d_action',None)
    if old:
        app.window.menuBar().removeAction(old);old.deleteLater()
    menu=next((a.menu() for a in app.window.menuBar().actions() if a.text().replace('&','')=='Extensions'),None)
    (menu or app.window.menuBar()).addAction(action)
    app.window._fgid_html3d_action=action

