import math
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsPointXY,
    QgsSpatialIndex
)
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapToolEmitPoint
from qgis.PyQt.QtGui import QKeyEvent
from qgis.PyQt.QtWidgets import QMessageBox

from .tMathDef import Vector, cursor_position
from .tSketch import SketchPolygonShape
from .tSnap import SnapTool


class PerpendicularPolygonTool(QgsMapTool):
    def __init__(self, canvas, iface):
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.iface = iface
        self.canvas = canvas
        self.perpendicular_start = None
        self.drawing = False  # Flag to indicate if drawing is active
        self.vector = Vector()
        self.sketch = SketchPolygonShape(self.iface.mapCanvas(), self.iface)
        self.snap = SnapTool(self.iface.mapCanvas(), self.iface)
        self.index = QgsSpatialIndex(self.iface.activeLayer())
        
        

    def canvasMoveEvent(self, event):
        coord = self.toMapCoordinates(event.pos())
        self.snap.snap_mark.hide()
        self.snapPoint = False
        self.snapPoint = self.snap.check_snap(event.pos(), self.sketch.vertices)
        if self.snapPoint[-1] == 0:
           self.snap.snap_mark.setIconType(QgsVertexMarker.ICON_BOX)
        elif self.snapPoint[-1] == 1:
           self.snap.snap_mark.setIconType(QgsVertexMarker.ICON_INVERTED_TRIANGLE)
        if self.snapPoint[0]:
           self.snap.snap_mark.setCenter(self.snapPoint[1])
           self.snap.snap_mark.show()
        if len(self.sketch.vertices) == 1:
            # Draw line from the first point to the current cursor position
            temp_vertices = [self.sketch.vertices[0], coord]
            self.sketch.update_sketch(temp_vertices)
        elif self.drawing and self.sketch.last_line:
            new_point = self.snap_ortho(coord)
            self.sketch.update_sketch(self.sketch.vertices + [new_point])

    


    def canvasPressEvent(self, event):
        if event.button() == 1:  # Right mouse button
            if self.snapPoint == False:
                coord = self.toMapCoordinates(event.pos())
            else:
                coord = self.snapPoint[1]
            if not self.sketch.vertices:
                self.sketch.vertices.append(coord)
                self.perpendicular_start = coord
            elif len(self.sketch.vertices) == 1:
                self.sketch.vertices.append(coord)
                self.sketch.last_line = (self.sketch.vertices[0], self.sketch.vertices[1])
                self.drawing = True  # Start drawing
                self.sketch.update_sketch()  # Ensure initial line is drawn
            else:
                # Append new vertex and continue drawing
                self.sketch.vertices.append(self.snap_ortho(coord))
                self.sketch.last_line = (self.sketch.vertices[-2], self.sketch.vertices[-1])
                self.drawing = True  # Continue drawing
        elif event.button() == 2:
            if len(self.sketch.vertices) > 1:
                self.sketch.last_line = (self.sketch.vertices[-2], self.sketch.vertices[-1])
                self.sketch.complete_polygon(self.sketch.vertices, self.index)
                self.drawing = False  # Continue drawing
            else: 
                QMessageBox.critical(self.iface.mainWindow(), "Error", "Щоб зберегти об'єкт створіть скетч")
    
    
    def keyPressEvent(self, event: QKeyEvent):
        if (event.key() == Qt.Key_E) and len(self.sketch.vertices) == 1: 
            point = self.snap.snap_parallel(cursor_position(self.canvas), self.sketch.vertices,  self.index)
            qgs_point = QgsPointXY(point[0], point[1])
            self.sketch.vertices.append(qgs_point)
            self.sketch.last_line = (self.sketch.vertices[0], self.sketch.vertices[1])
            self.drawing = True
        def add_mouse_coord():
            beforepoint = self.snap_ortho(cursor_position(self.canvas))
            self.sketch.vertices.append(beforepoint)
            self.sketch.last_line = (self.sketch.vertices[-2], self.sketch.vertices[-1])
        def create_point(point):
            qgs_point = QgsPointXY(point[0], point[1])
            self.sketch.vertices.append(self.snap_ortho(qgs_point))
            self.sketch.complete_polygon(self.sketch.vertices, self.index)   
            self.drawing = False
        if (event.key() == Qt.Key_W) and len(self.sketch.vertices) > 1: 
            point = self.vector.get_projectpoint(self.sketch.vertices)
            if len(self.sketch.vertices) > 2 and point != False: 
                create_point(point)
            elif len(self.sketch.vertices) == 2 or point == False:
                    add_mouse_coord()
                    point = self.vector.get_projectpoint(self.sketch.vertices)
                    create_point(point)

        if event.key() == Qt.Key_Escape:
            self.sketch.vertices = []
            self.sketch.rubber_band.reset()
            self.drawing = False
        
    
    def snap_ortho(self, point):
        if not self.sketch.last_line:
            return point

        last_point = self.sketch.vertices[-1]
        (x1, y1), (x2, y2) = self.sketch.last_line
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)
        if length == 0:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Довжина відрізка дорівнює нулю")
            self.sketch.clear_sketch()
            self.drawing = False
        else:
            dx /= length
            dy /= length
            perp_vector = (-dy, dx)
            proj_length = (point.x() - last_point.x()) * perp_vector[0] + (point.y() - last_point.y()) * perp_vector[1]
            proj_point = QgsPointXY(last_point.x() + proj_length * perp_vector[0], last_point.y() + proj_length * perp_vector[1])
            return proj_point