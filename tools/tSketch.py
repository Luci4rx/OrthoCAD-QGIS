from qgis.gui import QgsRubberBand, QtCore
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsWkbTypes,
    QgsGeometry,
    QgsFeature,
    QgsMapLayer,
    QgsPointXY
)
from qgis.PyQt.QtWidgets import QMessageBox

class SketchPolygonShape:
    def __init__(self, canvas, iface):
        self.iface = iface
        self.canvas = canvas
        self.vertices = []
        self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
        self.last_line = None
        self.geometry = None

    def clear_sketch(self):
        self.vertices = []
        self.rubber_band.reset()  # Clear the rubber band
        self.drawing = False  # Ensure drawing is stopped

    def update_sketch(self, temp_vertices=None):
        # self.rubber_band.reset()
        if not self.vertices:
            return
        if temp_vertices is None:
            temp_vertices = self.vertices.copy()
        if len(temp_vertices) > 1:
            # Draw the line from the first to the last vertex
           self.rubber_band.setToGeometry(QgsGeometry.fromPolygonXY([temp_vertices]), None)

    def complete_polygon(self, vertices, index):
        
        if len(vertices) <= 2:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Please define at least two points.")
            self.clear_sketch()
            return

        layer = self.iface.activeLayer()
        if not layer or (layer.type() == QgsMapLayer.RasterLayer or layer.geometryType() != QgsWkbTypes.PolygonGeometry):
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Please select a polygon layer to sketch.")
            self.clear_sketch()
            return
        
        layer.startEditing()
        feature = QgsFeature(layer.fields())

        # Check if layer supports MultiPolygonZ
        if layer.wkbType() == QgsWkbTypes.MultiPolygonZ:
            # Create 3D point sequence
            point_sequence = []
            for vertex in vertices:
                point_sequence.append(QgsPointXY(vertex.x(), vertex.y()))  # Replace 0 with the desired Z value
            self.geometry = QgsGeometry.fromMultiPolygonXY([[point_sequence]])
            feature.setGeometry(self.geometry)
        else:
            self.geometry =  QgsGeometry.fromPolygonXY([vertices])
            feature.setGeometry(self.geometry)
            
            
        layer.addFeature(feature)
        index.insertFeature(feature)
        layer.updateExtents()
        layer.updateFields()
        layer.triggerRepaint()
        self.clear_sketch()