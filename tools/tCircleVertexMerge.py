from qgis.core import QgsPointXY, QgsGeometry, QgsFeatureRequest, QgsVertexId, QgsWkbTypes, QgsGeometryUtils
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtGui import QColor
import math

class CircleVertexMerge(QgsMapTool):
    def __init__(self, canvas, iface):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface
        self.circle_rubberband = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.circle_rubberband.setColor(QColor(255, 0, 0, 150))
        self.circle_rubberband.setWidth(2)
        self.center_point = None
        self.radius = None
        self.layer = iface.activeLayer()

    def canvasPressEvent(self, event):
        self.center_point = self.toMapCoordinates(event.pos())

    def canvasMoveEvent(self, event):
        if self.center_point:
            radius_point = self.toMapCoordinates(event.pos())
            self.radius = math.sqrt(self.center_point.sqrDist(radius_point))
            self.updateCircle()

    def canvasReleaseEvent(self, event):
        self.mergeVertices()
        self.circle_rubberband.reset(QgsWkbTypes.PolygonGeometry)
        self.center_point = None

    def updateCircle(self):
        points = []
        for i in range(0, 360):
            angle = math.radians(i)
            x = self.center_point.x() + self.radius * math.cos(angle)
            y = self.center_point.y() + self.radius * math.sin(angle)
            points.append(QgsPointXY(x, y))

        geom = QgsGeometry.fromPolygonXY([points])
        self.circle_rubberband.setToGeometry(geom, None)

    def mergeVertices(self):
        if not self.layer or not self.center_point or not self.radius:
            return

        # Створюємо геометрію буфера кола на основі поточного радіуса
        circle_geom = QgsGeometry.fromPointXY(self.center_point).buffer(self.radius, 50)

        # Отримуємо лише ті об'єкти, які перетинаються з буфером кола
        request = QgsFeatureRequest().setFilterRect(circle_geom.boundingBox())
        features = self.layer.getFeatures(request)

        for feature in features:
            geom = feature.geometry()
            # Перевіряємо чи геометрія потрапляє у коло
            if geom.intersects(circle_geom):
                # Ітеруємо через всі вузли геометрії
                for vertex_id, vertex in enumerate(geom.vertices()):
                    vertex_xy = QgsPointXY(vertex)  # Перетворюємо QgsPoint на QgsPointXY
                    if circle_geom.contains(QgsGeometry.fromPointXY(vertex_xy)):
                        geom.moveVertex(self.center_point.x(), self.center_point.y(), vertex_id)

                self.layer.changeGeometry(feature.id(), geom)