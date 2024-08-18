from pathlib import Path
from qgis.core import (
    QgsSettings,
    QgsMapLayer,
    QgsWkbTypes
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.PyQt.QtGui import QIcon, QKeySequence
from qgis.PyQt.QtWidgets import QAction
from .tools import (PerpendicularPolygonTool, 
                    SonarHandler,  
                    SemanticEditor)
from .resources import *
from PyQt5 import QtWidgets, Qt


########### Orthocad Plugin Main Class ###############
class OrthocadPlugin():
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.tool = None
        self.sonar = None
        self.setup_signals()

        
        self.locale = QgsSettings().value("locale/userLocale", QLocale().name())[0:2]
        locale_path = Path(__file__).parent / "i18n" / f"orthocad_{self.locale}.qm"
        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path.resolve()))
            QCoreApplication.installTranslator(self.translator)
        
    def initGui(self):
        self.toolbar = self.iface.addToolBar("OrthoCAD-Tool")
        self.action_perpendicular = QAction(
            QIcon(':/plugins/Qorthocad/icons/orthotool.svg'),
            'Otho Tool',
            self.iface.mainWindow(),
        )
        self.sonar_tool = QAction(
            QIcon(':/plugins/Qorthocad/icons/sonar.svg'),
            'Sonar',
            self.iface.mainWindow(),
        )
        self.toolbar.addAction(self.sonar_tool)
        self.sonar_tool.setCheckable(True)
        self.action_perpendicular.triggered.connect(self.toggle_ortho_tool)
        self.sonar_tool.triggered.connect(self.toggle_sonar)
        self.toolbar.addAction(self.action_perpendicular)
        self.action_perpendicular.setCheckable(True)
        self.action_perpendicular.setShortcut(QKeySequence("Q"))
        self.startEditSemantic = QAction("Semantic", self.iface.mainWindow())
        self.toolbar.addAction(self.startEditSemantic)
        self.startEditSemantic.setShortcut(QKeySequence("Space"))
        self.startEditSemantic.triggered.connect(self.show_semantic_edit)
        self.action_perpendicular.setEnabled(False)
        self.iface.currentLayerChanged.connect(self.update_action_status)

    def show_semantic_edit(self):
        dialog = SemanticEditor()
        if dialog.exec_():
            text = dialog.get_text()
            print(f"Введений текст: {text}")

    def toggle_sonar(self):
        
        if self.sonar:
            self.sonar = None
            self.sonar_tool.setChecked(False)
        else:
            self.sonar = SonarHandler(self.iface.activeLayer(), self.iface.mapCanvas())  
            self.sonar_tool.setChecked(True)

    def toggle_ortho_tool(self):
        
        if self.tool:
            self.tool.hide_snap_mark()
            self.tool.sketch.clear_sketch()
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.tool = None
            self.action_perpendicular.setChecked(False)
        else:
            self.tool = PerpendicularPolygonTool(self.iface.mapCanvas(), self.iface)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.action_perpendicular.setChecked(True)
        
    def setup_signals(self):
        self.iface.mapCanvas().mapToolSet.connect(self.on_map_tool_set)
    
    def on_map_tool_set(self, tool):
        if tool != self.tool:
            self.tool = None
            self.action_perpendicular.setChecked(False)

    def tr(self, message: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, message)

    def unload(self):
        self.iface.removePluginMenu("Orthocad", self.action_perpendicular)
        
    def update_action_status(self):
        layer = self.iface.activeLayer()
        if layer and layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            self.action_perpendicular.setEnabled(True)
        else:
            self.action_perpendicular.setEnabled(False)