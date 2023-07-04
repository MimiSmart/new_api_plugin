import struct
import traceback

from logic import Logic

logic: Logic = None
local_ip = None
server_id = 0


def init(_logic: Logic, ip):
    global logic, local_ip
    logic = _logic
    local_ip = ip


def print_packet(packet):
    print("\n\n***********************UDP Packet*************************\n\n")
    print("Ethernet Header\n")
    print(f"   |-Destination Address : {bytes(packet['eth_dest_addr']).hex('-')}")
    print(f"   |-Source Address      : {bytes(packet['eth_src_addr']).hex('-')}")
    print(f"   |-Protocol            : {packet['eth_protocol']}")

    print("\nIP Header\n")
    print(f"   |-IP Version        : {packet['ip_version']}")
    print(f"   |-IP Header Length  : {packet['ip_hdr_len'] / 4} DWORDS or {packet['ip_hdr_len']} Bytes")
    print(f"   |-Type Of Service   : {packet['ip_tos']}")
    print(f"   |-IP Total Length   : {packet['ip_total_len']}  Bytes(Size of Packet)")
    print(f"   |-TTL      : {packet['ip_ttl']}")
    print(f"   |-Protocol : {packet['ip_protocol']}")
    print(f"   |-Checksum : {packet['ip_checksum']}")
    print(f"   |-Source IP        : {packet['ip_src_addr']}")
    print(f"   |-Destination IP   : {packet['ip_dest_addr']}")

    print("\nUDP Header\n")
    print(f"   |-Source Port      : {packet['udp_src_port']}")
    print(f"   |-Destination Port : {packet['udp_dest_port']}")
    print(f"   |-UDP Length       : {packet['udp_len']}")
    print(f"   |-UDP Checksum     : {packet['udp_checksum']}")

    print("\nIP Header\n")
    print(f"{packet['ip_hdr'].hex(' ')}")
    print("\nUDP Header\n")
    print(f"{packet['udp_hdr'].hex(' ')}")
    print("\nData Payload\n")
    print(f"{packet['data_payload'].hex(' ')}")
    print("\n###########################################################")


def packet_handler(packet):
    global logic, local_ip, server_id
    try:
        if packet['ip_src_addr'] == local_ip or packet['ip_dest_addr'] == local_ip:
            # print_packet(packet)
            data = packet['data_payload']

            unpackData = struct.unpack("I6B", data[:10])
            shHead = "".join(chr(char) for char in unpackData[1:])

            if shHead != "" and unpackData[0] == 6:
                data = data[10:]
                pass
            if shHead == "shcxml":
                data = data[10:]
                line = data[:unpackData[0] - 6]
                data = data[unpackData[0] - 6:]

                # debug
                with open("udp_log.txt", 'a') as f:
                    print("Given 'shcxml' in udp!")
                    f.write("Given 'shcxml' in udp!\n")
            elif shHead == "messag":
                data = data[10:]
                message = data[:unpackData[0] - 6]
                data = data[unpackData[0] - 6:]
                # debug
                with open("udp_log.txt", 'a') as f:
                    print("Given 'messag' in udp!")
                    f.write("Given 'messag' in udp!\n")
            elif shHead == "hismin":
                data = data[10:]
                line = data[:unpackData[0] - 6]
                data = data[unpackData[0] - 6:]
                id, subid, data = struct.unpack("HB%ds" % (len(line) - 3), line)
                addr = f"{id}:{subid}"
                print(f'History {addr}: {list(struct.unpack("%dB" % (len(data)), data))}')
                with open("udp_log.txt", 'a') as f:
                    print("Given 'hismin' in udp!")
                    f.write("Given 'hismin' in udp!\n")
            else:
                # сделать вывод в лог ппакеты которые неправильно парсятся
                # byte skip_separator 0
                # byte lenPayload 1
                # short skip 2-4
                # short senderId 4-6
                # short destId 6-8
                # byte PD 8
                # byte transid 9
                # byte senderSubId 10
                # byte destSubId 11
                # byte lenState 12
                # byte skip_separator 13
                # state = data[13:]

                lenPayload, senderId, destId, PD, transId, senderSubId, destSubId, lenState = struct.unpack("xBx2H5Bx",
                                                                                                            data[:14])
                # print(f"{lenPayload=}, {senderId=}, {destId=}, {PD=}, {transId=}, {senderSubId=}, {destSubId=}, {lenState=}")

                # debug
                if senderId > 2047 or destId > 2047 or destSubId > 255 or senderSubId > 255:
                    with open("udp_log.txt", 'a') as f:
                        print('Incorrect parsing packet! Write to udp_log.txt')
                        f.write(f"{lenPayload=}, {senderId=}, {destId=}, {PD=}, {transId=},\n"
                                f" {senderSubId=}, {destSubId=}, {lenState=},\n"
                                f" data={data.hex(' ')}\n\n")
                else:
                    # print(data.hex(' '))
                    data = data[14:]

                    if PD == 15:
                        while lenState > 0:
                            line = data[:2]
                            data = data[2:]
                            lenState -= 2
                            subid, length = struct.unpack("2B", line)
                            addr = f"{senderId}:{subid}"

                            state = data[:length]
                            data = data[length:]
                            lenState -= length
                            if addr in logic.items:
                                logic.items[addr].set_state(state)

                                # свитч записывается в историю сразу при изменении
                                if logic.items[addr].type == 'switch':
                                    logic.items[addr].write_history()
                    elif PD == 7:
                        addr = f"{senderId}:{senderSubId}"
                        state = data[:lenState]
                        if addr in logic.items:
                            logic.items[addr].set_state(state)

                            # свитч записывается в историю сразу при изменении
                            if logic.items[addr].type == 'switch':
                                logic.items[addr].write_history()
                    # push-message
                    elif destId in [server_id, 2047] and destSubId == 32:
                        tmp = data[:lenState]
                        # data = self.fread(dataLength)['data']
                        type_message = tmp[0]
                        message = tmp[1:-1]
                        logic.push_events.append({'type': type_message, 'message': message.decode('utf-8'),
                                                  'sender': ''.join([str(senderId), ':', str(senderSubId)])})
                        print(f"Received push message on {senderId}:{senderSubId} from {destId}:{destSubId}, with type"
                              f" message is {type_message} and text message: {message.decode('utf-8')}")
    except Exception as ex:
        print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))


def run(id):
    global server_id
    server_id = id
    # sniffer.run(callback=packet_handler)
    while True:
        import time
        time.sleep(10)
# packet_handler(None)
# run()
