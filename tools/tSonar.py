from qgis.PyQt.QtCore import QObject
from qgis.core import (
    QgsProject, 
    QgsGeometry, 
    QgsWkbTypes, 
    QgsPointXY, 
    QgsFeature, 
)
from qgis.PyQt.QtCore import QVariant
class FeatureCreatedHandler(QObject):
    def __init__(self, layer):
        super().__init__()
        self.layer = layer
        self.layer.featureAdded.connect(self.on_feature_added)
    
    def on_feature_added(self, fid):
        feature = self.layer.getFeature(fid)
        geom = feature.geometry()
        short_segments = []
        for ring in geom.asPolygon():
            for i in range(len(ring) - 1):
                segment_start = QgsPointXY(ring[i])
                segment_end = QgsPointXY(ring[i + 1])
                segment_length = segment_start.distance(segment_end)
                if segment_length < 1.11:
                    short_segments.append((segment_start, segment_end, segment_length))


        print(short_segments)