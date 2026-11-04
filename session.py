"""Foreground detection + Windows-key-only hook, no injection into games."""
import ctypes as c
from ctypes import wintypes as w
import json, pathlib, threading, time, os, queue, logging, logging.handlers
from color_cycle import PressLatch
import color_worker
ROOT=pathlib.Path(__file__).resolve().parent
STATE=pathlib.Path('C:/ProgramData/RazerLite/session/game.json')
u=c.WinDLL('user32',use_last_error=True); k=c.WinDLL('kernel32',use_last_error=True)
LRESULT=c.c_ssize_t
HOOK=c.WINFUNCTYPE(LRESULT,c.c_int,w.WPARAM,w.LPARAM)
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
u.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
u.MonitorFromWindow.argtypes=[w.HWND,w.DWORD];u.MonitorFromWindow.restype=w.HANDLE
class Monitor(c.Structure): _fields_=[('size',w.DWORD),('rect',w.RECT),('work',w.RECT),('flags',w.DWORD)]
u.GetMonitorInfoW.argtypes=[w.HANDLE,c.POINTER(Monitor)]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
k.CloseHandle.argtypes=[w.HANDLE]
k.GetModuleHandleW.argtypes=[w.LPCWSTR];k.GetModuleHandleW.restype=w.HMODULE
u.SetWindowsHookExW.argtypes=[c.c_int,HOOK,w.HINSTANCE,w.DWORD];u.SetWindowsHookExW.restype=w.HANDLE
u.CallNextHookEx.argtypes=[w.HANDLE,c.c_int,w.WPARAM,w.LPARAM];u.CallNextHookEx.restype=LRESULT
u.UnhookWindowsHookEx.argtypes=[w.HANDLE]
u.GetMessageW.argtypes=[c.POINTER(w.MSG),w.HWND,w.UINT,w.UINT]
k.CreateMutexW.argtypes=[w.LPVOID,w.BOOL,w.LPCWSTR];k.CreateMutexW.restype=w.HANDLE
mutex=k.CreateMutexW(None,False,'Local\\RazerLiteSession')
if not mutex or c.get_last_error()==183: raise SystemExit(0)
gaming=False;last_update=0.0
color_enabled=False
color_presses=queue.SimpleQueue()
color_latch=PressLatch()

def foreground(cfg):
    hwnd=u.GetForegroundWindow()
    if not hwnd:return False
    pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(pid))
    h=k.OpenProcess(0x1000,False,pid.value)
    if not h:return False
    try:
        buf=c.create_unicode_buffer(32768);length=w.DWORD(len(buf))
        if not k.QueryFullProcessImageNameW(h,0,buf,c.byref(length)):return False
        name=pathlib.PureWindowsPath(buf.value).name.lower()
    finally:k.CloseHandle(h)
    if cfg['mode']=='always':return True
    if name in [x.lower() for x in cfg['exclude']]:return False
    if name in [x.lower() for x in cfg['games']]:return True
    if cfg['mode']!='fullscreen':return False
    rect=w.RECT();mi=Monitor();mi.size=c.sizeof(mi)
    if not u.GetWindowRect(hwnd,c.byref(rect)):return False
    if not u.GetMonitorInfoW(u.MonitorFromWindow(hwnd,2),c.byref(mi)):return False
    return rect.left<=mi.rect.left and rect.top<=mi.rect.top and rect.right>=mi.rect.right and rect.bottom>=mi.rect.bottom

def watch():
    global gaming,last_update,color_enabled
    STATE.parent.mkdir(parents=True,exist_ok=True)
    while True:
        try:
            cfg=json.loads((ROOT/'config.json').read_text())
            gaming=foreground(cfg);last_update=time.monotonic()
            color_enabled=bool(cfg.get('color_button',False))
            tmp=STATE.with_suffix('.tmp')
            tmp.write_text(json.dumps({'gaming':gaming,'time':time.time()}))
            os.replace(tmp,STATE)
        except Exception:
            gaming=False
            logging.exception('Foreground monitor failed')
        time.sleep(.25)

class Key(c.Structure): _fields_=[('vk',w.DWORD),('scan',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
blocked=set()
@HOOK
def callback(code,msg,data):
    if code>=0:
        key=c.cast(data,c.POINTER(Key)).contents.vk
        if key==0x87 and color_enabled and not (c.cast(data,c.POINTER(Key)).contents.flags & 0x10):
            if msg in (0x100,0x104):
                if color_latch.feed(True):color_presses.put((True,time.time_ns()))
                return 1
            if msg in (0x101,0x105):
                if color_latch.held:
                    color_latch.feed(False)
                    color_presses.put((False,time.time_ns()))
                return 1
        if key in (0x5b,0x5c):
            if msg in (0x100,0x104) and gaming and time.monotonic()-last_update<2:
                blocked.add(key);return 1
            if key in blocked:
                if msg in (0x101,0x105):blocked.discard(key)
                return 1
    return u.CallNextHookEx(None,code,msg,data)

if __name__=='__main__':
    STATE.parent.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,handlers=[logging.handlers.RotatingFileHandler(STATE.parent/'session.log',maxBytes=262144,backupCount=2)])
    color_stop=threading.Event()
    threading.Thread(target=color_worker.run,args=(color_presses,STATE.parent/'color.json',color_stop),daemon=True).start()
    hook=u.SetWindowsHookExW(13,callback,k.GetModuleHandleW(None),0)
    if not hook:raise c.WinError(c.get_last_error())
    threading.Thread(target=watch,daemon=True).start()
    try:
        msg=w.MSG()
        while u.GetMessageW(c.byref(msg),None,0,0)>0:
            u.TranslateMessage(c.byref(msg));u.DispatchMessageW(c.byref(msg))
    finally:
        color_stop.set()
        u.UnhookWindowsHookEx(hook)
        STATE.write_text(json.dumps({'gaming':False,'time':time.time()}))
