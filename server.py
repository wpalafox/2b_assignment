import socket
import os
import time
import timer
import udt
import packet


SERVER_HOST = "0.0.0.0"
SERVER_PORT = ""
BUFFER_SIZE = 999 #Save 1 byte for sequence number
DEFAULT_FILE_PATH = "default_file.pdf"
ACK_TIMEOUT = 2  # Timeout for waiting for ACKs, in seconds


def send_snw(sender_socket, file_path):
    if os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)
        sender_socket.send((f"{file_size}|".encode()))

        with open(file_path, "rb") as file:
            seq_number = 0
            bytes_read = file.read(BUFFER_SIZE) 
            while bytes_read:
                # Add the sequence number to the data segment
                #data = bytes([seq_number]) + bytes_read
                #create a packet 
                dataPacket = packet.make(seq_number, bytes_read)

                # Send the segment and wait for ACK
                ack_received = False
                while not ack_received:
                    #sender_socket.send(data)
                    #send it 
                    client_address = (SERVER_HOST, SERVER_PORT)
                    udt.send(dataPacket, sender_socket, client_address)
                    print(f"Sent segment with sequence number {seq_number}")

                    # Wait for ACK with a timeout
                    sender_socket.settimeout(ACK_TIMEOUT)
                    try:
                        ack = sender_socket.recv(1)
                        received_seq_number = int.from_bytes(ack, byteorder='little')

                        # Check if the received ACK matches the expected sequence number
                        if received_seq_number == seq_number:
                            ack_received = True
                            print(f"Received ACK for sequence number {seq_number}")
                        else:
                            print(f"Received incorrect ACK for sequence number {received_seq_number}")
                    except socket.timeout:
                        print(f"ACK timeout for sequence number {seq_number}")

                # Move to the next segment and toggle the sequence number
                bytes_read = file.read(BUFFER_SIZE)
                seq_number ^= 1  # Toggle the sequence number between 0 and 1

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
        else:
            print("Protocol not supported.")

        client_socket.close()

if __name__ == "__main__":
    SERVER_PORT = int(input("Enter the port number to listen on: "))
    protocol = input("Enter the protocol to use (SnW or GBN): ")
    main()
