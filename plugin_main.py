from pathlib import Path
from qgis.core import (
    QgsSettings, 
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .tools import PerpendicularPolygonTool
from .resources import *

########### Orthocad Plugin Main Class ###############
class OrthocadPlugin:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.tool = None
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
        self.action_perpendicular.triggered.connect(self.toggle_ortho_tool)
        self.toolbar.addAction(self.action_perpendicular)
        self.action_perpendicular.setCheckable(True)
      

    def toggle_ortho_tool(self):
        if self.tool:
            self.tool.ClearSketch()
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
        self.tool = PerpendicularPolygonTool(self.iface.mapCanvas(), self.iface)
        self.tool.ClearSketch()
        self.iface.removePluginMenu("Orthocad", self.action_perpendicular)
        if self.tool:
            self.iface.mapCanvas().unsetMapTool(self.tool)


