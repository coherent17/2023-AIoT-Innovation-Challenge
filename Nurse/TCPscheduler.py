#v1-1 update the basic logic behind the program
import sys
import configparser
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QLabel, QSplashScreen,QInputDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap,QPainter
import socket
import time
from emerdencyTable import emergency_dictionary
import threading


# Add a SplashPage class to display the splash screen
class SplashPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlizaRing")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #333333;")
        self.layout = QVBoxLayout()
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("icon.png"))
        self.layout.addWidget(self.logo, alignment=Qt.AlignCenter)
        self.setLayout(self.layout)

    def showEvent(self, event):
        QTimer.singleShot(2000, self.close)

class RoomScheduler(QWidget):
    def __init__(self,name):
        
        #Basic layout
        super().__init__()
        self.setWindowTitle("聽~紅鈴的聲音")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #efefef;")
        self.layout = QVBoxLayout()
        
        #Add buttom for switching event list
        #initially, we print the unfinished event
        self.main_button = QPushButton("切換為 已完成事件")
        self.main_button.setStyleSheet("QPushButton { background-color: #555555; color: white; padding: 10px; border-radius: 5px; }"
                                   "QPushButton:hover { background-color: #777777; }"
                                   "QPushButton:pressed { background-color: #333333; }")
        self.main_button.clicked.connect(self.swich_event_list)
        self.layout.addWidget(self.main_button, alignment=Qt.AlignLeft)

        #Load the table
        self.set_unfinished_event()
        self.set_finished_event()
        self.table = QTableWidget() 
        self.set_table()#set the config of table

        ##Add config button
        self.name = name
        cfg_button = QPushButton("設定姓名")
        cfg_button.clicked.connect(self.setup_name)
        cfg_button.setStyleSheet("QPushButton { background-color: #555555; color: white; padding: 10px; border-radius: 5px; }"
                                   "QPushButton:hover { background-color: #777777; }"
                                   "QPushButton:pressed { background-color: #333333; }")
        self.layout.addWidget(cfg_button, alignment=Qt.AlignLeft)

        # Add Exit Button
        exit_button = QPushButton("退出")
        exit_button.clicked.connect(self.exit_application)
        exit_button.setStyleSheet("QPushButton { background-color: #555555; color: white; padding: 10px; border-radius: 5px; }"
                                   "QPushButton:hover { background-color: #777777; }"
                                   "QPushButton:pressed { background-color: #333333; }")
        self.layout.addWidget(exit_button, alignment=Qt.AlignRight)
        
        # Start TCP server
        self.tcp_server = TCPServer()
        self.tcp_server.task_received.connect(self.handle_received_task)
        self.tcp_server.start()
    def set_unfinished_event(self):
        
        #initialize and sort the unfinished event list for demo
        #the unfinished event will be sorted by emergency
        self.unfinished_event = [
            {'number': '101房', 'event': '什麼時候出院', 'emergency': 4,'timestamp':None,"executer":None,"status":'unexecuted'},
            {'number': '102房', 'event': '打胰島素', 'emergency': 2,'timestamp':None,"executer":None,"status":'unexecuted'},
            {'number': '103房', 'event': '衛生紙', 'emergency': 4,'timestamp':None,"executer":None,"status":'unexecuted'},
            {'number': '104房', 'event': '很喘', 'emergency': 1,'timestamp':None,"executer":None,"status":'unexecuted'},
            {'number': '105房', 'event': '尿袋', 'emergency': 3,'timestamp':None,"executer":None,"status":'unexecuted'},
        ]
        self.unfinished_event = sorted(self.unfinished_event, key=lambda x: x['emergency'])
        
    def set_finished_event(self):
        #initialize and sort the finished event list for demo
        #the unfinished event will be sorted by timestamp
        self.finished_event = [
            {'number': '106房', 'event': '飯還沒來', 'emergency': 4,'timestamp':time.time()-10000,"executer":"柯祈因","status":'executed'},
        ]
        
    def set_table(self):#setting layout of the table to be printed in the middle of the surface
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.table.setColumnCount(5) 
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #222222; color: white; }")
        self.table.horizontalHeader().setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.table.setHorizontalHeaderLabels(["床號", "事件種類", "緊急程度", "處理情形", "操作"])
        self.layout.addWidget(self.table)
        
        self.setLayout(self.layout)
        self.adjustSize()
        self.setFixedSize(self.size())
    
        self.set_printed_event_list(self.unfinished_event)
        
    def handle_received_task(self, room, event, emergency):
        # Create a new row in the table for the received task
        new_row = self.table.rowCount()
        self.unfinished_event.append({'number': str(room)+'房', 'event': event, 'emergency': int(emergency),'timestamp':None,"executer":None,"status":'unexecuted'})
        self.unfinished_event = sorted(self.unfinished_event, key=lambda x: x['emergency'])
        
        
        if self.main_button.text() == "切換為 已完成事件":#update the event in real time
            self.set_printed_event_list(self.unfinished_event)
        # Find the index to insert the new task based on emergency level

    def swich_event_list(self):
        if self.main_button.text()=="切換為 已完成事件":
            self.main_button.setText("切換為 紅鈴動態")
            self.set_printed_event_list(self.finished_event)
        else: #"切換為 紅鈴動態"
            self.main_button.setText("切換為 已完成事件")
            self.set_printed_event_list(self.unfinished_event)
    
    def set_printed_event_list(self,event_list:list):
        #event_list is always an sorted array
        self.table.setRowCount(0)
        self.table.setRowCount(len(event_list))
        for i, event in enumerate(event_list):
            room_item = QTableWidgetItem(event['number'])
            room_item.setForeground(QColor(0, 0, 0)) #1st column
            event_item = QTableWidgetItem(event['event'])
            event_item.setForeground(QColor(0, 0, 0))#2nd column
            emergency_item = QTableWidgetItem(str(event['emergency']))
            emergency_item.setForeground(QColor(0, 0, 0))#3rd column
            
            state_item = QTableWidgetItem("未執行")
            
            action = QPushButton("我要處理")
            action.clicked.connect(self.execute_task)
            action.setProperty("index", i)
            action.setStyleSheet("QPushButton { background-color: green; color: white; padding: 6px 10px; border-radius: 5px; }"
                                         "QPushButton:hover { background-color: #777777; }"
                                         "QPushButton:pressed { background-color: #333333; }")
            if event['status']=='executing':
                state_item = QTableWidgetItem(event['executer']+' 執行中')
                action.setText("結束執行")
                action.setStyleSheet("QPushButton { background-color: #ff3333; color: white; padding: 6px 10px; border-radius: 5px; }"
                                         "QPushButton:hover { background-color: #777777; }"
                                         "QPushButton:pressed { background-color: #333333; }")
            elif event['status']=='executed':
                state_item = QTableWidgetItem(event['executer']+' 已完成')
                action = QTableWidgetItem('已完成事件') #the finished tasks cannot be further delete or other action
                
                #action.setStyleSheet("background-color: green")
            
            state_item.setForeground(QColor(0, 0, 0))

            self.table.setItem(i, 0, room_item)
            self.table.setItem(i, 1, event_item)
            self.table.setItem(i, 2, emergency_item)
            self.table.setItem(i, 3, state_item)
            if event['status']=='executed':
                self.table.setItem(i, 4, action)
            else:
                self.table.setCellWidget(i, 4, action) 

        # Expand rows and columns
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setMinimumSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def execute_task(self):#**need modification
        button = self.sender()
        index = button.property("index")  # Get the stored row index
        if index is not None:     
            
            if self.unfinished_event[index]['status'] == "unexecuted": #change the state of specific event
                reply = QMessageBox.question(self, "確認", "確定處理此事件?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.unfinished_event[index]['executer'] = self.name
                    self.unfinished_event[index]['status'] = 'executing'
                    
            elif self.unfinished_event[index]['executer'] == self.name:
                reply = QMessageBox.question(self, "確認", "確定刪除此事件?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.unfinished_event[index]['status'] = 'executed'
                    self.unfinished_event[index]['timestamp'] = time.time()
                    event = self.unfinished_event[index]
                    self.unfinished_event.pop(index)
                    self.finished_event.insert(0,event)
                    
            else: #the executer is not user
                QMessageBox.information(self,"警告","無法刪除他人執行的事件!!")
        self.set_printed_event_list(self.unfinished_event)

    def exit_application(self):
        QApplication.quit()

    def showEvent(self, event):
        self.activateWindow()
    
    def setup_name(self):#**need modification
        name, ok = QInputDialog.getText(self, "設定姓名", "請輸入新名字")
        if ok:
            #update the executer of all events
            for index,_ in enumerate(self.unfinished_event):
                if self.unfinished_event[index]['executer'] == self.name:
                    self.unfinished_event[index]['executer'] = name
            for index,event in enumerate(self.finished_event):
                if self.finished_event[index]['executer'] == self.name:
                    self.finished_event[index]['executer'] = name   
                
            #modify the config file
            self.name = name
            file = open('name.cfg','w')
            file.write(name)
            file.close()
            
            if self.main_button.text()=="切換為 已完成事件":
                self.set_printed_event_list(self.unfinished_event)
            else: #"切換為 紅鈴動態"
                self.set_printed_event_list(self.finished_event)        


class KeyboardThread(threading.Thread):

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def run(self):
        while True:
            self.input_cbk(input()) #waits to get input + Return

class TCPServer(QThread):
    task_received = pyqtSignal(str, str, str)

    def run(self):
        #host = '172.20.10.4'                               # IP for Raspberry Pi
        host = socket.gethostbyname(socket.gethostname())  # IP address of the TCP server
        port = 50007                                       # Arbitrary non-privileged port
        RECV_BUFF_SIZE = 4096                              # Receive buffer size
        DEFAULT_KEEP_ALIVE = 1                             # TCP Keep Alive: 1 - Enable, 0 - Disable

        # Create a TCP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set TCP Keepalive parameters
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, DEFAULT_KEEP_ALIVE)

        # variable to identify if there is an active client connection
        is_client_connected = False

        try:
            # Bind the socket to a specific address and port
            server_socket.bind((host, port))
            server_socket.listen(1)
        except socket.error as msg:
                print("ERROR: ", msg)
                server_socket.close()
                server_socket = None
        
        if server_socket is None:
            sys.exit(1)
        
        while True:
            try:
                is_client_connected = False
                print("Listening on: IPv4 Address: %s Port: %d"%(host, port))
                conn, addr = server_socket.accept()
                is_client_connected = True
            
            except KeyboardInterrupt:
                print("Closing Connection")
                server_socket.close()
                server_socket = None
                sys.exit(1)


            print('Incoming connection accepted: ', addr)

            while True:
                try:
                    
                    data = conn.recv(RECV_BUFF_SIZE)
                    if not data: break
                    print("Acknowledgement from TCP Client:", data.decode('utf-8'))
                    print("")
                    self.task_received.emit('601', data.decode('utf-8'), str(emergency_dictionary[data.decode('utf-8')]))
                    
                except socket.error:
                    print("Timeout Error! TCP Client connection closed")
                    break
                    
                except KeyboardInterrupt:
                    print("Closing Connection")
                    server_socket.close()
                    server_socket = None
                    sys.exit(1)    

if __name__ == "__main__":
    
    #Read cfg file and get the name
    cfg_file = open('name.cfg','r')
    name = cfg_file.readline()
    cfg_file.close()
    name.replace('\n','')
    
    app = QApplication(sys.argv)

    # Create and show the splash screen
    splash = QSplashScreen(QPixmap("icon.png"))
    splash.show()

    # Create the RoomScheduler widget
    window = RoomScheduler(name = name)

    # Close the splash screen and show the RoomScheduler after a delay
    QTimer.singleShot(2000, splash.close)
    QTimer.singleShot(2000, window.showMaximized)

    sys.exit(app.exec_())