from qgis.gui import QgsRubberBand
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
        self.rubber_band.reset()
        self.drawing = False

    def update_sketch(self, temp_vertices=None):
        if not self.vertices:
            return
        if temp_vertices is None:
            temp_vertices = self.vertices.copy()
        if len(temp_vertices) > 1:
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

        if layer.wkbType() == QgsWkbTypes.MultiPolygonZ:
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
        self.clear_sketch()