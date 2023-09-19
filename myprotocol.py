LENGTH_FIELD_SIZE = 3
PORT = 5555


def create_msg(data):
    """Create a valid protocol message, with length field"""
    length = str(len(data))
    zfill_length = length.zfill(LENGTH_FIELD_SIZE)
    if len(zfill_length) > LENGTH_FIELD_SIZE:
        print("Input is too long")
        return False
    message = zfill_length + data
    return message


def get_msg(my_socket):
    """Extract message from protocol, without the length field
       If length field does not include a number, returns False, "Error" """
    length = my_socket.recv(LENGTH_FIELD_SIZE).decode()
    if length.isdigit():
        message = my_socket.recv(int(length)).decode()
        return True, message

    return False, ""  # we shouldn't really get here if the function "create_msg" works well
