"""Service regression: repeated maintenance must not toggle keyboard firmware."""
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import hardware

class Keyboard:
    pid=0x23f;name='Synthetic keyboard'
    def __init__(self):self.reads=0;self.writes=[]
    def get_game_mode(self):self.reads+=1;return True
    def set_game_mode(self,value):self.writes.append(value)
    def has_effect(self,*args):return False

class StopAfter:
    def __init__(self):self.ticks=0
    def is_set(self):return self.ticks>=5
    def wait(self,seconds):self.ticks+=1

class Manager:
    def __init__(self,kbd):self.devices=[kbd]
    def scan(self):return self.devices
    def close(self):pass

class KeyboardModeTests(unittest.TestCase):
    def test_service_clears_legacy_mode_once_not_on_maintenance_or_shutdown(self):
        kbd=Keyboard();stop=StopAfter()
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/'config.json').write_text(json.dumps({'color_button':False,'color':[0,255,0],'brightness':100}))
            with patch.object(hardware,'ROOT',root),patch.object(hardware,'DATA',root),patch.object(hardware,'STOP',stop), \
                 patch.object(hardware,'DeviceManager',return_value=Manager(kbd)), \
                 patch.object(hardware,'apply_color'),patch.object(hardware.logging,'basicConfig'), \
                 patch.object(hardware.logging.handlers,'RotatingFileHandler'), \
                 patch.object(hardware.time,'monotonic',side_effect=lambda:stop.ticks*2.):
                hardware.run()
        self.assertEqual(kbd.reads,1)
        self.assertEqual(kbd.writes,[False])

if __name__=='__main__':unittest.main()
