"""
Control position of bead using a path drawn on an image.
"""
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QTimer
import cv2
from skimage.morphology import skeletonize
import numpy as np
import sys
import redis
import time

def get_time():
    return time.time_ns() * 1e-9

def find_endpoints(skel):
    endpoints = []
    rows, cols = skel.shape

    # For each pixel in the skeleton, check if there is one neighbor pixel in the surrounding eight pixels
    for y in range(1, rows-1):
        for x in range(1, cols-1):
            if skel[y, x] == 1:
                nb = np.sum(skel[y-1:y+2, x-1:x+2]) - 1

                if nb == 1:
                    endpoints.append((x, y))

    return endpoints

def trace_path(skel, start):
    coords = [start]
    visited = set([start])
    current = start
    
    while True:
        x, y = current

        # Encapsulate eight neighbor pixels
        neighbors = [(x + dx, y + dy)  for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]
        
        next_pts = [pt for pt in neighbors if 0 <= pt[0] < skel.shape[1] and 0 <= pt[1] < skel.shape[0] and 
            skel[pt[1], pt[0]] == 1 and pt not in visited]
        
        if not next_pts:
            break

        # If multiple next pixels, simply select the first one
        # Ideally, the image itself should never have branching paths, so this should not be an issue
        current = next_pts[0]
        
        visited.add(current)
        coords.append(current)

    return coords

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 680, 780)  # Set window size
        self.setFixedSize(680, 780)  # Disable resizing

        self.setWindowTitle('Image Path Control')

        # Physical system
        self.side_length = 16.8  # cm
        self.board_z = 1.0

        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        # self.redis.publish("positions", repr([[self.side_length / 2, self.side_length / 2, self.board_z]]).encode('utf-8'))  # Publish a dummy position

        self.last_sent = get_time()
        self.num_sends = 0

        # Control layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Buttons
        self.button_layout = QHBoxLayout()

        self.load_button = QPushButton("Load Path")
        self.load_button.clicked.connect(self.load_image)
        self.button_layout.addWidget(self.load_button)

        self.preprocess_button = QPushButton("Preprocess Path")
        self.preprocess_button.clicked.connect(self.preprocess)
        self.button_layout.addWidget(self.preprocess_button)

        self.execute_button = QPushButton("Execute Path")
        self.execute_button.clicked.connect(self.execute)
        self.button_layout.addWidget(self.execute_button)

        # Speed Input
        self.layout.addLayout(self.button_layout)

        self.interval_layout = QHBoxLayout()

        self.interval_label = QLabel("Interval/Speed (ms per pixel):")
        self.interval_layout.addWidget(self.interval_label)

        self.interval_input = QLineEdit()
        self.interval_input.setText("2")
        self.interval_layout.addWidget(self.interval_input)

        self.layout.addLayout(self.interval_layout)

        # Canvas
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        self.path_loaded = False
        self.img = None

        self.skeleton_loaded = False
        self.skeleton = None

        self.path = None
        self.scaled_path = None

        self.path_pixmap = None

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")

        if file_path:
            pixmap = QtGui.QPixmap(file_path)
            
            # Scale image, preserving aspect ratio
            pixmap = pixmap.scaled(self.width() - 50, self.height() - 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

            self.img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

            self.path_loaded = True

    def preprocess(self):
        if not self.path_loaded: 
            return
        
        _, binary = cv2.threshold(self.img, 127, 1, cv2.THRESH_BINARY_INV)

        self.skeleton = skeletonize(binary.astype(bool)).astype(np.uint8)

        # Update GUI
        skeleton_vis = (self.skeleton * 255).astype(np.uint8)
        height, width = skeleton_vis.shape
        bytes_per_line = width

        qimage = QtGui.QImage(skeleton_vis.data, width, height, bytes_per_line, QtGui.QImage.Format_Grayscale8)

        pixmap = QtGui.QPixmap.fromImage(qimage)
        pixmap = pixmap.scaled(self.width() - 50, self.height() - 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.image_label.setPixmap(pixmap)

        # Find endpoints
        endpoints = find_endpoints(self.skeleton)

        # Create path
        self.path = trace_path(self.skeleton, endpoints[0])

        # Scale path
        img_height, img_width = self.img.shape

        self.scaled_path = []
        for (px, py) in self.path:
            x_coord = (px / img_width) * self.side_length
            y_coord = (py / img_height) * self.side_length
            self.scaled_path.append((x_coord, y_coord))

        # print("First 10 converted path points:", self.scaled_path[:10])

        # Publish position of start point to board
        print(f"Publishing start position: x - {self.scaled_path[0][0]:.4f}, y - {self.scaled_path[0][1]:.4f}, z - {self.board_z:.4f}, at time t = {get_time():.6f}")
        
        # Might need to divide all dimensions by 100
        msg_packed = repr([[self.scaled_path[0][0] / 100, self.scaled_path[0][1] / 100, self.board_z / 100]]).encode('utf-8')
        self.redis.publish("positions", msg_packed)

        self.skeleton_loaded = True

        # Uncomment to save the skeleton to disk
        # save_path, _ = QFileDialog.getSaveFileName(self, "Save Skeleton Image", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)")

        # if save_path:
        #     cv2.imwrite(save_path, skeleton_vis)
    
    def execute(self):
        if not self.skeleton_loaded:
            return
        
        # Clear the pixmap
        self.path_pixmap = QtGui.QPixmap(self.image_label.width(), self.image_label.height())
        self.path_pixmap.fill(Qt.black)

        self.image_label.setPixmap(self.path_pixmap)

        self.path_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.draw_next_point)
        self.timer.timeout.connect(self.send_positions)

        interval_ms = int(self.interval_input.text())
        self.timer.start(interval_ms)

    def send_positions(self):
        point = self.scaled_path[self.path_index]

        print(f"Sending coordinates: x - {point[0]:.4f}, y - {point[1]:.4f}, z - {self.board_z:.4f}, at time t = {get_time():.6f}")
        
        # Might need to divide all dimensions by 100
        msg_packed = repr([[point[0] / 100, point[1] / 100, self.board_z / 100]]).encode('utf-8')
        self.redis.publish("positions", msg_packed)

    def draw_next_point(self):
        if (self.path_index + 1) >= len(self.scaled_path):
            self.timer.stop()
            print("Finished drawing path/sending positions.")
            return

        point = self.scaled_path[self.path_index]
        # print(f"Drawing point {self.path_index}: x - {point[0]:.4f}, y - {point[1]:.4f}")
        self.draw_pixel(point[0], point[1])
        self.path_index += 1

    def draw_pixel(self, x, y):
        # Original image dimensions
        img_h, img_w = self.img.shape
        label_w = self.image_label.width()
        label_h = self.image_label.height()

        # Reconvert back to image pixel
        x = x / self.side_length * img_w;
        y = y / self.side_length * img_h;

        # Scale coordinates to GUI 
        x_disp = int(x * label_w / img_w)
        y_disp = int(y * label_h / img_h)

        painter = QtGui.QPainter(self.path_pixmap)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawPoint(x_disp, y_disp)
        painter.end()

        self.image_label.setPixmap(self.path_pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())