import datetime
import os
import socket
import struct
import time

from Cryptodome.Cipher import AES

from logic import Logic

LogPath = '/home/sh2/logs/log.txt'
LogicPath = '/home/sh2/logic.xml'


class SHClient:
    host = "127.0.0.1"
    port = "55555"
    aeskey = ""
    initClientDefValue = 0x7ef
    initClientID = 0
    logicXml = ""
    xmlFile = ""
    allowReadXmlLogic = True
    allowRetraslateUDP = True
    keysFile = "/home/sh2/keys.txt"

    connectionTimeOut = 5  # seconds
    connectionResource = None

    readFromBlockedSocket = False
    runSuccess = False
    running = False

    logic: Logic

    def init_logic(self, _logic):
        self.logic = _logic

    def __init__(self, host="", port="", aeskey="", xmlfile=""):
        if host != "": self.host = host
        if port != "": self.port = port
        self.aeskey = aeskey
        self.xmlFile = xmlfile

    def run(self):
        self.connectToServer()
        if not self.connectionResource:
            return False
        self.authorization()
        if not self.connectionResource:
            print("Server authorization failed")
            return False

        if self.allowRetraslateUDP:
            if self.allowReadXmlLogic:
                self.readXmlLogic()
                if b"</smart-house>" not in self.logicXml:
                    print("Could not get xml logic from smart-house server")
                    return False
            elif self.xmlFile != "" and os.path.exists(self.xmlFile):
                self.readXmlLogic()
                # with open(self.xmlFile) as f:
                #     self.logicXml = f.read()
        if self.logicXml == "":
            self.logicXml = "<?xml version='1+0' encoding='UTF-8'?><smart-house name=\"Умный дом\"></smart-house>"

        self.connectionResource.setblocking(True)
        self.runSuccess = True
        return True

    # ready
    def connectToServer(self):
        try:
            self.connectionResource = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connectionResource.connect((self.host, int(self.port)))
            self.connectionResource.settimeout(self.connectionTimeOut)
        except:
            print('No connection to shs server')

    def authorization(self):
        if self.connectionResource:
            data = self.fread(16)
            if data["success"]:
                cipher = AES.new(self.aeskey.encode('utf-8'), AES.MODE_ECB)
                encrypted = cipher.encrypt(data['data'])
                self.connectionResource.send(encrypted)
            else:
                print("could not read data for authorization")
                self.disconnect()

    def fread(self, size):
        success = True
        res = bytes()
        if self.readFromBlockedSocket:
            while (size - len(res)) > 0:
                response = self.connectionResource.recvfrom(size - len(res))[0]
                # print(response.hex(' '))
                # len data equal 0 if server disconnect
                if not len(response):
                    print('SHclient disconnected')
                    exit(0)
                res += response
        else:
            self.connectionResource.setblocking(False)  # set socket to nonblock status
            while (size - len(res)) > 0:
                res += self.connectionResource.recvfrom(size - len(res))[0]
            self.connectionResource.setblocking(True)  # set socket to block status

        return {"success": success, "data": res}

    def disconnect(self):
        if self.connectionResource:
            self.connectionResource.close()
            self.connectionResource = None

    def requestAllDevicesState(self, id=0):
        if self.runSuccess:
            data = self.packData(id, 0, 14, 0, [0, 0, 0, 0, 0, 0])
            # print("Send data:", data.hex(' '))
            if not self.connectionResource.send(data):
                print("error send")

    def setStatus(self, addr, state):
        id, subid = addr.split(':')
        # while len(state)<6:
        #     state.append(0)
        if self.runSuccess:
            data = self.packData(int(id), int(subid), 5, len(state), state)
            # print("Send data:", data.hex(' '))
            if not self.connectionResource.send(data):
                print("error send")

    # PD=14 - REQUEST_ALL_DEVICES. if use with id module - this module returned first
    # PD=7 - set status
    # PD=1 - start packet
    # PD=30 - synchro time packet
    # PD=15 - ping module->server with states
    def packData(self, id, subid, pd, length, value=[0, 0, 0, 0, 0, 0]):
        s = struct.pack("2H4BH", self.initClientID, id, pd, 0, 0, subid, length)
        if length > 0:
            for i in range(length):
                s += struct.pack("B", value[i])
        return s

    def sender(self):
        cntr = 0
        while 1:
            if self.running:
                # тут проверяются запросы на историю итемов
                if self.logic.history_requests:
                    for addr in self.logic.history_requests.keys():
                        if not self.logic.items[addr].history and not self.logic.history_requests[addr]['requested']:
                            self.logic.history_requests[addr]['requested'] = True
                            self.getDeviceHistory(addr, self.logic.history_requests[addr]['range_time'],
                                                  self.logic.history_requests[addr]['scale'])
                            cntr = 0

                # тут освобождается очередь сетстатусов
                while self.logic.set_queue:
                    addr, state = self.logic.set_queue[0]
                    self.logic.set_queue.pop(0)

                    # для диммера устанавливаем время изменения яркости 0 секунд, если в запросе отсутствует
                    if (self.logic.items[addr].type == 'dimer-lamp' or self.logic.items[
                        addr].type == 'dimmer-lamp') and len(state) == 2:
                        state += b'\0'

                    self.setStatus(addr, state)

                    cntr = 0

                # тут отправляются пуши
                for push in self.logic.push_requests:
                    try:
                        tmp = push
                        self.logic.push_requests.pop(0)
                        self.sendMessage(tmp['message'], tmp['message_type'], tmp['id'], tmp['subid'])
                        cntr = 0
                    except:
                        print(''.join(
                            ["Error send message on ", str(push['id']), ':', str(push['subid']),
                             ', with type message = ',
                             str(push['message_type']), ' and text message: "', push['message'], '"']))
                        break

                # ping server to avoid kick by timeout
                if cntr >= 600:
                    self.ping()
                    cntr = 0
                else:
                    cntr += 1

                time.sleep(0.1)
            else:
                break

    def listener(self):
        self.running = True
        # print("Started listen packets")
        while True:
            data = self.fread(10)
            unpackData = struct.unpack("L6B", data["data"])
            shHead = "".join(chr(char) for char in unpackData[1:])

            if shHead != "" and unpackData[0] == 6:
                continue
            if shHead == "shcxml":
                self.fread(unpackData[0] - 6)
                continue
            elif shHead == "messag":
                self.fread(unpackData[0] - 6)
                continue
            elif shHead == "hismin":
                line = self.fread(unpackData[0] - 6)
                id, subid, data = struct.unpack("HB%ds" % (len(line['data']) - 3), line['data'])
                addr = str(id) + ':' + str(subid)
                self.logic.items[addr].history = list(struct.unpack("%dB" % (len(data)), data))
                if addr in self.logic.history_requests:
                    self.logic.history_requests[addr]['responsed'] = True
            # skip other packets
            else:
                self.fread(dataLength)

    def ping(self):
        xml = '<?xml version="1+0" encoding="UTF-8"?>' + "\n" + '<smart-house-commands>' + "\n"
        xml += "<ping/>\n"
        xml += "</smart-house-commands>\n"
        xmlsize = len(xml)
        data = struct.pack("L", xmlsize) + xml.encode('utf-8')
        self.connectionResource.send(data)

    def readXmlLogic(self):
        xml = '<?xml version="1+0" encoding="UTF-8"?>' + "\n" + '<smart-house-commands>' + "\n"
        # параметр mac-id определяет какой id выдаст сервер
        if self.allowRetraslateUDP:
            xml += "<get-shc retranslate-udp=\"no\" mac-id=\"6234567890123456\"/>\n"
        else:
            xml += "<get-shc mac-id=\"6234567890123456\"/>\n"
        # xml += '<get-shc keep-push="yes" crc32="0xD74D316D" mac-id="d66526a68c9718e9" current-id="45" retranslate-udp-optim="yes" remote-connection="yes" os-type="1" os-ver="33.0" send-ping-to="20" set-ping-to="30" resend="get-shc" srv-serial="61a4cce3" need-ip-ids="yes"/>'+"\n"

        xml += "</smart-house-commands>\n"
        xmlsize = len(xml)
        data = struct.pack("L", xmlsize) + xml.encode('utf-8')

        self.connectionResource.send(data)

        if self.connectionResource:
            logicXml = ""

            for j in range(3):
                if logicXml != "":
                    break
                data = self.fread(10)
                if not data["success"]:
                    return
                unpackData = struct.unpack("L6B", data["data"])
                shHead = ""
                for i in range(1, 7):
                    shHead += chr(unpackData[i])

                if shHead == "shcxml":
                    length = unpackData[0]
                    line = self.fread(4)
                    if not line["success"]:
                        return
                    crc = struct.unpack("L", line["data"])
                    line = self.fread(1)
                    if not line["success"]:
                        return
                    addata = struct.unpack("B", line["data"])
                    self.initClientID = self.initClientDefValue - addata[0]

                    receivedFileSize = length - 11
                    tmpdata = self.fread(receivedFileSize)
                    if not tmpdata["success"]:
                        return
                    logicXml = tmpdata["data"]
                    self.logicXml = tmpdata["data"]

                    self.logicXml.replace(b'&amp', b'#amp')
                    self.logicXml.replace(b'&', b'&amp')
                    self.logicXml.replace(b'#amp', b'&amp')

                    # if self.xmlFile != "" and self.saveXmlLogic and (not os.path.exists(self.xmlFile)
                    #                                                  or (os.path.exists(
                    #             self.xmlFile) and os.path.getsize(self.xmlFile) != receivedFileSize)):
                    # with open(self.xmlFile, "w") as f:
                    # f.write(self.logicXml.decode('utf-8'))
                    # chmod(self.xmlFile, 0o666)
                elif shHead == "messag":
                    message = self.fread(unpackData[0] - 6)
                    if not message["success"]:
                        return
                else:
                    tmpdata = self.fread(unpackData[0] - 6)
                    if not tmpdata["success"]:
                        return
                time.sleep(0.1)

    # addr - str "id:subid". ex.: "999:99"
    # range_date - list of 2 timestamps, ex.: [1683800000,1683800001]
    def getDeviceHistory(self, addr, range_time, scale):
        id, subid = addr.split(':')
        history = list()

        local_now = datetime.datetime.now().astimezone()
        gmtdiff = local_now.tzinfo.utcoffset(local_now).seconds * -1

        xml = ""
        xml += '<?xml version="1.0" encoding="UTF-8"?>' + "\n" + '<smart-house-commands>' + "\n"
        xml += '<get-history-minutely id="' + id + '" sub-id="' + subid + '"'
        if scale is not None and scale > 1:
            xml += ' scale="' + str(scale) + '"'
        xml += ' start-timet="' + str(range_time[0]) + '"'
        xml += ' end-timet="' + str(range_time[1]) + '"'
        xml += "/>\n"
        xml += "</smart-house-commands>\n"

        xmlsize = len(xml)
        data = struct.pack("L", xmlsize) + xml.encode('utf-8')
        if not self.connectionResource.send(data):
            print("Exception appeared. Couldn't write to socket next data: ", str(data))
        print("shclient: history request send")

    def sendMessage(self, message, message_type=1, id=2047, subid=32):
        if not self.runSuccess: return False
        message = message.encode('utf-8')
        length = 1 + len(message)

        data = struct.pack("2H4BH", self.initClientID, id, 5, 0, 0, subid, length)
        data += message_type.to_bytes(1, 'little')
        data += message

        if not self.connectionResource.send(data):
            print(''.join(
                ["Error send message on ", str(id), ':', str(subid), ', with type message = ', str(message_type),
                 ' and text message: "', message, '"']))
    # def getDisplayedDevices(self):
    #         query = '#area[not(@permissions)]/item[@type!="rtsp" and @type!="remote-control" and @type!="multi-room" and @type!="virtual"]'
