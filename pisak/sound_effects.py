"""
Sound effects player.
"""
from gi.repository import Gst
from pisak import logger

_LOG = logger.get_logger(__name__)

Gst.init()

class Sound(object):
    def __init__(self, path):
        super().__init__()
        self._playbin = Gst.ElementFactory.make('playbin')
        self._playbin.set_property('uri', 'file://' + str(path))

    def play(self):
        self._playbin.set_state(Gst.State.READY)
        self._playbin.set_state(Gst.State.PLAYING)
    
class SoundEffectsPlayer(object):
    def __init__(self, sounds_list):
        super().__init__()
        self.sounds = {}

        CHANNELS_PER_FILE = 1
        DEFAULT_CONFIG = {
            'file_name': '',
            'volume': 1.0,
            'loop_count': 1
        }

        for sound_name, value in sounds_list.items():
            config = DEFAULT_CONFIG.copy()
            if isinstance(value, dict):
                config.update(value)
            else:
                config['file_name'] = value
            volume = float(config['volume'])
            # volumes[sound_name] = volume
            vec = []
            for i in range(CHANNELS_PER_FILE):
                vec.append(Sound(config['file_name']))
            self.sounds[sound_name] = tuple(vec)
            # print('xxx: ' + str(self.sounds))

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name][0].play()
        else:
            _LOG.warning('Sound not found.')

    def set_volume(self, volume):
        pass

    def shutdown(self):
        pass
