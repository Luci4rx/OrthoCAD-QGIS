import math
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsGeometry, 
    QgsPointXY, 
    QgsWkbTypes, 
    QgsFeature
)
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsMapToolEmitPoint
from qgis.PyQt.QtGui import QColor, QCursor, QKeyEvent
from qgis.PyQt.QtWidgets import QMessageBox

from .MathDef import Vector
from .tSketch import SketchShape

class PerpendicularPolygonTool(QgsMapTool):
    def __init__(self, canvas, iface):
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.iface = iface
        self.canvas = canvas
        # self.vertices = []
        # self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        # self.rubber_band.setColor(QColor(255, 0, 0, 100))
        # self.rubber_band.setWidth(2)
        # self.last_line = None
        # self.perpendicular_start = None
        # self.drawing = False  # Flag to indicate if drawing is active
        self.sketch = SketchShape()
        self.vector = Vector()
        # snap marker
        self.snap_mark = QgsVertexMarker(self.canvas)
        self.snap_mark.setColor(QColor(255, 255, 0))
        self.snap_mark.setPenWidth(2)
        self.snap_mark.setIconSize(10)
        
        

    def canvasMoveEvent(self, event):
        coord = self.toMapCoordinates(event.pos())
        self.snap_mark.hide()
        self.snapPoint = False
        self.snapPoint = self.checkSnapToGeometry(event.pos())
        if self.snapPoint[-1] == 0:
            self.snap_mark.setIconType(QgsVertexMarker.ICON_BOX)
        elif self.snapPoint[-1] == 1:
            self.snap_mark.setIconType(QgsVertexMarker.ICON_INVERTED_TRIANGLE)
        if self.snapPoint[0]:
            self.snap_mark.setCenter(self.snapPoint[1])
            self.snap_mark.show()
        if len(self.vertices) == 1:
            # Draw line from the first point to the current cursor position
            temp_vertices = [self.vertices[0], coord]
            self.updateRubberBand(temp_vertices)
        elif self.drawing and self.last_line:
            new_point = self.snap_ortho(coord)
            self.updateRubberBand(self.vertices + [new_point])



    def canvasPressEvent(self, event):
        if event.button() == 1:  # Right mouse button
            if self.snapPoint == False:
                coord = self.toMapCoordinates(event.pos())
            else:
                coord = self.snapPoint[1]
            if not self.vertices:
                self.vertices.append(coord)
                self.perpendicular_start = coord
            elif len(self.vertices) == 1:
                self.vertices.append(coord)
                self.last_line = (self.vertices[0], self.vertices[1])
                self.drawing = True  # Start drawing
                self.updateRubberBand()  # Ensure initial line is drawn
            else:
                # Append new vertex and continue drawing
                self.vertices.append(self.snap_ortho(coord))
                self.last_line = (self.vertices[-2], self.vertices[-1])
                self.drawing = True  # Continue drawing
        elif event.button() == 2:
            if len(self.vertices) > 1:
                self.last_line = (self.vertices[-2], self.vertices[-1])
                self.createPerpendicularPolygon()
                self.drawing = False  # Continue drawing
            else: 
                QMessageBox.critical(self.iface.mainWindow(), "Error", "Щоб зберегти об'єкт створіть скетч")
            
    def checkSnapToGeometry(self, point):
        snapped = False
        snap_point = self.toMapCoordinates(point)
        snapper = self.canvas.snappingUtils()
        snap_match = snapper.snapToMap(point)
        snap_type = None
        # Перевірка прив'язки до вершин
        if snap_match.hasVertex():
            snap_point = snap_match.point()
            snapped = True
            snap_type = 0

        # Перевірка прив'язки до власних точок
        if not snapped:
            for vertex in self.vertices:
                if snap_point.distance(vertex) < self.canvas.mapUnitsPerPixel() * 10:  # Змінити поріг при необхідності
                    snap_point = vertex
                    snapped = True
                    break

        # Перевірка прив'язки до ліній
        if not snapped and snap_match.hasEdge():
            edge_point = snap_match.point()
            if snap_point.distance(edge_point) < self.canvas.mapUnitsPerPixel() * 10:  # Змінити поріг при необхідності
                snap_point = edge_point
                snapped = True
                snap_type = 1
        return snapped, snap_point, snap_type
    
    def cursor_position(self):
        global_pos = QCursor.pos()
        screen_pos = self.canvas.mapFromGlobal(global_pos)
        map_point = self.canvas.getCoordinateTransform().toMapCoordinates(screen_pos)
        return map_point
    
    def keyPressEvent(self, event: QKeyEvent):
        def add_mouse_coord():
            beforepoint = self.snap_ortho(self.cursor_position())
            self.vertices.append(beforepoint)
            self.last_line = (self.vertices[-2], self.vertices[-1])
        def create_point(point):
            qgs_point = QgsPointXY(point[0], point[1])
            self.vertices.append(self.snap_ortho(qgs_point))
            self.createPerpendicularPolygon()
            self.drawing = False
        if (event.key() == 67 or event.key() == 1057) and len(self.vertices) > 1: 
            point = self.vector.get_projectpoint(self.vertices)
            if len(self.vertices) > 2 and point != False: 
                create_point(point)
            elif len(self.vertices) == 2 or point == False:
                    add_mouse_coord()
                    point = self.vector.get_projectpoint(self.vertices)
                    create_point(point)

        if event.key() == Qt.Key_Escape:
            self.vertices = []
            self.rubber_band.reset()
            self.drawing = False
    
    def snap_ortho(self, point):
        if not self.last_line:
            return point

        last_point = self.vertices[-1]
        (x1, y1), (x2, y2) = self.last_line
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)
        dx /= length
        dy /= length

        perp_vector = (-dy, dx)
        proj_length = (point.x() - last_point.x()) * perp_vector[0] + (point.y() - last_point.y()) * perp_vector[1]
        proj_point = QgsPointXY(last_point.x() + proj_length * perp_vector[0], last_point.y() + proj_length * perp_vector[1])
        return proj_point

    def updateRubberBand(self, temp_vertices=None):
        self.rubber_band.reset()
        if not self.vertices:
            return

        if temp_vertices is None:
            temp_vertices = self.vertices.copy()

        if len(temp_vertices) > 1:
            # Draw the line from the first to the last vertex
            self.rubber_band.setToGeometry(QgsGeometry.fromPolygonXY([temp_vertices]), None)
    
    def ClearSketch(self):
        self.vertices = []
        self.rubber_band.reset()  # Clear the rubber band
        self.drawing = False  # Ensure drawing is stopped
    
    
    def createPerpendicularPolygon(self):
        if len(self.vertices) <= 2:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Please define at least two points.")
            self.ClearSketch()
            return

        layer = self.iface.activeLayer()
        if not layer or layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Please select a polygon layer to sketch.")
            self.ClearSketch()
            return

        layer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPolygonXY([self.vertices]))
        layer.addFeature(feature)
        self.ClearSketch()
       
