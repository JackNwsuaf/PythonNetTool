import socket
import sys
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ""
target = ""
upload_description = ""
port = 0


def usage():
    print "Python Net Tool"
    print
    print "Usage:pnt.py -t target_host -p port"
    print "-l --listening       - listen on [host]:[port] for incoming connections"
    print "-e --execute=file_to_run     - execute the given file upon receiving connection"
    print "-c --command     - initialize a command shell"
    print "-u --upload=destination      - upon receiving connection upload a file and write to [destination]"
    print
    print
    print "Examples:"
    print  "pnt.py -t 192.168.1.1 -p 1989 -l -c"
    print  "pnt.py -t 192.168.1.1 -p 1989 -l cu=c:\\target.exe"
    print "pnt.py -t 192.168.1.1 -p 1989 -l -e=\"/etc/passwd\""
    print "echo 'ABCD' | ./pnt.py 192.168.11.2 -p 135 "


def main():
    global listen
    global port
    global execute
    global command
    global upload_description
    global target

    if not len(sys.argv[1:]):
        usage()

    # 读取命令行
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu",
                                   ["help", "listen", "port", "command", "upload"])  # longopts without "="?!
    except getopt.GetoptError as err:
        print str(err)
        usage()
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_description = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"
    # Listen or send data from stdin
    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        # Send data
        client_sender(buffer)


main()


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Link target host
        client.connect((target, port))
        if len(buffer):
            client.send(buffer)
        while True:  # Ctrl-D to stop
            recv_len = 1
            response = ""
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)

                if recv_len < 4096:
                    break
            print response,
        buffer = raw_input("")
        buffer += "\n"  # shell compatibility
        client.send(buffer)

    except:

        print "Exception! Exiting."
        client.close()


def server_loop():
    global target  # port?

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def run_command(command):
    command = command.rstrip()  # remove trailing space
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to excute command.\r\n"
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    if (upload_description):
        file_buffer = ""

        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        try:
            file_descriptor = open(upload_description, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            client_socket.send("Successfully saved file  to %s\r\n" % upload_description)

        except:
            client_socket.send("Falied to save file to %s\r\n" % upload_description)

    if len(execute):
        output=run_command(execute)
        client_socket.send(output)

    if command:
        while True:
            client_socket.send("<PNT:#>")
            cmd_buffer=""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
                response = run_command(cmd_buffer)
                client_socket.send(response)

