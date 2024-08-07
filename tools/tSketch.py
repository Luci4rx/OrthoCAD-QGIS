from qgis.gui import QgsRubberBand
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsWkbTypes,
    QgsGeometry 
)

class SketchPolygonShape:
    def __init__(self, canvas, iface):
        self.iface = iface
        self.canvas = canvas
        self.vertices = []
        self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
        self.last_line = None

    def clear_sketch(self):
        self.vertices = []
        self.rubber_band.reset()  # Clear the rubber band
        self.drawing = False  # Ensure drawing is stopped

    def update_sketch(self, temp_vertices=None):
        self.rubber_band.reset()
        if not self.vertices:
            return
        if temp_vertices is None:
            temp_vertices = self.vertices.copy()
        if len(temp_vertices) > 1:
            # Draw the line from the first to the last vertex
           self.rubber_band.setToGeometry(QgsGeometry.fromPolygonXY([temp_vertices]), None)