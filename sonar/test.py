
# Перевірка сегментів #№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№
from qgis.core import (
    QgsProject, 
    QgsGeometry, 
    QgsWkbTypes, 
    QgsPointXY, 
    QgsFeature, 
    QgsVectorLayer, 
    QgsField, 
    QgsSpatialIndex
)
from qgis.PyQt.QtCore import QVariant

# Отримуємо активний шар
layer = QgsProject.instance().mapLayersByName('Single parts')[0]

# Створюємо новий шар для ліній
line_layer = QgsVectorLayer('LineString?crs=epsg:32643', 'Lines from segments', 'memory')
prov = line_layer.dataProvider()
prov.addAttributes([QgsField('Length', QVariant.Double)])
line_layer.updateFields()

# Додаємо новий шар до проекту
QgsProject.instance().addMapLayer(line_layer)

# Створюємо просторовий індекс для шару
spatial_index = QgsSpatialIndex(layer.getFeatures())

# Отримуємо кількість об'єктів для прогрес бару
total_features = layer.featureCount()

# Список для зберігання всіх лінійних об'єктів
lines_to_add = []

# Ітеруємося по всіх об'єктах шару
for feature_index, feature in enumerate(layer.getFeatures()):
    
    geom = feature.geometry()
    
    # Перевіряємо, чи це полігональний тип геометрії
    if geom.type() == QgsWkbTypes.PolygonGeometry:
        polygons = geom.asPolygon()  # Отримуємо кільця полігону

        # Ітеруємося по кожному кільцю
        for polygon_index, ring in enumerate(polygons):
            num_vertices = len(ring)  # Отримуємо кількість точок у кільці

            # Ітеруємося по кожному сегменту в кільці
            for i in range(num_vertices - 1):
                start_point = ring[i]
                end_point = ring[i + 1]
                segment_length = QgsPointXY(start_point).distance(QgsPointXY(end_point))

                if segment_length < 1.11:
                    print(f'Помилка у фічері {feature_index + 1}, кільце {polygon_index + 1}, сегмент {i + 1}')
                    
                    # Створюємо лінію і додаємо її до списку
                    line = QgsFeature(line_layer.fields())
                    line_geom = QgsGeometry.fromPolylineXY([QgsPointXY(start_point), QgsPointXY(end_point)])
                    line.setGeometry(line_geom)
                    line.setAttribute('Length', segment_length)
                    lines_to_add.append(line)

    # Виводимо прогрес в консоль
    progress = int((feature_index + 1) / total_features * 100)
    print(f"Processing: {progress}% completed", end='\r')

# Додаємо всі лінії до шару одразу
prov.addFeatures(lines_to_add)

# Завершуємо оновлення шару
line_layer.updateExtents()
print("\nProcessing complete!")




# Перевірка відстані між об'єктами #№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№
from qgis.core import QgsProject, QgsGeometry, QgsFeature, QgsPointXY, QgsVectorLayer, QgsField
from qgis.PyQt.QtCore import QVariant

# Parameters
radius = 500  # Radius in meters

def process_features():
    # Get the active layer
    layer = QgsProject.instance().mapLayersByName('Single parts')[0]

    # Create a new vector layer for storing lines
    vector_layer = QgsVectorLayer("LineString?crs=EPSG:32643", "Shortest distances", "memory")
    provider = vector_layer.dataProvider()

    # Add a field for storing length
    provider.addAttributes([QgsField("length", QVariant.Double)])
    vector_layer.updateFields()

    # Create a spatial index for the layer
    index = QgsSpatialIndex(layer.getFeatures())

    features = []
    feature_count = layer.featureCount()
    
    for i, feature in enumerate(layer.getFeatures()):
        geom = feature.geometry()
        point = geom.pointOnSurface().asPoint()
        
        # Find the nearest features within the specified radius
        nearest_ids = index.nearestNeighbor(point, 10)
        
        min_distance = None
        closest_feature = None
        
        # Iterate through nearest features
        for id in nearest_ids:
            if id == feature.id():
                continue
            
            other_feature = layer.getFeature(id)
            other_geom = other_feature.geometry()
            
            # Calculate distance
            distance = geom.distance(other_geom)
            if 0 < distance < radius and (min_distance is None or distance < min_distance):
                min_distance = distance
                closest_feature = other_feature
        
        # If a closest feature is found, create a line
        if min_distance is not None and min_distance < 1.11:
            line_geom = QgsGeometry.fromPolylineXY([
                QgsPointXY(point),
                QgsPointXY(closest_feature.geometry().pointOnSurface().asPoint())
            ])
            line_feature = QgsFeature()
            line_feature.setGeometry(line_geom)
            line_feature.setAttributes([min_distance])
            features.append(line_feature)
        
        # Print progress
        print(f"Progress: {i + 1}/{feature_count}")
    
    # Add the features to the layer
    provider.addFeatures(features)
    
    # Add the new layer to the map
    QgsProject.instance().addMapLayer(vector_layer)

# Run the processing
process_features()


# Marge #№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry
)
from PyQt5.QtWidgets import QMessageBox

# Получаем активный слой
layer = iface.activeLayer()

if not layer or layer.geometryType() != QgsWkbTypes.PolygonGeometry:
    QMessageBox.critical(None, "Error", "Выберите полигональный слой.")
else:
    # Получаем выбранные объекты
    selected_features = layer.selectedFeatures()

    if len(selected_features) < 2:
        QMessageBox.critical(None, "Error", "Выберите как минимум два объекта для объединения.")
    else:
        # Начинаем редактирование слоя
        layer.startEditing()

        # Создаем объект, который будет хранить объединенную геометрию
        merged_geometry = QgsGeometry()

        # Объединяем геометрии выбранных объектов
        for feature in selected_features:
            if merged_geometry.isEmpty():
                merged_geometry = feature.geometry()
            else:
                merged_geometry = merged_geometry.combine(feature.geometry())

        # Создаем новый объект с объединенной геометрией
        new_feature = QgsFeature(layer.fields())
        new_feature.setGeometry(merged_geometry)

        # Полная очистка атрибутов нового объекта
        new_feature.initAttributes(len(layer.fields()))
        for i in range(len(layer.fields())):
            new_feature.setAttribute(i, None)  # Очищаем атрибуты, присваивая None

        # Добавляем новый объект на слой
        if layer.addFeature(new_feature):
            # Удаляем исходные объекты
            for feature in selected_features:
                layer.deleteFeature(feature.id())

            # Завершаем редактирование
            layer.commitChanges()
            QMessageBox.information(None, "Success", "Объекты успешно объединены.")
        else:
            layer.rollBack()
            QMessageBox.critical(None, "Error", "Ошибка при добавлении нового объекта на слой.")



# Очистка вузлів лишніх #№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№
from qgis.core import QgsFeature, QgsGeometry, QgsVectorLayer, QgsProject

def simplify_geometry(feature, tolerance=0.01):
    """Спрощення геометрії об'єкта з вказаним порогом"""
    geom = feature.geometry()
    simplified_geom = geom.simplify(tolerance)
    return simplified_geom

# Отримання шару та обраних об'єктів
layer = QgsProject.instance().mapLayersByName('Single parts')[0]  # Замість 'YourLayerName' використовуйте ім'я вашого шару

if not layer:
    print("Шар не знайдено!")
else:
    # Перевірте, чи шар підтримує редагування
    if not layer.isEditable():
        layer.startEditing()

    # Отримання всіх вибраних об'єктів
    selected_features = layer.selectedFeatures()

    for feature in selected_features:
        # Спрощення геометрії вибраного об'єкта
        simplified_geom = simplify_geometry(feature, tolerance=0.01)

        # Оновлення геометрії об'єкта
        feature.setGeometry(simplified_geom)
        layer.updateFeature(feature)
    
    # Збереження змін
    layer.commitChanges()
    print("Вибрані об'єкти були спрощені.")
