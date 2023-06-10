import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QLabel
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
        self.table.setColumnCount(5)  # Update column count
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #222222; color: white; }")
        self.table.horizontalHeader().setFont(QFont("Arial", 12, QFont.Bold))
        self.table.setHorizontalHeaderLabels(["Room", "Event", "Emergency", "State", "Action"])  # Remove "Select"
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
            {'number': 'Room 105', 'event': 'Allergic Reaction', 'emergency': 3},
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
            state_item = QTableWidgetItem("Not finished")
            state_item.setForeground(QColor(200, 200, 200))

            action_button = QPushButton("Take Task")
            action_button.clicked.connect(self.execute_task)
            action_button.setProperty("index", i)  # Set custom property to store the row index
            action_button.setStyleSheet("QPushButton { background-color: green; color: white; padding: 6px 10px; border-radius: 5px; }"
                                         "QPushButton:hover { background-color: #777777; }"
                                         "QPushButton:pressed { background-color: #333333; }")

            self.table.setItem(i, 0, room_item)
            self.table.setItem(i, 1, event_item)
            self.table.setItem(i, 2, emergency_item)
            self.table.setItem(i, 3, state_item)
            self.table.setCellWidget(i, 4, action_button)  # Adjust column index

        # Expand rows and columns
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setMinimumSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def execute_task(self):
        button = self.sender()
        index = button.property("index")  # Get the stored row index
        if index is not None:
            state_item = self.table.item(index, 3)
            state = state_item.text()
            if state == "Not finished":
                reply = QMessageBox.question(self, "Confirmation", "Do you want to take this task?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    state_item.setText("Executed")
                    button.setText("Delete Task")
                    button.setStyleSheet("QPushButton { background-color: #ff3333; color: white; padding: 6px 10px; border-radius: 5px; }"
                                         "QPushButton:hover { background-color: #ff5555; }"
                                         "QPushButton:pressed { background-color: #cc2222; }")
            elif state == "Executed":
                reply = QMessageBox.question(self, "Confirmation", "Do you want to delete this task?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.table.removeRow(index)
                    # Update the stored row index in action buttons
                    for row in range(self.table.rowCount()):
                        action_button = self.table.cellWidget(row, 4)  # Adjust column index
                        action_button.setProperty("index", row)

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
        state_item = QTableWidgetItem("Not finished")
        state_item.setForeground(QColor(200, 200, 200))

        action_button = QPushButton("Take Task")
        action_button.clicked.connect(self.execute_task)
        action_button.setProperty("index", new_row)  # Set custom property to store the row index
        action_button.setStyleSheet("QPushButton { background-color: #555555; color: white; padding: 6px 10px; border-radius: 5px; }"
                                    "QPushButton:hover { background-color: #777777; }"
                                    "QPushButton:pressed { background-color: #333333; }")

        self.table.setItem(new_row, 0, room_item)
        self.table.setItem(new_row, 1, event_item)
        self.table.setItem(new_row, 2, emergency_item)
        self.table.setItem(new_row, 3, state_item)
        self.table.setCellWidget(new_row, 4, action_button)  # Adjust column index

        # Update the stored row index in action buttons
        for row in range(self.table.rowCount()):
            action_button = self.table.cellWidget(row, 4)  # Adjust column index
            action_button.setProperty("index", row)

        # Highlight the new row
        for column in range(self.table.columnCount()):
            item = self.table.item(new_row, column)

    def showEvent(self, event):
        self.activateWindow()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RoomScheduler()
    window.showMaximized()
    sys.exit(app.exec_())
    