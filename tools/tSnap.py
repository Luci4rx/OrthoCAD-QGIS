class SnapChecker:
   def check_snap(self, point):
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