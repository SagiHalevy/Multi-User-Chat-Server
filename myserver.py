import socket
import select
import myprotocol


def set_name(arguments, client_socket, names_dict):
    """sets name for the client, if impossible- return corresponding message"""
    if len(arguments) == 1 and arguments != ['']:  # name must be exactly one word and not empty
        name = arguments[0]
        if not client_exist(name, names_dict):  # name must not be taken by other client
            previous_name = get_name_from_socket(client_socket, names_dict)
            if not previous_name:  # if that client doesn't yet has name
                names_dict[name] = client_socket
            else:  # if the client already has name, update it with the new one
                del names_dict[previous_name]
                names_dict[name] = client_socket
            return "Hello " + name
        else:
            return "The name " + name + " is taken, try pick another name"
    return False


def get_names(arguments, names_dict):
    """
    return all the names of the clients that have name
    """
    if len(arguments) == 0:
        all_names = ",".join(names_dict.keys())
        if not all_names:  # if no client has name yet
            return "Nothing is here yet..."
        return all_names
    return False


def send_msg(arguments, client_socket, names_dict, messages_to_send):
    """
    sends a message from a client to client
    """
    if len(arguments) >= 2:
        sender = get_name_from_socket(client_socket, names_dict)
        if not sender:  # client must have name before sending a message
            return "You don't have name yet! use NAME <name> to set your name"

        if client_exist(arguments[0], names_dict):  # if receiver client exist, create the message
            receiver_socket = names_dict[arguments[0]]
            msg = " ".join(arguments[1:])
            msg_with_sender = sender + " sent: " + msg
            messages_to_send.append((receiver_socket, msg_with_sender))
            return "ResponseNotRequired"
        else:
            return "Client " + arguments[0] + " not found!"
    else:
        return False


def client_exist(name, names_dict):
    """
    check if the client exist or not returns(True/False)
    """
    if name in names_dict.keys():
        return True
    else:
        return False


def get_name_from_socket(my_socket, names_dict):
    """
    if given client socket has name, return that names, otherwise return false
    """
    for name, current_socket in names_dict.items():
        if current_socket == my_socket:
            return name
    return False


# this will hold the function for each available command
instructions = {"NAME": set_name, "GET_NAMES": get_names, "MSG": send_msg}


def disconnect_client(client_socket, names_dict, client_sockets):
    """
    disconnect given client from the socket, while removing from all the dictionaries and lists
    """
    print("Client ", client_socket.getpeername(), "has left")
    potential_name = get_name_from_socket(client_socket, names_dict)
    if potential_name:
        del names_dict[potential_name]
    client_sockets.remove(client_socket)
    client_socket.close()


def check_cmd(cmd):
    """
    check for the commands and arguments of a given input , split them accordingly, and return the instruction and
    arguments, if they're invalid, return empty list
    """
    split_input = cmd.split(" ")
    instruction, arguments = split_input[0], split_input[
                                             1:]  # try pull the first word from the input and rest are arguments
    handler = instructions.get(
        instruction)  # if the command is a valid command, handler will be changed to the current function

    if handler:  # if the command was found
        return instruction, arguments  # will check validation for the command's arguments

    return [], []  # command is invalid


def create_server_rsp(instruction, arguments, client_socket, names_dict, messages_to_send):
    """
    call the function according to the given instruction(command) of the user, return the result of that function
    """
    handler = instructions.get(instruction)
    if instruction == 'NAME':
        return handler(arguments, client_socket, names_dict)

    elif instruction == 'GET_NAMES':
        return handler(arguments, names_dict)

    elif instruction == 'MSG':
        return handler(arguments, client_socket, names_dict, messages_to_send)


def main():
    name_to_socket = {}
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", myprotocol.PORT))
    server_socket.listen()
    print("Server is up!")

    client_sockets = []  # will hold all the clients that currently connected
    messages_to_send = []  # will hold all the messages that need to be sent, each element is (client_socket, message)
    while True:
        read_list, write_list, error_list = select.select([server_socket] + client_sockets, client_sockets, [])

        for current_socket in read_list:  # get new clients
            if current_socket is server_socket:
                client_socket, client_address = server_socket.accept()
                print("New client joined : ", client_address)
                client_sockets.append(client_socket)

            else:  # takes care of messages from clients
                try:
                    valid_msg, cmd = myprotocol.get_msg(current_socket)
                    if cmd == "":  # if client want to disconnect
                        disconnect_client(current_socket, name_to_socket, client_sockets)
                    else:
                        if valid_msg:
                            # 1. Print received message
                            print(cmd)
                            # 2. Check if the command is valid, use "check_cmd" function
                            instruction, arguments = check_cmd(cmd)
                            # 3. If valid command - create response
                            if instruction:
                                potential_response = create_server_rsp(instruction, arguments, current_socket,
                                                                       name_to_socket, messages_to_send)
                                if potential_response is not False:
                                    response = potential_response
                                else:
                                    response = "Invalid arguments"

                            else:
                                response = "Invalid instruction"

                        else:
                            response = "Wrong protocol"
                            current_socket.recv(1024)  # Attempt to empty the socket from possible garbage
                        if response != "ResponseNotRequired":  # if the response should be sent to client
                            messages_to_send.append((current_socket, response))
                except (ConnectionResetError, ConnectionAbortedError):
                    disconnect_client(current_socket, name_to_socket, client_sockets)
        for message in messages_to_send:  # take care of sending the messages
            current_socket, data = message
            if current_socket in write_list:
                data = "The server sent: " + data
                length_field_input = myprotocol.create_msg(data)  # 1. Add length field ("HELLO" -> "04HELLO")
                if length_field_input:
                    current_socket.send(length_field_input.encode())
                messages_to_send.remove(message)


if __name__ == "__main__":
    main()
