import socket
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("0.0.0.0", 55555))

while True:
    data, addr = sock.recvfrom(1024)
    try:
        if len(data) >= 10:
            senderId, destId, PD, transid, senderSubId, destSubId, length = struct.unpack("HHBBBBH", data[:10])
            payload = data[10:]
            print("senderId %d, destId %d, PD %s, transid %s, senderSubId %s, destSubId %s, length %d" % (
            senderId, destId, PD, transid, senderSubId, destSubId, length))
            print("payload: ", payload)
            # if senderId == id and destSubId==sid:
            # return payload
    except Exception as e:
        pass
        # print("Can`t pars packed: {}".format(data))
        # print("Error: {}".format(e))
        # print("Stack: {}".format(traceback.format_exc()))
