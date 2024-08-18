from qgis.core import QgsPointXY, QgsWkbTypes
from qgis.PyQt.QtCore import QObject
from qgis.gui import QgsRubberBand
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QColor
from qgis.core import QgsPointXY, QgsSpatialIndex

class SonarHandler(QObject):
    def __init__(self, layer, canvas):
        super().__init__()
        self.layer = layer
        self.canvas = canvas
        self.layer.featureAdded.connect(self.on_feature)
        self.layer.geometryChanged.connect(self.on_feature)
        self.flag = None
        self.rubber_bands = []  # Список для хранения всех RubberBand


    def on_feature(self, fid):
        print('sadsa')
        feature = self.layer.getFeature(fid)
        geom = feature.geometry()
        if feature and feature.id() != self.flag:
            
            short_segments = []
            
            for ring in geom.asPolygon():
                for i in range(len(ring) - 1):
                    segment_start = QgsPointXY(ring[i])
                    segment_end = QgsPointXY(ring[i + 1])
                    segment_length = segment_start.distance(segment_end)
                    
                    if segment_length < 1.11:
                        segment = (segment_start, segment_end)
                        reverse_segment = (segment_end, segment_start)
                        if segment not in short_segments and reverse_segment not in short_segments:
                            short_segments.append(segment)

                            # Создаем новый QgsRubberBand для каждой проблемной линии
                            rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
                            rubber_band.setColor(QColor(255, 0, 0))  # Червоний колір для виділення проблемних сегментів
                            rubber_band.setWidth(5)  # Ширина лінії
                            rubber_band.addPoint(segment_start)
                            rubber_band.addPoint(segment_end)
                            rubber_band.addPoint(segment_start)  # Замикання лінії
                            
                            # Сохраняем rubber_band в список, чтобы предотвратить его удаление
                            self.rubber_bands.append(rubber_band)


            self.flag = feature.id()

        radius = 100  # Radius in meters
        point = geom.pointOnSurface().asPoint()
        # Find the nearest features within the specified radius
        features = self.layer.getFeatures()
        spatial_index = QgsSpatialIndex(features)
        nearest_ids = spatial_index.nearestNeighbor(point, 10)
        min_distance = None
        closest_feature = None
        
        # Iterate through nearest features
        for id in nearest_ids:
            if id == feature.id():
                continue
            
            other_feature = self.layer.getFeature(id)
            other_geom = other_feature.geometry()
            
            # Calculate distance
            distance = geom.distance(other_geom)
            if 0 < distance < radius and (min_distance is None or distance < min_distance):
                min_distance = distance
                closest_feature = other_feature
    
            # If a closest feature is found, create a line
            if min_distance is not None and min_distance < 1.11:
                # Создаем новый QgsRubberBand для каждой проблемной линии
                rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
                rubber_band.setColor(QColor(255, 0, 255))  # Червоний колір для виділення проблемних сегментів
                rubber_band.setWidth(5)  # Ширина лінії
                rubber_band.addPoint(point)
                rubber_band.addPoint(closest_feature.geometry().pointOnSurface().asPoint())          
                # Сохраняем rubber_band в список, чтобы предотвратить его удаление
                self.rubber_bands.append(rubber_band)
            
            
        else:
            return
        
        