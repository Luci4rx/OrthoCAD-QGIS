
from qgis.core import (
    QgsGeometry
)
from qgis.gui import QgsVertexMarker
from qgis.PyQt.QtGui import QColor


class SnapTool:
    def __init__(self, canvas, iface):
        self.canvas = canvas
        self.iface = iface 
        self.snap_mark = QgsVertexMarker(canvas)
        self.snap_mark.setColor(QColor(255, 255, 0))
        self.snap_mark.setPenWidth(2)
        self.snap_mark.setIconSize(10)

    def check_snap(self, point, vertices):
        snapped = False
        snap_point = self.canvas.getCoordinateTransform().toMapCoordinates(point) 
        snapper = self.canvas.snappingUtils()
        snap_match = snapper.snapToMap(snap_point)
        snap_type = None
        # Перевірка прив'язки до вершин
        if snap_match.hasVertex():
            snap_point = snap_match.point()
            snapped = True
            snap_type = 0

        # Перевірка прив'язки до власних точок
        if not snapped:
            for vertex in vertices:
                if snap_point.distance(vertex) < self.canvas.mapUnitsPerPixel() * 10:  # Змінити поріг при необхідності
                    snap_point = vertex
                    snapped = True
                    break

        # Перевірка прив'язки до ліній
        if not snapped and snap_match.hasEdge():
            edge_snap_point = snap_match.point()
            if snap_point.distance(edge_snap_point) < self.canvas.mapUnitsPerPixel() * 10:  # Змінити поріг при необхідності
                snap_point = edge_snap_point
                snapped = True
                snap_type = 1
        return snapped, snap_point, snap_type