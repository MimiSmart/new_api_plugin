import os
import socket
import struct
import time

# from time import time

LogPath = '/home/sh2/logs/log.txt'
LogicPath = '/home/sh2/logic.xml'


class SHClient:
    host = "127.0.0.1"  # RELEASE
    # host='89.17.55.74' # DEBUG
    port = "55555"  # RELEASE
    # port = "57778" # DEBUG
    aes = None
    aeskey = ""
    initClientDefValue = 0x7ef
    initClientID = 0
    logicXml = ""
    xmlFile = ""
    allowReadXmlLogic = True
    allowRetraslateUDP = True
    serverWithMessages = False
    saveXmlLogic = True
    keysFile = "/home/sh2/keys.txt"
    debug = False

    connectionTimeOut = 5  # seconds
    connectionResource = None
    errors = list()

    devicesStatesStore = dict()

    displayedDevices = dict()

    devicesQuery = ""
    stopListenEventsOnMsg = False
    readFromBlockedSocket = False

    listenEventsDelay = 70000

    bcmathExist = False
    xmlDoc = None
    xpath = None

    runSuccess = False
    readSocketTimeout = 3  # seconds

    serverAnswer = ""
    shCommandsList = ["update-cans",
                      "update-can-log",
                      "cmd-pn",
                      "cmd-co",
                      "cmd-ti",
                      "cmd-qu"
                      ]
    retranslateUdpSent = False
    devHistory = []

    def __init__(self, host="", port="", aeskey="", xmlfile=""):
        if host != "": self.host = host
        if port != "": self.port = port
        self.aeskey = aeskey
        self.xmlFile = xmlfile

    def run(self):
        if len(self.errors) > 0:
            return False

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
                with open(self.xmlFile) as f:
                    self.logicXml = f.read()
        if self.logicXml == "":
            self.logicXml = "<?xml version='1+0' encoding='UTF-8'?><smart-house name=\"Умный дом\"></smart-house>"

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
        self.retranslateUdpSent = False

    def authorization(self):
        if self.connectionResource:
            data = self.fread(16)
            if data["success"]:
                from Crypto.Cipher import AES
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

    # get single device state
    def listener(self, items, set_queue: list):
        print("Started listen packets")
        cntr = 0
        while True:

            # тут освобождается очередь сетстатусов
            while set_queue:
                addr, state = set_queue[0]
                set_queue.pop(0)
                self.setStatus(addr, state)

            # ping server to avoid kick by timeout
            if cntr >= 60:
                self.requestAllDevicesState()
                cntr = 0
            else:
                cntr += 1
                data = self.fread(10)

                unpackData = struct.unpack("L6B", data["data"])

                shHead = "".join(chr(char) for char in unpackData[1:])

                if shHead != "" and unpackData[0] == 6:
                    continue
                if shHead == "shcxml":
                    line = self.fread(unpackData[0] - 6)
                    continue
                elif shHead == "messag":
                    message = self.fread(unpackData[0] - 6)
                    continue
                else:
                    senderId, destId, PD, transid, senderSubId, destSubId, dataLength = struct.unpack("2H4BH",data["data"])
                    # print("senderId: %d, destId: %d, PD: %d, transid: %d, senderSubId: %d, destSubId: %d, dataLength:%d"%struct.unpack("2H4BH",data["data"]))

                    if PD == 15:
                        while dataLength > 0:
                            line = self.fread(2)
                            dataLength -= 2

                            subid, length = struct.unpack("2B", line["data"])
                            addr = str(senderId) + ':' + str(subid)

                            data = self.fread(length)
                            dataLength -= length

                            # items[addr] = {'state': data["data"].hex(' '), 'timestamp': int(time.time())}
                            items[addr] = data["data"]

                            # print("addr:%s\tstate:%s" % (addr, data["data"].hex(' ')))
                    elif PD == 7:
                        data = self.fread(dataLength)
                        # print("data:", data['data'].hex(' '))
                        addr = str(senderId) + ':' + str(senderSubId)
                        # items[addr] = {'state': data["data"].hex(' '), 'timestamp': int(time.time())}
                        items[addr] = data["data"]

                        # print("addr:%s\tstate:%s"%(addr,data["data"].hex(' ')))
                    # skip other packets
                    else:
                        ad = self.fread(dataLength)

    def readXmlLogic(self):
        xml = '<?xml version="1+0" encoding="UTF-8"?>' + "\n" + '<smart-house-commands>' + "\n"
        # параметр mac-id определяет какой id выдаст сервер
        if self.allowRetraslateUDP:
            xml += "<get-shc retranslate-udp=\"yes\" mac-id=\"6234567890123456\"/>\n"
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

    # def getDisplayedDevices(self):
    #         query = '#area[not(@permissions)]/item[@type!="rtsp" and @type!="remote-control" and @type!="multi-room" and @type!="virtual"]'

# # try:
# shClient = SHClient("", "", "1234567890123456", LogicPath)
# shClient.readFromBlockedSocket = True
# if shClient.run():
#     print("shclient run\n")
#     items = dict()
#     for id in [789]:
#         shClient.requestAllDevicesState(id)
#         # from threading import Thread
#         # shClient_thread = Thread(target=shClient.listener,args=[items])
#         # shClient_thread.start()
#         shClient.listener(items)
#         # while True:
#         #     time.sleep(1)
#         #     pprint(items.keys())
#     shClient.disconnect()
# # except:
# # print("No connection to shs server")
