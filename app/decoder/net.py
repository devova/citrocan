import websocket

from decoder.base import DecoderGroup, TransportInterface


class WebSocketDecoder(DecoderGroup, TransportInterface):

    def __init__(self, *args, **kwargs):
        super(WebSocketDecoder, self).__init__(*args, **kwargs)
        for decoder in self.decoders:
            decoder.transport = self
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
            cid = flds[1]
            clen = int(flds[2])
            cflds = []
            for n in range(clen):
                cflds.append(int(flds[n + 3], 16))
            self.decode(cid, clen, cflds)
            self.connected = True
            self.update = True
        except (TypeError, ValueError, IndexError) as e:
            print("can't decode:", buf, e)

    def send_message(self, id, data):
        buf = 'S %s %s ' % (id, len(data))
        buf += ' '.join(hex(b) for b in data)
        self.sock.send(buf)
