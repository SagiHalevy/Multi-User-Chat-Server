import msvcrt
import socket
import myprotocol
import select


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect(("127.0.0.1", myprotocol.PORT))

    print("Enter command")
    word = ""  # this will hold the input of the user

    while True:
        read_list, write_list, _ = select.select([my_socket], [my_socket], [])
        if read_list:
            valid_msg, cmd = myprotocol.get_msg(my_socket)  # get the server message using the protocol rules
            if valid_msg:
                print(cmd)  # 4. If server's response is valid, print it
        # Will follow the user input without blocking
        if msvcrt.kbhit():
            encoded_key = msvcrt.getch()
            if encoded_key == b'\r':  # enter pressed
                print()  # create new line to separate
                if word == 'EXIT':
                    user_input = ""
                else:
                    user_input = word
                word = ""
                length_field_input = myprotocol.create_msg(user_input)  # 1. Add length field ("HELLO" -> "04HELLO")
                if length_field_input:  # make sure the message follows the protocol rules
                    if write_list:
                        my_socket.send(length_field_input.encode())  # 2. Send it to the server
                        if user_input == "":  # if user wants to leave
                            break
                else:
                    print("Enter command")
            elif encoded_key == b'\x08':  # backslash pressed
                print("\b", end='', flush=True)
                print(" ", end='', flush=True)
                print("\b", end='', flush=True)
                word = word[:-1]
            else:
                key = encoded_key.decode()
                print(key, end='', flush=True)
                word = word + key

    print("Closing\n")
    # Close socket
    my_socket.close()


if __name__ == "__main__":
    main()
