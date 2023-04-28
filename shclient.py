import os
import socket
import struct
from pprint import pprint
import time

LogPath = '/home/sh2/logs/log.txt'
LogicPath = '/home/sh2/logic.xml'


# import socket
# connectionResource = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # connectionResource.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# # connectionResource.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# connectionResource.connect(("127.0.0.1", 55555))
# connectionResource.settimeout(5)
# res = connectionResource.recvfrom(10)


class SHClient():
    host = "127.0.0.1"
    port = "55555"
    aes = None
    aeskey = ""
    logFile = ""
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

    def __init__(self, host="", port="", aeskey="", logfile="", xmlfile=""):
        if host != "": self.host = host
        if port != "": self.port = port
        self.aeskey = aeskey
        self.logFile = logfile
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

        # from xml.dom import minidom,

        # begin load xml
        # self.xmlDoc = minidom.parse(self.logicXml)

        # ('1+0', "UTF-8")
        # self.xmlDoc.formatOutput = True
        # self.xmlDoc.preserveWhiteSpace = False

        # set_error_handler(function(number, error):
        #     if preg_match('/^DOMDocument::loadXML\(\): (++)/', error, m):
        #         throw new Exception(m[1])
        #     )
        #
        # try:
        #     self.xmlDoc.loadXML(self.logicXml)
        # except Exception:
        #     self.errors = "__METHOD__"+" line: "+"__LINE__"+" "+"parse xml error: "+e.getMessage()
        #     return False
        # restore_error_handler()
        # end load xml

        # self.xpath = new DOMXPath(self.xmlDoc)
        self.runSuccess = True
        # self.getDisplayedDevices()
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
                res += self.connectionResource.recvfrom(size - len(res))[0]
        else:
            stream_set_blocking(self.connectionResource, 0)  # set socket to nonblock status
            info = stream_get_meta_data(self.connectionResource)
            while (size - len(res)) > 0 and not info['timed_out'] and not feof(self.connectionResource):
                res += self.connectionResource.recvfrom(size - len(res))[0]
            self.connectionResource.setblocking(True)  # set socket to block status
        return {"success": success, "data": res}

    def disconnect(self):
        if self.connectionResource:
            self.connectionResource.close()
            self.connectionResource = None

    def requestDeviceState(self, id, subid):
        resultData = dict()
        if self.runSuccess and id > 0 and subid > 0:
            data = self.packData(id, 0, 14, 0, [0, 0, 0, 0, 0, 0])
            self.connectionResource.send(data)
            resultData = self.readDeviceState(id, subid)
        return resultData

    def packData(self, id, subid, pd, length, value=[0, 0, 0, 0, 0, 0]):
        s = struct.pack("2H4BH", self.initClientID, id, pd, 0, 0, subid, length)
        if length > 0:
            for i in range(length):
                s += struct.pack("B", value[i])
        return s

    # get single device state
    # def readDeviceState(self, id, subid):
    #     resultData = list()
    #     foundItem = False
    #     for j in range(300):
    #         if foundItem: break
    #
    #         data = self.fread(10)
    #         print(data)
    #         # bin = ''.join(data["data"])
    #         # print(bin2hex(bin))
    #
    #         if not data["success"]:
    #             return resultData
    #         unpackData = struct.unpack("L6B", data["data"])
    #         shHead = ""
    #         for i in range(1, 7):
    #             shHead += chr(unpackData[i])
    #
    #         if shHead != "" and unpackData[0] == 6:
    #             continue
    #
    #         if shHead == "shcxml":
    #             line = self.fread(4)
    #             if not line["success"]:
    #                 return resultData
    #             crc = struct.unpack("L", line["data"])
    #
    #             line = self.fread(1)
    #             if not line["success"]: return resultData
    #             addata = struct.unpack("B", line["data"])
    #             line = self.fread(unpackData[0] - 5)
    #             if not line["success"]: return resultData
    #         elif shHead == "messag":
    #             message = self.fread(unpackData[0] - 6)
    #             if not message["success"]: return resultData
    #         else:
    #             unpackData = struct.unpack("2H4BH", data["data"])
    #
    #             if unpackData[2] == 15:
    #                 dataLength = unpackData[6]
    #                 while dataLength > 0:
    #                     line = self.fread(2)
    #                     if not line["success"]:
    #                         return resultData
    #                     dataLength -= 2
    #                     ucanData = struct.unpack("2B", line["data"])
    #                     tmpdata = self.fread(ucanData[1])
    #                     if not tmpdata["success"]: return resultData
    #                     line = tmpdata["data"]
    #                     dataLength -= ucanData[1]
    #                     values = list()
    #                     index = str(unpackData[0]) + ":" + str(ucanData[0])
    #
    #                     # itemType = self.getItemType(int(unpackData[0]), int(ucanData[0]))
    #                     #
    #                     # if ucanData[1] == 1:
    #                     #     addata = struct.unpack("B", line)
    #                     #     values.append(addata[0])
    #                     # elif ucanData[1] == 2 and itemType != "dimer-lamp" and not strpos(itemType, "sensor"):
    #                     #     addata = struct.unpack("B", line)
    #                     #     values.append(addata[0])
    #                     # elif ucanData[1] == 2 and itemType == "dimer-lamp":
    #                     #     addata = struct.unpack("B", line)
    #                     #     for v in addata:
    #                     #         values.append(v)
    #                     #     if array_key_exists(1, values):
    #                     #         if self.bcmathExist: values[1] = round(bcdiv(values[1], 2+5))
    #                     #         else:
    #                     #             values[1] = round(values[1] / 2+5)
    #                     # elif ucanData[1] == 2:
    #                     addata = struct.unpack("H", line)
    #                     if addata[0] > 32768:
    #                         value = round((double)((65536 - addata[0]) / -256), 2)
    #                     else:
    #                         value = round((double)(addata[0] / 256), 2)
    #                     values.append(value)
    #                     # elif ucanData[1] > 2:
    #                     #     addata = struct.unpack("B", line)
    #                     #     for v in addata:
    #                     #         values.append(v)
    #                     # if int(id) == int(unpackData[0]) and int(subid) == int(ucanData[0]) and count(values):
    #                     #     foundItem = True
    #                     #     resultData = values
    #                     #     self.devicesStatesStore[index] = values
    #             else:
    #                 ad = self.fread(unpackData[1])
    #                 if not ad["success"]:
    #                     return resultData
    #     return resultData

    # # find item with requested id and subid in xml and return type attribute value
    # def getItemType(self, id, subid):
    #     type = ""
    #     if self.xpath is None: return type
    #
    #     query = '#item[(@id="' + str(id) + '" and @sub-id="' + str(subid) + '") or @addr="' + str(id) + ':' + str(
    #         subid) + '"]/@type'
    #
    #     entries = self.xpath.query(query)
    #     if is_object(entries) and entries.length > 0:
    #         type = entries.item[0].nodeValue
    #     return type

    def readXmlLogic(self):
        xml = '<?xml version="1+0" encoding="UTF-8"?>' + "\n" + '<smart-house-commands>' + "\n"
        if self.allowRetraslateUDP:
            xml += "<get-shc retranslate-udp=\"yes\" />\n"
        else:
            xml += "<get-shc />\n"
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

                    if self.xmlFile != "" and self.saveXmlLogic and (not os.path.exists(self.xmlFile)
                                                                     or (os.path.exists(
                                self.xmlFile) and os.path.getsize(self.xmlFile) != receivedFileSize)):
                        with open(self.xmlFile, "w") as f:
                            f.write(self.logicXml.decode('utf-8'))
                        chmod(self.xmlFile, 0o666)
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
    #     if self.runSuccess:
    #         query = '#area[not(@permissions)]/item[@type!="rtsp" and @type!="remote-control" and @type!="multi-room" and @type!="virtual"]'
    #         if self.devicesQuery != "": query = self.devicesQuery
    #         entries = self.xpath.query(query)
    #
    #         if is_object(entries) and entries.length > 0:
    #             for entry in entries:
    #                 entryAttributes = array()
    #                 for attr in entry.attributes:
    #                     entryAttributes[attr.nodeName] = attr.nodeValue
    #                 id = subid = 0
    #                 if "id" in entryAttributes:
    #                     id = entryAttributes["id"]
    #                 if "sub-id" in entryAttributes:
    #                     subid = entryAttributes["sub-id"]
    #                 if "addr" in entryAttributes:
    #                     id, subid = explode(":", entryAttributes["addr"])
    #                 if int(id) > 0 and int(subid) > 0:
    #                     index = id + ":" + subid
    #                     self.displayedDevices[index] = {"id": id, "subid": subid}


# try:
shClient = SHClient("", "", "1234567890123456", LogPath, LogicPath)
shClient.readFromBlockedSocket = True
if shClient.run():
    print("shclient run\n")
    pprint(shClient.requestDeviceState(524, 98))
# except:
# print("No connection to shs server")
