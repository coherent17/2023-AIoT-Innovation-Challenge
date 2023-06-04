import socket

SERVER_IP = 'localhost'
SERVER_PORT = 12345

room = 'Room 311'
event = 'Eye Attack'
emergency = '1'

# Create a TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the server
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

    # Construct the task message
    task_message = f"{room},{event},{emergency}"

    # Send the task message to the server
    client_socket.sendall(task_message.encode())
    print("Task sent to the server")

finally:
    # Close the client socket
    client_socket.close()
