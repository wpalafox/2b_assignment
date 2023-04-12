import socket
import os
from timer import Timer
import time

import udt
import packet
import threading
from collections import deque
from select import select

# Set server host, port, buffer size, and default file path
SERVER_HOST = "0.0.0.0"
SERVER_PORT = ""
BUFFER_SIZE = 999  # Save 1 byte for sequence number
DEFAULT_FILE_PATH = "default_file.pdf"
ACK_TIMEOUT = 2  # Timeout for waiting for ACKs, in seconds
WINDOW_SIZE = 4  # Set the window size here (e.g., 4, 8, 12, 16)

# Function to send a file using Go-Back-N protocol
def send_gbn(sender_socket, file_path):
    # Helper function to send a packet with a given sequence number
    def send_packet(packet_data, seq_number, sock, address):
        dataPacket = packet.make(seq_number, packet_data)
        udt.send(dataPacket, sock, address)

    # Helper function to receive an ACK and check if it matches the expected sequence number
    def recv_ack(sock, expected_seq_number):
        try:
            ack = sock.recv(1)
            received_seq_number = int.from_bytes(ack, byteorder='little')
            return received_seq_number == expected_seq_number
        except socket.timeout:
            return False

    # Check if the file exists, and if so, send the file using GBN
    if os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)
        sender_socket.send((f"{file_size}|".encode()))

        with open(file_path, "rb") as file:
            bytes_read = file.read(BUFFER_SIZE)
            seq_number = 0
            window = deque()
            base = 0
            next_seq_number = 0

            # Continue sending packets while there are packets in the window or bytes left to read from the file
            while bytes_read or window:
                # Fill the window and send packets while the window is not full and there are bytes left to read from the file
                while len(window) < WINDOW_SIZE and bytes_read:
                    window.append((seq_number, bytes_read))
                    send_packet(bytes_read, seq_number, sender_socket, (SERVER_HOST, SERVER_PORT))
                    print(f"Sent segment with sequence number {seq_number}")
                    bytes_read = file.read(BUFFER_SIZE)
                    seq_number = (seq_number + 1) % (2 * WINDOW_SIZE)
                    next_seq_number = seq_number

                # Set a timeout and wait for an ACK
                sender_socket.settimeout(ACK_TIMEOUT)
                ack_received = recv_ack(sender_socket, base % (2 * WINDOW_SIZE))

                # If an ACK is received, update the base and remove the acknowledged packet from the window
                if ack_received:
                    print(f"Received ACK for sequence number {base % (2 * WINDOW_SIZE)}")
                    base += 1
                    window.popleft()
                else:
                    print(f"ACK timeout for sequence number {base % (2 * WINDOW_SIZE)}")
                    # Retransmit all packets in the window
                    for seq_number, packet_data in window:
                        send_packet(packet_data, seq_number, sender_socket, (SERVER_HOST, SERVER_PORT))

        print(f"File {file_path} has been sent.")
    else:
        sender_socket.send(b"0")
        print("Default file not found.")

def main():
    

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print(f"[*] Listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"[+] {client_address} connected.")
        # Wait for the handshake message from the client
        handshake_msg = client_socket.recv(BUFFER_SIZE).decode()
        
        
        if protocol == "SnW":
            send_snw(client_socket, DEFAULT_FILE_PATH)
        elif protocol == "GBN":
            send_gbn(client_socket, DEFAULT_FILE_PATH)  
        else:
            print("Protocol not supported.")


        client_socket.close()

if __name__ == "__main__":
    SERVER_PORT = int(input("Enter the port number to listen on: "))
    protocol = input("Enter the protocol to use (SnW or GBN): ")
    main()
