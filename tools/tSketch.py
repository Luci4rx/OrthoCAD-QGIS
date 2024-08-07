from qgis.gui import QgsRubberBand
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsWkbTypes
)

class SketchShape:
    def __init__(self, canvas, iface):
        self.iface = iface
        self.canvas = canvas
        self.vertices = []
        self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
        self.last_line = None
        self.perpendicular_start = None
        self.drawing = False