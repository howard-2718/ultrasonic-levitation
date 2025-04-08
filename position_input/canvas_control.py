"""
Control position of bead using a canvas.
"""
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import sys
import redis
import time

import numpy as np

def get_time():
    return time.time_ns() * 1e-9

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 600, 600)  # Set window size
        self.setWindowTitle('Canvas Drawn Path Control')

        self.side_length = 16.8  # Dimensions in cm
        self.board_x = self.side_length / 2 
        self.board_y = self.side_length / 2
        self.board_z = 1.0

        self.canvas_x = 100
        self.canvas_y = 100

        self.label = QLabel(self)
        self.label.move(self.canvas_x, self.canvas_y)
        self.canvas = QtGui.QPixmap(400, 400)
        self.canvas.fill(Qt.white)

        self.label.setPixmap(self.canvas)

        # Draw an initial dot (pixel) at the center of the board
        init_painter = QtGui.QPainter(self.label.pixmap())
        init_painter.drawPoint(200, 200)
        init_painter.end()

        self.last_x, self.last_y = None, None

        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.redis.publish("positions", repr([[self.board_x / 100, self.board_y / 100, self.board_z / 100]]).encode('utf-8'))  # Publish the initial position
        
        self.last_sent = get_time()
        self.num_sends = 0

        # List of path points
        self.path_points = []

        # Add a button to clear the canvas
        self.clear_button = QPushButton('Clear Canvas', self)
        self.clear_button.setGeometry(450, 500, 120, 40)  # Position at bottom right
        self.clear_button.clicked.connect(self.clear_canvas)

        # Add a button to convert path to coordinates and execute
        self.clear_button = QPushButton('Execute Path', self)
        self.clear_button.setGeometry(450, 60, 120, 40)  # Position at bottom right
        self.clear_button.clicked.connect(self.execute_path)

    # Send board position to Redis
    def send_positions(self):
        curr_time = get_time()
        
        base_position = [self.board_x / 100, self.board_y / 100, self.board_z / 100]
        positions = [base_position]
        self.num_sends += 1

        msg_packed = repr(positions).encode('utf-8')
        self.redis.publish("positions", msg_packed)
        
        self.last_sent = curr_time

    def mouseMoveEvent(self, e):
        if self.last_x is None:  # Only for the first event
            self.last_x = e.x() - self.canvas_x
            self.last_y = e.y() - self.canvas_y
            return

        painter = QtGui.QPainter(self.label.pixmap())

        # Pen customization
        p = painter.pen()
        p.setWidth(4)
        painter.setPen(p)

        painter.drawLine(self.last_x, self.last_y, e.x() - self.canvas_x, e.y() - self.canvas_y)
        painter.end()
        self.update()

        print(f"Mouse drawn: x - {e.x() - self.canvas_x} and y - {e.y() - self.canvas_y}")
        self.path_points.append([e.x() - self.canvas_x, e.y() - self.canvas_y])

        # Update the origin for next time
        self.last_x = e.x() - self.canvas_x
        self.last_y = e.y() - self.canvas_y

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None

    def clear_canvas(self):
        self.path_points = []

        self.canvas.fill(Qt.white)
        self.label.setPixmap(self.canvas)
        self.update()

    def execute_path(self):
        print(self.path_points)  # Confirm that the path points look good 

        # Interpolate data thrice
        self.path_points = self.interpolate_data(self.path_points)
        self.path_points = self.interpolate_data(self.path_points)
        # self.path_points = self.interpolate_data(self.path_points)

        # Currently, execute the path step-by-step. Perhaps not ideal
        UPDATE_RATE = 6000  # In Hz
        time_step = 1.0 / UPDATE_RATE

        for point in self.path_points:
            self.board_x = point[0] * self.side_length / 400
            self.board_y = point[1] * self.side_length / 400

            print(f"Sending coordinates: x - {self.board_x:.4f}, y - {self.board_y:.4f}, z - {self.board_z:.4f}, at time t = {get_time():.6f}")
            self.send_positions()

            time.sleep(time_step)  # Wait out the time_step before sending the next position

    def interpolate_data(self, array):
        interpolated = []

        for i in range(len(array) - 1):
            interpolated.append(array[i])
            midpoint = [(array[i][0] + array[i+1][0]) / 2, (array[i][1] + array[i+1][1]) / 2]
            interpolated.append(midpoint)

        interpolated.append(array[-1])  # Append the last element
        
        return interpolated

    # Idea from Miti: make Functionality where it can just go back and forth along the same contour


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())
