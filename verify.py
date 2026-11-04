"""Run on Windows, with RazerLite service stopped to avoid concurrent HID requests."""
import pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).parent/'vendor'))
from openrazer_win.core.manager import DeviceManager
m=DeviceManager(bluetooth=False)
try:
 ds=m.scan();assert {d.pid for d in ds}>={0x99,0x23f}
 mouse=m.by_pid(0x99);kbd=m.by_pid(0x23f)
 assert mouse.get_dpi()==(26000,26000)
 assert all(s==(26000,26000) for s in mouse.get_dpi_stages()[1])
 print('PASS: hardware readback: DPI 26000, all DPI stages 26000')
 print('Keyboard game mode:',kbd.get_game_mode())
 for d in ds:
  try: print(d.name,'brightness:',d.get_brightness())
  except Exception as e: print('LIMITATION: brightness readback unavailable for', d.name, str(e))
finally:m.close()
