import socket

from decoder.base import DecoderGroup


class TelnetDecoder(DecoderGroup):

    def __init__(self, decoders, proxy_attributes=False):
        super(TelnetDecoder, self).__init__(
            decoders, proxy_attributes=proxy_attributes)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, ip, port):
        self.sock.connect((ip, port))
        try:
            buf = self.sock.recv(1024)
            self.on_message(buf)
        finally:
            self.sock.close()

    def on_message(self, buf):
        try:
            flds = buf.split()
            cid = int(flds[1], 16)
            clen = int(flds[2])
            cflds = []
            for n in range(clen):
                cflds.append(int(flds[n + 3], 16))
            self.decode(cid, clen, cflds)
            self.connected = True
            self.update = True
        except (TypeError, ValueError, IndexError) as e:
            print("can't decode:", buf, e)


