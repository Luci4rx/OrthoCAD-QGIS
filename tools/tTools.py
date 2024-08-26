import math
from qgis.PyQt.QtCore import Qt, QEvent, QObject
from qgis.core import (
    QgsPointXY,
    QgsSpatialIndex
)
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapToolEmitPoint, QgsMapCanvas, QgsMapToolAdvancedDigitizing
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
        self.eventFilterOrtho = EventFilterOrthoTool(self)  # Передаємо self для можливості доступу до методів
        iface.mapCanvas().installEventFilter(self.eventFilterOrtho)
        iface.mapCanvas().viewport().installEventFilter(self.eventFilterOrtho)
        self.FreeLine = False

        
        
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
        if self.drawing and self.FreeLine:
            new_point = coord
            self.sketch.update_sketch(self.sketch.vertices + [new_point])
        elif self.drawing and self.sketch.last_line:
            new_point = self.snap_ortho(coord)
            self.sketch.update_sketch(self.sketch.vertices + [new_point])
        

    def canvasReleaseEvent(self, event):
         pass



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
            elif self.drawing and self.FreeLine:
                self.sketch.vertices.append(coord)
                self.sketch.last_line = (self.sketch.vertices[-2], self.sketch.vertices[-1])
                self.drawing = True  # Continue drawing
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
        
    def hide_snap_mark(self):
        self.snap.snap_mark.hide()


class EventFilterOrthoTool(QObject):
    def __init__(self, othotool, parent=None):
        super().__init__(parent)
        self.othoTool = othotool
        self.parent = parent

    def eventFilter(self, obj, event):
        if isinstance(obj, QgsMapCanvas):
            if event.type() == QEvent.KeyPress:
                if (event.key() == Qt.Key_B): 
                    if self.othoTool.FreeLine:
                        self.othoTool.FreeLine = False
                    else:
                        self.othoTool.FreeLine = True
                if (event.key() == Qt.Key_E) and len(self.othoTool.sketch.vertices) == 1: 
                    point = self.othoTool.snap.snap_parallel(cursor_position(self.othoTool.canvas), self.othoTool.sketch.vertices,  self.othoTool.index)
                    qgs_point = QgsPointXY(point[0], point[1])
                    self.othoTool.sketch.vertices.append(qgs_point)
                    self.othoTool.sketch.last_line = (self.othoTool.sketch.vertices[0], self.othoTool.sketch.vertices[1])
                    self.othoTool.drawing = True
                else:
                    super().eventFilter(self.othoTool, event)
                def add_mouse_coord():
                    beforepoint = self.othoTool.snap_ortho(cursor_position(self.othoTool.canvas))
                    self.othoTool.sketch.vertices.append(beforepoint)
                    self.othoTool.sketch.last_line = (self.othoTool.sketch.vertices[-2], self.othoTool.sketch.vertices[-1])
                def create_point(point):
                    qgs_point = QgsPointXY(point[0], point[1])
                    self.othoTool.sketch.vertices.append(self.othoTool.snap_ortho(qgs_point))
                    self.othoTool.sketch.complete_polygon(self.othoTool.sketch.vertices, self.othoTool.index)   
                    self.othoTool.drawing = False
                if (event.key() == Qt.Key_W) and len(self.othoTool.sketch.vertices) > 1: 
                    point = self.othoTool.vector.get_projectpoint(self.othoTool.sketch.vertices)
                    if len(self.othoTool.sketch.vertices) > 2 and point != False: 
                        create_point(point)
                    elif len(self.othoTool.sketch.vertices) == 2 or point == False:
                            add_mouse_coord()
                            point = self.othoTool.vector.get_projectpoint(self.othoTool.sketch.vertices)
                            create_point(point)
                else:
                    super().eventFilter(self.othoTool, event)

                if event.key() == Qt.Key_Escape:
                    self.othoTool.sketch.vertices = []
                    self.othoTool.sketch.rubber_band.reset()
                    self.othoTool.drawing = False
                    return True
                else:
                    super().eventFilter(self.othoTool, event)

        return super().eventFilter(obj, event)
    
