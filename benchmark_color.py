"""Local synthetic callback -> worker -> live HID-service latency. No OS key injection.
Run on Windows with RazerLite Running and RazerLiteSession stopped.
"""
import ctypes as c,json,pathlib,threading,time,re,statistics
import session as s
from color_cycle import load_selection,save_selection
import color_worker
path=s.STATE.parent/'color.json';original=load_selection(path)
log=path.parent.parent/'hardware.log';offset=log.stat().st_size
stop=threading.Event();worker=threading.Thread(target=color_worker.run,args=(s.color_presses,path,stop));worker.start()
key=s.Key();key.vk=0x87;s.color_enabled=True
address=c.addressof(key)
try:
 for _ in range(7):
  s.callback(0,0x100,address);time.sleep(.06)
  s.callback(0,0x101,address);time.sleep(.12)
 s.callback(0,0x100,address);time.sleep(1.8)
 s.callback(0,0x101,address);time.sleep(.1)
 released=load_selection(path)
 time.sleep(.35)
 assert load_selection(path)['rgb']==released['rgb'],'Color kept moving after release'
 assert released['held'] is False
 print('PASS: seven taps, smooth hold, release freezes selected RGB')
finally:
 stop.set();worker.join(1)
 original['event_ns']=time.time_ns();original['held']=False
 save_selection(path,original)
 time.sleep(.15)
with log.open() as f:
 f.seek(offset);lines=f.read().splitlines()
for name in ('Razer Basilisk V3','Razer Cynosa Lite'):
 values=[float(line.rsplit('=',1)[1]) for line in lines if 'Color applied '+name in line]
 assert len(values)>=15,(name,'not enough acknowledged color frames',len(values))
 print(name,'frames',len(values),'median_ms',round(statistics.median(values),1),'max_ms',max(values))
