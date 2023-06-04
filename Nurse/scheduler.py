import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QInputDialog, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scheduler = RoomScheduler()
    scheduler.showFullScreen()
    sys.exit(app.exec_())
