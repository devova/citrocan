import websocket

from decoder.base import DecoderGroup


class WebSocketDecoder(DecoderGroup):

    def __init__(self, decoders, proxy_attributes=False):
        super(WebSocketDecoder, self).__init__(
            decoders, proxy_attributes=proxy_attributes)
        self._terminate = False

    @property
    def terminate(self):
        return self._terminate

    def connect(self, url):
        self.sock = websocket.create_connection(url)
        buf = ''
        while not self.terminate:
            try:
                buf += self.sock.recv()
                if '\n' in buf:
                    buf = buf.split('\n')
                    message = buf[0][:-1]
                    buf = '\n'.join(buf[1:])
                    self.on_message(message)
            except:
                self.sock.close()
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
