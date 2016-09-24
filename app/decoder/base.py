import importlib
import sys

PY3 = sys.version_info >= (3, 0)


class CallbackException(Exception):
    """
    Raised when any Exception raised in call back
    """


class Decoder(object):
    _callbacks = {}
    mfs = {}

    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls, *args)
        ids = [prop_name[3:] for prop_name in dir(instance)
               if callable(getattr(instance, prop_name, None)) and prop_name.startswith('id_') and prop_name != 'id_else']
        instance.supported_ids = ids
        return instance

    def __setitem__(self, key, value):
        self.decode(key, value)

    def fetch_id(self, id):
        if isinstance(id, int):
            id = hex(id)
        return id

    def decode(self, id, data, data_len=None):
        if not data_len:
            data_len = len(data)
        data = data[:data_len]
        id = self.fetch_id(id)
        if id in self.supported_ids:
            f = getattr(self, 'id_%s' % id)
            f(data)
            for callback in self._callbacks.get(id, []):
                try:
                    callback(self, id, data)
                except:
                    raise CallbackException
        else:
            self.id_else(id, data)

    def id_else(self, id, data):
        pass

    @staticmethod
    def get_str(b):
        if PY3:
            ba = bytes(b).strip(b'\0')
        else:
            ba = bytes(b''.join([chr(x) for x in b if x]))
        try:
            s = ba.decode('utf8')
        except UnicodeDecodeError:
            try:
                s = ba.decode('cp1251', errors='replace')
            except UnicodeDecodeError:
                s = "<bad name>"
            except LookupError:
                s = "<wrong program build>"
        return s.strip()

    def parse_mf(self, id, data_len, data):
        typ = (data[0] & 0xf0) >> 4
        arg = data[0] & 0x0f
        if typ == 0:  # single
           return (arg, data[1:min(1 + arg, data_len)])
        elif typ == 1:  # first
            fl = arg * 256 + data[1]
            el = fl - (data_len - 2)
            self.mfs[id] = [fl, el, data[2:data_len]]
        elif typ == 2:  # consecutive. TODO: check frame order!
            if id not in self.mfs:
                return None
            el = self.mfs[id][1]
            if el > data_len - 1:
                self.mfs[id][1] -= data_len - 1
                self.mfs[id][2] += data[1:data_len]
            else:
                fl = self.mfs[id][0]
                d = self.mfs[id][2] + data[1:min(data_len, el + 2)]
                del self.mfs[id]
                return (fl, d)
        elif typ == 3:  # flow, packets not for us
            pass
        return None

    def on(self, id, callback):
        """
        Start listen for message with given id. Call callback when id has parsed
        """
        id = self.fetch_id(id)
        self._callbacks.setdefault(id, []).append(callback)

    def off(self, id, callback):
        """
        Stop listen for message with given id and given callback
        """
        id = self.fetch_id(id)
        self._callbacks.setdefault(id, []).remove(callback)


class DecoderGroup(object):

    def __init__(self, decoders, proxy_attributes=False):
        self._decoders = []
        self.proxy_attributes = proxy_attributes
        for decoder in decoders:
            module, cls = decoder.rsplit('.', 1)
            module = importlib.import_module(module)
            attr_name = cls[:-7] if cls.endswith('Decoder') else cls
            attr_name = attr_name.lower()
            attr = getattr(module, cls)()
            self._decoders.append(attr_name)
            setattr(self, attr_name, attr)

    def __getattr__(self, item):
        if not self.proxy_attributes:
            raise AttributeError
        for decoder in self.decoders:
            attr = getattr(decoder, item, None)
            if attr is not None:
                return attr

    @property
    def decoders(self):
        return [getattr(self, name) for name in self._decoders]

    def decode(self, id, data_len, data):
        for decoder in self.decoders:
            decoder.decode(id, data, data_len)

    def on(self, id, callback):
        for decoder in self.decoders:
            if id in decoder.supported_ids:
                decoder.on(id, callback)
