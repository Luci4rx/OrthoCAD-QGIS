import numpy as np
from qgis.PyQt.QtGui import QCursor

class Vector:
    def get_vector_ort(self, p1, p2):
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
    
    def get_projectpoint(self, vertices):
        ort_1 = self.get_vector_ort((vertices[-1].x(), vertices[-1].y()), (vertices[-2].x(), vertices[-2].y()))
        ort_2 = self.get_vector_ort((vertices[0].x(), vertices[0].y()), (vertices[1].x(), vertices[1].y()))
        point = self.line_intersection((vertices[-1].x(), vertices[-1].y()), ort_1[0], (vertices[0].x(), vertices[0].y()), ort_2[0])
        return point
    
    def rectangle_diagonal(self, line, vertices):
        x1, y1 = line[0][0], line[0][1]
        x2, y2 = line[1][0], line[1][1]
        direction_x = x2 - x1
        direction_y = y2 - y1
        length_direction = (direction_x**2 + direction_y**2) ** 0.5
        norm_direction_x = direction_x / length_direction
        norm_direction_y = direction_y / length_direction
        parallel_point_end = (vertices[0].x() + norm_direction_x * 1, vertices[0].y()  + norm_direction_y * 1)
        line_par = (vertices[0].x(), vertices[0].y()), parallel_point_end
        ort_2 = self.get_vector_ort((line_par[0][0], line_par[0][1]), (line_par[1][0], line_par[1][1]))
        point_int = self.line_intersection(ort_2[0], ort_2[1], line[0], line[1])
        return point_int

def cursor_position(canvas):
        global_pos = QCursor.pos()
        screen_pos = canvas.mapFromGlobal(global_pos)
        map_point = canvas.getCoordinateTransform().toMapCoordinates(screen_pos)
        return map_point
