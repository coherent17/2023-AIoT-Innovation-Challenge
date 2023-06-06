import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QCheckBox, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap
import socket

class RoomScheduler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Room Scheduler")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #333333;")
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #222222; color: white; }")
        self.table.horizontalHeader().setFont(QFont("Arial", 12, QFont.Bold))
        self.table.setHorizontalHeaderLabels(["Room", "Event", "Emergency", "Select", "Delete"])
        self.layout.addWidget(self.table)
        self.load_rooms()
        self.setLayout(self.layout)
        self.adjustSize()
        self.setFixedSize(self.size())

        # Add Exit Button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_application)
        exit_button.setStyleSheet("QPushButton { background-color: #555555; color: white; padding: 10px; border-radius: 5px; }"
                                   "QPushButton:hover { background-color: #777777; }"
                                   "QPushButton:pressed { background-color: #333333; }")
        self.layout.addWidget(exit_button, alignment=Qt.AlignRight)

        # Start TCP server
        self.tcp_server = TCPServer()
        self.tcp_server.task_received.connect(self.handle_received_task)
        self.tcp_server.start()

    def load_rooms(self):
        # Simulated room data
        rooms = [
            {'number': 'Room 101', 'event': 'Heart Attack', 'emergency': 4},
            {'number': 'Room 102', 'event': 'Fractured Arm', 'emergency': 2},
            {'number': 'Room 103', 'event': 'Stroke', 'emergency': 4},
            {'number': 'Room 104', 'event': 'Fever', 'emergency': 1},
            {'number': 'Room 105', 'event': 'Appendicitis', 'emergency': 4},
            {'number': 'Room 106', 'event': 'Headache', 'emergency': 2},
            {'number': 'Room 107', 'event': 'Influenza', 'emergency': 1},
            {'number': 'Room 108', 'event': 'Broken Leg', 'emergency': 3},
            {'number': 'Room 109', 'event': 'Chest Pain', 'emergency': 4},
            {'number': 'Room 110', 'event': 'Allergic Reaction', 'emergency': 3},
        ]

        sorted_rooms = sorted(rooms, key=lambda x: x['emergency'], reverse=True)  # Sort by emergency state in descending order

        self.table.setRowCount(len(sorted_rooms))
        for i, room in enumerate(sorted_rooms):
            room_item = QTableWidgetItem(room['number'])
            room_item.setForeground(QColor(200, 200, 200))
            event_item = QTableWidgetItem(room['event'])
            event_item.setForeground(QColor(200, 200, 200))
            emergency_item = QTableWidgetItem(str(room['emergency']))
            emergency_item.setForeground(QColor(200, 200, 200))

            select_checkbox = QCheckBox()
            select_checkbox.setStyleSheet("QCheckBox { color: white; }")
            select_checkbox.setProperty("index", i)  # Set custom property to store the row index

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(self.delete_event)
            delete_button.setProperty("index", i)  # Set custom property to store the row index
            delete_button.setStyleSheet("QPushButton { background-color: #ff3333; color: white; padding: 6px 10px; border-radius: 5px; }"
                                         "QPushButton:hover { background-color: #ff5555; }"
                                         "QPushButton:pressed { background-color: #cc2222; }")

            self.table.setItem(i, 0, room_item)
            self.table.setItem(i, 1, event_item)
            self.table.setItem(i, 2, emergency_item)
            self.table.setCellWidget(i, 3, select_checkbox)
            self.table.setCellWidget(i, 4, delete_button)

        # Expand rows and columns
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setMinimumSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def delete_event(self):
        button = self.sender()
        index = button.property("index")  # Get the stored row index
        if index is not None:
            reply = QMessageBox.question(self, "Confirmation", "Are you sure you want to delete this task?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.table.removeRow(index)
                # Update the stored row index in delete buttons
                for row in range(self.table.rowCount()):
                    delete_button = self.table.cellWidget(row, 4)
                    delete_button.setProperty("index", row)

    def exit_application(self):
        QApplication.quit()

    def handle_received_task(self, room, event, emergency):
        # Create a new row in the table for the received task
        new_row = self.table.rowCount()

        # Find the index to insert the new task based on emergency level
        for row in range(self.table.rowCount()):
            current_emergency_item = self.table.item(row, 2)
            current_emergency = int(current_emergency_item.text())
            if int(emergency) > current_emergency:
                new_row = row
                break

        self.table.insertRow(new_row)

        room_item = QTableWidgetItem(room)
        room_item.setForeground(QColor(200, 200, 200))
        event_item = QTableWidgetItem(event)
        event_item.setForeground(QColor(200, 200, 200))
        emergency_item = QTableWidgetItem(emergency)
        emergency_item.setForeground(QColor(200, 200, 200))

        select_checkbox = QCheckBox()
        select_checkbox.setStyleSheet("QCheckBox { color: white; }")
        select_checkbox.setProperty("index", new_row)  # Set custom property to store the row index

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_event)
        delete_button.setProperty("index", new_row)  # Set custom property to store the row index
        delete_button.setStyleSheet("QPushButton { background-color: #ff3333; color: white; padding: 6px 10px; border-radius: 5px; }"
                                    "QPushButton:hover { background-color: #ff5555; }"
                                    "QPushButton:pressed { background-color: #cc2222; }")

        self.table.setItem(new_row, 0, room_item)
        self.table.setItem(new_row, 1, event_item)
        self.table.setItem(new_row, 2, emergency_item)
        self.table.setCellWidget(new_row, 3, select_checkbox)
        self.table.setCellWidget(new_row, 4, delete_button)


class WelcomePage(QWidget):
    def __init__(self, scheduler):
        super().__init__()
        self.setWindowTitle("Welcome Page")
        self.setWindowIcon(QIcon("icon.png"))
        self.setStyleSheet("background-color: #333333;")

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # Add Icon Label
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap("icon.png"))
        self.layout.addWidget(icon_label)

        # Add Title Label
        title_label = QLabel("Room Scheduler")
        title_label.setStyleSheet("QLabel { color: white; font-size: 36px; font-weight: bold; }")
        self.layout.addWidget(title_label)

        # Add Subtitle Label
        subtitle_label = QLabel("Efficient Room Management for Nurses")
        subtitle_label.setStyleSheet("QLabel { color: #999999; font-size: 18px; }")
        self.layout.addWidget(subtitle_label)

        # Add Instructions Label
        instructions_label = QLabel("Click the button below to access the scheduler.")
        instructions_label.setStyleSheet("QLabel { color: white; font-size: 24px; }")
        self.layout.addWidget(instructions_label)

        # Add Enter Button
        enter_button = QPushButton("Enter Scheduler")
        enter_button.clicked.connect(scheduler.showMaximized)
        enter_button.setStyleSheet("QPushButton { background-color: #555555; color: white; padding: 20px; border-radius: 10px; font-size: 24px; }"
                                   "QPushButton:hover { background-color: #777777; }"
                                   "QPushButton:pressed { background-color: #333333; }")
        self.layout.addWidget(enter_button)

        self.showFullScreen()

    def enter_scheduler(self):
        scheduler = RoomScheduler()
        scheduler.showMaximized()
        self.close()

class TCPServer(QThread):
    task_received = pyqtSignal(str, str, str)

    def run(self):
        SERVER_IP = 'localhost'
        SERVER_PORT = 12345

        # Create a TCP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Bind the socket to a specific address and port
            server_socket.bind((SERVER_IP, SERVER_PORT))

            # Listen for incoming connections
            server_socket.listen(1)
            print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

            while True:
                # Accept a client connection
                client_socket, client_address = server_socket.accept()
                print(f"Connection established with {client_address[0]}:{client_address[1]}")

                # Receive data from the client
                data = client_socket.recv(1024).decode()

                # Process the received data
                if data:
                    room, event, emergency = data.split(',')
                    self.task_received.emit(room, event, emergency)

                # Close the client socket
                client_socket.close()

        except OSError as e:
            print(f"Error: {e}")
        finally:
            # Close the server socket
            server_socket.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scheduler = RoomScheduler()
    welcome_page = WelcomePage(scheduler)
    welcome_page.showMaximized()
    sys.exit(app.exec_())