import math
from pathlib import Path
from functools import partial
from qgis.PyQt.QtCore import Qt
import numpy as np
from qgis.core import (
    QgsApplication, 
    QgsSettings, 
    QgsGeometry, 
    QgsPointXY, 
    QgsWkbTypes, 
    QgsFeature, 
    QgsVectorLayer,
    QgsSnappingUtils,
    QgsProject
)
from qgis.gui import QgisInterface, QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsMapToolEmitPoint
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator, QUrl
from qgis.PyQt.QtGui import QColor, QCursor, QDesktopServices, QIcon, QKeyEvent
from qgis.PyQt.QtWidgets import QAction, QMessageBox

########### OrthocadPlugin Class ###############

class OrthocadPlugin:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.tool = None
        
        self.locale = QgsSettings().value("locale/userLocale", QLocale().name())[0:2]
        locale_path = Path(__file__).parent / "i18n" / f"orthocad_{self.locale}.qm"
        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path.resolve()))
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.action_perpendicular = QAction(
            QIcon(),  # Add a suitable icon here
            self.tr("Perpendicular Polygon Tool"),
            self.iface.mainWindow(),
        )
        self.action_perpendicular.triggered.connect(self.togglePerpendicularTool)
        self.iface.addPluginToMenu("Orthocad", self.action_perpendicular)

    def togglePerpendicularTool(self):
        if self.tool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.tool = None
        else:
            self.tool = PerpendicularPolygonTool(self.iface.mapCanvas(), self.iface)
            self.iface.mapCanvas().setMapTool(self.tool)

    def tr(self, message: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, message)

    def unload(self):
        self.iface.removePluginMenu("Orthocad", self.action_perpendicular)
        if self.tool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.tool.ClearSketch()
        

# ########## PerpendicularPolygonTool Class ###############

class PerpendicularPolygonTool(QgsMapTool):
    def __init__(self, canvas, iface):
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.iface = iface
        self.canvas = canvas
        self.vertices = []
        self.rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
        self.last_line = None
        self.perpendicular_start = None
        self.drawing = False  # Flag to indicate if drawing is active

        # snap marker
        self.snap_mark = QgsVertexMarker(self.canvas)
        self.snap_mark.setColor(QColor(255, 255, 0))
        self.snap_mark.setPenWidth(2)
        self.snap_mark.setIconType(QgsVertexMarker.ICON_BOX)
        self.snap_mark.setIconSize(10)
        
    def canvasMoveEvent(self, event):
        coord = self.toMapCoordinates(event.pos())
        self.snap_mark.hide()
        self.snapPoint = False
        self.snapPoint = self.checkSnapToPoint(event.pos())

        if self.snapPoint[0]:
            self.snap_mark.setCenter(self.snapPoint[1])
            self.snap_mark.show()

        if len(self.vertices) == 1:
            # Draw line from the first point to the current cursor position
            temp_vertices = [self.vertices[0], coord]
            self.updateRubberBand(temp_vertices)
        elif self.drawing and self.last_line:
            new_point = self.snapToPerpendicular(coord)
            self.updateRubberBand(self.vertices + [new_point])

    def get_vector(self, p1, p2):
        # Координати точок
        x1, y1 = p1
        x2, y2 = p2

        # Вектор лінії
        vector = np.array([x2 - x1, y2 - y1])

        # Перпендикулярний вектор
        perpendicular_vector = np.array([-vector[1], vector[0]])

        # Довжина перпендикулярного вектора для нормалізації
        length = np.linalg.norm(perpendicular_vector)

        # Нормалізуємо перпендикулярний вектор
        normalized_perpendicular_vector = perpendicular_vector / length

        # Визначимо довжину відрізка, наприклад, 1000 одиниць
        segment_length = 1

        # Відрізаємо відрізок на основі нормалізованого перпендикулярного вектора
        half_segment = segment_length / 2
        start_point = np.array([x1, y1]) + half_segment * normalized_perpendicular_vector
        end_point = np.array([x1, y1]) - half_segment * normalized_perpendicular_vector
        return ((start_point[0], start_point[1]), (end_point[0], end_point[1]))

    def line_intersection(self, p1, p2, q1, q2):
        """
        Знаходить точку перетину двох ліній, заданих двома відрізками.
        
        :param p1: Перша точка першого відрізка (x1, y1)
        :param p2: Друга точка першого відрізка (x2, y2)
        :param q1: Перша точка другого відрізка (x3, y3)
        :param q2: Друга точка другого відрізка (x4, y4)
        :return: Точка перетину або None, якщо лінії не перетинаються
        """
        # Векторні координати
        p1 = np.array(p1)
        p2 = np.array(p2)
        q1 = np.array(q1)
        q2 = np.array(q2)
        
        # Вектори
        d1 = p2 - p1
        d2 = q2 - q1
        
        # Матриця системи рівнянь
        denom = np.cross(d1, d2)
        
        
        # Рівняння для параметрів t і s
        diff = q1 - p1
        t = np.cross(diff, d2) / denom
        intersection = p1 + t * d1
        
        # Перетворення в стандартний тип Python
        intersection = tuple(map(float, intersection))

        if denom == 0:
            intersection = False

        return intersection



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
                self.vertices.append(self.snapToPerpendicular(coord))
                self.last_line = (self.vertices[-2], self.vertices[-1])
                self.drawing = True  # Continue drawing
        elif event.button() == 2:
                self.last_line = (self.vertices[-2], self.vertices[-1])
                self.createPerpendicularPolygon()
                self.drawing = False  # Continue drawing
            
    


    def checkSnapToPoint(self, point):
        snapped = False
        snap_point = self.toMapCoordinates(point)
        snapper = self.canvas.snappingUtils()
        snap_match = snapper.snapToMap(point)
        
        if snap_match.hasVertex():
            snap_point = snap_match.point()
            snapped = True
        else:
            # Check snapping to own points
            for vertex in self.vertices:
                if snap_point.distance(vertex) < self.canvas.mapUnitsPerPixel() * 10:  # Adjust threshold as needed
                    snap_point = vertex
                    snapped = True
                    break
        
        return snapped, snap_point
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == 67 or event.key() == 67:
            if len(self.vertices) >= 3:
                ort_1 = self.get_vector((self.vertices[-1].x(), self.vertices[-1].y()), (self.vertices[-2].x(), self.vertices[-2].y()))
                ort_2 = self.get_vector((self.vertices[0].x(), self.vertices[0].y()), (self.vertices[1].x(), self.vertices[1].y()))
                point = self.line_intersection((self.vertices[-1].x(), self.vertices[-1].y()), ort_1[0], (self.vertices[0].x(), self.vertices[0].y()), ort_2[0])
                if point == False:
                    self.last_line = (self.vertices[-2], self.vertices[-1])
                    self.createPerpendicularPolygon()
                    self.drawing = False  # Continue drawing
                else: 
                    qgs_point = QgsPointXY(point[0], point[1])
                    self.vertices.append(self.snapToPerpendicular(qgs_point))
                    self.createPerpendicularPolygon()
                    self.drawing = False
  
        if event.key() == Qt.Key_Escape:
            self.vertices = []
            self.rubber_band.reset()
            self.drawing = False
    
    def snapToPerpendicular(self, point):
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
        # Clear the sketch
        self.vertices = []
        self.rubber_band.reset()  # Clear the rubber band
        self.drawing = False  # Ensure drawing is stopped

    def createPerpendicularPolygon(self):
        if len(self.vertices) < 2:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Please define at least two points.")
            return

        layer = self.iface.activeLayer()
        if not layer or layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Please select a polygon layer to sketch.")
            return

        layer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPolygonXY([self.vertices]))
        layer.addFeature(feature)
        self.ClearSketch()
       
