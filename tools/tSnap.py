from qgis.core import (
    QgsGeometry,
    QgsWkbTypes
)
from qgis.gui import QgsVertexMarker
from qgis.PyQt.QtGui import QColor
from .tMathDef import Vector


class SnapTool:
    def __init__(self, canvas, iface):
        self.canvas = canvas
        self.iface = iface 
        self.snap_mark = QgsVertexMarker(canvas)
        self.snap_mark.setColor(QColor(255, 255, 0))
        self.snap_mark.setPenWidth(2)
        self.snap_mark.setIconSize(10)
        self.vector = Vector()

    def check_snap(self, point, vertices):
        try:
            snap_point = self.canvas.getCoordinateTransform().toMapCoordinates(point) 
        except:
            snap_point = point
        snapper = self.canvas.snappingUtils()
        snap_match = snapper.snapToMap(snap_point)
        snap_type = None
        snapped = False
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
    
    
    def snap_parallel(self, pos, vertices, index):
        point_qgs = self.check_snap(pos, vertices)[1]
        nearest_ids = index.nearestNeighbor(point_qgs, 1)  # Знаходження найближчого об'єкта
        if not nearest_ids:
                return
        obj = self.iface.activeLayer().getFeature(nearest_ids[0])
        geom = obj.geometry()
        closest_side = None
        min_dist = float('inf')
        polygon = None
        layer = self.iface.activeLayer()
        if layer.wkbType() == QgsWkbTypes.Polygon:
            polygon = geom.asPolygon()[0]
        elif layer.wkbType() == QgsWkbTypes.MultiPolygon or QgsWkbTypes.MultiPolygonZ or QgsWkbTypes.PolygonZ:
            polygons = geom.asMultiPolygon()
            first_polygon = polygons[0]
            polygon_geom = QgsGeometry.fromPolygonXY(first_polygon)
            polygon = polygon_geom.asPolygon()[0]
        for i in range(len(polygon) - 1):
            line = QgsGeometry.fromPolylineXY([polygon[i], polygon[i + 1]])
            dist = line.distance(QgsGeometry.fromPointXY(point_qgs))
            if dist < min_dist:
                min_dist = dist
                closest_side = line
        points = closest_side.asPolyline()
        pintsList = []
        for point in points:
            x = point.x()
            y = point.y()
            pintsList.append((x, y))
        
        point_self = self.vector.rectangle_diagonal(pintsList, vertices)

        return point_self