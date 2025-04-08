"""
Control position of bead using keyboard control.
"""
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt
import sys
import redis
import time

sonic_surface = False

def get_time():
    return time.time_ns() * 1e-9

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.defaultSpeed = 100 #cm/s
        self.defaultUpdateRate = 800 #Hz

        self.setGeometry(100, 100, 600, 100)  # Set window size (I made the window smaller - Howard)
        self.setWindowTitle('Arrow Key Motion Translation')
        self.side_length = 10.0 if sonic_surface else 16.8
        self.step_size = 0.1 # Can be controlled with Q and W
        self.step_size_adj = 0.005
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_z = 0
        # start at center
        self.board_x = self.side_length / 2  # cm
        self.board_y = self.side_length / 2
        self.board_z = 0.5
        self.tracking = False
        # add label to show tracking status
        self.label = QLabel(self)
        self.label.move(10, 10)
        # set size to be bigger
        self.label.resize(600, 50)
        self.update_label()
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.redis.publish("positions", repr([[self.board_x / 100, self.board_y / 100, self.board_z / 100]]).encode('utf-8'))  # initial position
        self.last_sent = get_time()
        if sonic_surface:
            self.wait_before_sending = 0.01  # serial port limits us to 100 Hz?
        self.num_sends = 0

    def update_label(self):
        self.label.setText(f"Tracking (T): {'ON' if self.tracking else 'OFF'}, x={self.board_x:.3f}, y={self.board_y:.3f}, z={self.board_z:.3f}, step size={self.step_size:.3f}")

    def send_positions(self):
        # Send board position to Redis
        curr_time = get_time()
        if sonic_surface: # skip sending if we're on the sonic surface and we're sending too fast
            if curr_time - self.last_sent < self.wait_before_sending:
                return
        # dist = 0.001
        # diffs = [[0, dist, 0], [0, -dist, 0], [dist, 0, 0], [-dist, 0, 0]]
        base_position = [self.board_x / 100, self.board_y / 100, self.board_z / 100]
        # positions = [list(map(sum, zip(base_position, diff))) for diff in diffs]
        positions = [base_position] # There's quite a bit of floating point error; is that a big deal? - Howard
        pos_str = [f"{a:.4f}" for a in positions[0]]
        #print(f"Sending msg {self.num_sends} {pos_str}")
        self.num_sends += 1

        msg_packed = repr(positions).encode('utf-8')
        self.redis.publish("positions", msg_packed)
        self.last_sent = curr_time

    def moveOffset(self, dx, dy, speed = None, updateRate = None):
        if speed == None:
            speed = self.defaultSpeed
        if updateRate == None:
            updateRate = self.defaultUpdateRate

        distance = (dx**2+dy**2)**(1/2)
        timestep = 1/updateRate
        xStep = (speed/updateRate)*dx/distance
        yStep = (speed/updateRate)*dy/distance
        numSteps = (distance/speed)*updateRate

        lastTime = time.time()
        stepCounter = 0
        while stepCounter < numSteps:
            if time.time() - lastTime > timestep:
                self.board_x += xStep
                self.board_y += yStep
                self.send_positions()
                stepCounter += 1
                lastTime = time.time()

    def schmoovement(self, xdist, ydist, wait, speed = None, updateRate = None):
        self.moveOffset(xdist/2,ydist/2, speed = speed, updateRate = updateRate)
        time.sleep(wait)
        self.moveOffset(-xdist,-ydist, speed = speed, updateRate = updateRate)
        time.sleep(wait)
        self.moveOffset(xdist,ydist, speed = speed, updateRate = updateRate)
        time.sleep(wait)
        self.moveOffset(-xdist/2,-ydist/2, speed = speed, updateRate = updateRate)
        time.sleep(wait)

    def test(self):
        dist = 4
        distStep = 2

        wait = 0.5

        while wait >= 0:
            for i in range(2):
                self.schmoovement(dist,dist,wait)
            wait -= 0.05
            time.sleep(1.5)
        

    # keyboard event, turn tracking on and off with T key
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up:
            self.board_y += self.step_size
        elif key == Qt.Key_Down:
            self.board_y -= self.step_size
        elif key == Qt.Key_Left:
            self.board_x -= self.step_size
        elif key == Qt.Key_Right:
            self.board_x += self.step_size
        elif key == Qt.Key_O: # Added code for the z direction but it doesn't seem to do what I want - Howard
            self.board_z -= self.step_size
        elif key == Qt.Key_P:
            self.board_z += self.step_size
        elif key == Qt.Key_T:
            self.tracking = not self.tracking # Does tracking even do anything? - Howard
        elif key == Qt.Key_Q:
            self.step_size -= self.step_size_adj
        elif key == Qt.Key_W:
            self.step_size += self.step_size_adj
        elif key == Qt.Key_Z:
            self.moveBackForth()
        elif key == Qt.Key_X:
            self.test()
        
        # Clamp step size
        self.step_size = max(0, self.step_size)

        self.board_x = max(0, min(self.side_length, self.board_x))  # Ensure x coordinate stays within 0cm-10cm range
        self.board_y = max(0, min(self.side_length, self.board_y))  # Ensure y coordinate stays within 0cm-10cm range
        self.board_z = max(0, self.board_z) # Clamp z to positive

        self.update_label()
        self.send_positions()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())
