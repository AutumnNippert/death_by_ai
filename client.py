import socket
import threading
import sys
import requests
import os
import platform

OS = platform.system()

IP = sys.argv[1]
disable_sending = False

def watch_send_messages(sock):
    while True:
        global disable_sending
        if disable_sending:
            continue
        message = input('>>> ')
        sock.sendall(message.encode())

def watch_receive_messages(sock):
    global disable_sending
    while True:
        data = sock.recv(1024)
        if not data:
            break
        
        if "disable_sending" in data.decode():
            disable_sending = True
            # print("Sending messages disabled")
            continue
        elif "enable_sending" in data.decode() :
            disable_sending = False
            # print("Sending messages enabled")
            continue
        # flush the buffer
        sys.stdout.flush()
        print(f'{data.decode()}')
        tts_dectalk(data.decode())


def main():
    # Connect to the server
    server_address = (IP, 1337)
    
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        
        # Start a thread to watch for messages from the server
        receive_thread = threading.Thread(target=watch_receive_messages, args=(sock,))
        receive_thread.start()

        # Start a thread to watch for messages to send to the server
        send_thread = threading.Thread(target=watch_send_messages, args=(sock,))
        send_thread.start()

        # Wait for the threads to finish
        receive_thread.join()
        send_thread.join()
            
    except ConnectionRefusedError:
        print("Could not connect to the server. Is it running?")
    finally:
        print("Closing connection.")
        sock.close()
        
def tts_dectalk(text, filename="output.mp3", type="dectalk"):
    if type == "dectalk":
        url = 'https://tts.cyzon.us/tts?text='
        url += text
        #This url when doing a get request will return a wav file
        response = requests.get(url)
        filename = filename
        with open(filename, 'wb') as f:
            f.write(response.content)
    
    # if type == "gTTS":
    #     obj = gTTS(text=text, lang='en', tld='com.au', slow=False)
    #     filename = "res/" + filename
    #     obj.save(filename)

    
    #play the sound depending on the OS
    if OS == "Windows":
        os.system(f'start {filename}')
    elif OS == "Linux":
        os.system(f'aplay {filename} > /dev/null 2>&1')
    elif OS == "Darwin":
        os.system(f'afplay {filename}')
    else:
        print("OS not supported for tts")

if __name__ == '__main__':
    main()