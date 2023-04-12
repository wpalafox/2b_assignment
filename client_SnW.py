# Import necessary libraries
import socket
import os
import timer
import udt
import packet

def main():
    # Define buffer size and request server IP address and port number
    BUFFER_SIZE = 999
    SERVER_HOST = input("Enter the server IP address: ")
    SERVER_PORT = int(input("Enter the server port number: "))

    # Create a TCP socket and connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    # Send a handshake message to the server to start the file transfer
    client_socket.send(b"START_TRANSFER")

    # Receive the file size and decode it using the separator '|'
    file_size = int(client_socket.recv(BUFFER_SIZE).decode().split('|')[0])

    # If file size is zero, it means the file was not found on the server
    if file_size == 0:
        print("File not found on the server.")
        client_socket.close()
        return

    # Set the file extension according to the type of file being transferred (update as needed)
    file_extension = ".pdf"
    file_path = os.path.join(os.getcwd(), "received_file" + file_extension)

    # Open the file to write the received data
    with open(file_path, "wb") as file:
        bytes_received = 0
        expected_seq_number = 0

        # Keep receiving segments until the whole file is received
        while bytes_received < file_size:
            # Receive the data and extract the packet
            data = udt.recv(client_socket)
            packet_rec = packet.extract(data[0])
            segment_data = packet_rec[1]
            received_seq_number = packet_rec[0]

            # Check if the received sequence number matches the expected sequence number
            if received_seq_number == expected_seq_number:
                bytes_received += len(segment_data)
                file.write(segment_data)
                print(f"Received segment with sequence number {received_seq_number}")

                # Send ACK for the received sequence number
                ack = received_seq_number.to_bytes(1, byteorder='little')
                client_socket.send(ack)
                print(f"Sent ACK for sequence number {received_seq_number}")

                # Toggle the expected sequence number
                expected_seq_number ^= 1
            else:
                print(f"Received out-of-order segment with sequence number {received_seq_number}")

    print(f"File has been received and saved as 'received_file{file_extension}'.")
    client_socket.close()

if __name__ == "__main__":
    main()
