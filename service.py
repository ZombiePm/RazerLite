"""Native SCM dispatcher using only Python's standard library."""
import ctypes as c
from ctypes import wintypes as w
import hardware
adv=c.WinDLL('advapi32',use_last_error=True)
class Status(c.Structure):
    _fields_=[(n,w.DWORD) for n in ('type','state','accepted','winexit','exit','checkpoint','hint')]
MAIN=c.WINFUNCTYPE(None,w.DWORD,c.POINTER(w.LPWSTR))
HANDLER=c.WINFUNCTYPE(w.DWORD,w.DWORD,w.DWORD,w.LPVOID,w.LPVOID)
class Entry(c.Structure): _fields_=[('name',w.LPWSTR),('main',MAIN)]
adv.RegisterServiceCtrlHandlerExW.argtypes=[w.LPCWSTR,HANDLER,w.LPVOID]
adv.RegisterServiceCtrlHandlerExW.restype=w.HANDLE
adv.SetServiceStatus.argtypes=[w.HANDLE,c.POINTER(Status)]
adv.StartServiceCtrlDispatcherW.argtypes=[c.POINTER(Entry)]
handle=None

def report(state,exitcode=0):
    s=Status(0x10,state,5 if state==4 else 0,exitcode,0,0,10000 if state==3 else 0)
    adv.SetServiceStatus(handle,c.byref(s))
@HANDLER
def control(code,event,data,context):
    if code in (1,5):
        report(3)
        hardware.STOP.set()
    return 0
@MAIN
def main(argc,argv):
    global handle
    handle=adv.RegisterServiceCtrlHandlerExW('RazerLite',control,None)
    if not handle:return
    report(4)
    result=0
    try: hardware.run()
    except Exception: result=1
    finally:report(1,result)
entries=(Entry*2)(Entry('RazerLite',main),Entry(None,MAIN()))
if not adv.StartServiceCtrlDispatcherW(entries): raise c.WinError(c.get_last_error())
