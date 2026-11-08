"""Synthetic policy checks; no keystrokes are injected into the desktop."""
import ctypes as c,time
import session as s
key=s.Key();key.vk=0x5b
address=c.addressof(key)
s.gaming=True;s.last_update=time.monotonic()
assert s.callback(0,0x100,address)==1
s.gaming=False
assert s.callback(0,0x101,address)==1
assert not s.key_filter.presses
s.gaming=True;s.last_update=time.monotonic()-10
assert s.callback(0,0x100,address)!=1
print('PASS: Windows key down/up pairing; stale detector fails open')
s.color_enabled=True
key.vk=0x87
assert s.callback(0,0x100,address)==1
assert s.callback(0,0x100,address)==1
assert s.callback(0,0x101,address)==1
assert s.color_presses.qsize()==2
assert s.color_presses.get()[0] is True
assert s.color_presses.get()[0] is False
key.flags=0x10
assert s.callback(0,0x100,address)!=1
print('PASS: color key consumed, repeat ignored, injected input ignored')
class Kernel:
 def OpenProcess(self,*args):return 1
 def QueryFullProcessImageNameW(self,h,f,buf,length):buf.value='C:\\Games\\example.exe';return 1
 def CloseHandle(self,*args):pass
class User:
 def GetForegroundWindow(self):return 1
 def GetWindowThreadProcessId(self,*args):pass
 def GetWindowRect(self,h,p):
  r=p._obj;r.left=r.top=0;r.right=1920;r.bottom=1080;return 1
 def MonitorFromWindow(self,*args):return 1
 def GetMonitorInfoW(self,h,p):
  r=p._obj.rect;r.left=r.top=0;r.right=1920;r.bottom=1080;return 1
s.k=Kernel();s.u=User()
cfg={'mode':'fullscreen','games':[],'exclude':[]}
assert s.foreground(cfg)
cfg['exclude']=['example.exe'];assert not s.foreground(cfg)
cfg.update(mode='games',exclude=[]);assert not s.foreground(cfg)
cfg['games']=['example.exe'];assert s.foreground(cfg)
print('PASS: fullscreen, exclusions, explicit game list')
