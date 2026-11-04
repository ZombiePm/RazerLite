"""Basilisk V3 button 0x60 -> F24; leave scroll-mode button 0x6a untouched.
Protocol reference: GavinViney/openrazer-win, mouse.py, class 02 commands 8c/0c.
"""
import json
from openrazer_win.protocol.report import RazerReport
BUTTON=0x60

def active_profile(device):
    req=RazerReport(5,0x84,1);req.transaction_id=0x1f
    value=device.transport.send_payload(req,True).arguments[0]
    if not 0 <= value <= 5:raise ValueError("Unsupported active profile")
    return value

def read(device, button=BUTTON, profile=0):
    req=RazerReport(2,0x8c,2);req.transaction_id=0x1f
    req.arguments[:2]=bytes([profile,button])
    return bytes(device.transport.send_payload(req,True).arguments[:10])

def write(device, args):
    if len(args)!=10 or args[1]!=BUTTON or not 0 <= args[0] <= 5:raise ValueError('Unexpected binding target')
    args=args[:2]+b'\x00'+args[3:]
    req=RazerReport(2,0x0c,10);req.transaction_id=0x1f;req.arguments[:10]=args
    device.transport.send_payload(req,True)
    if read(device,profile=args[0])!=args:raise RuntimeError('Button mapping readback mismatch')

def ensure(device, backup, profile=0):
    before=read(device,profile=profile)
    wanted=bytes([profile,BUTTON,0,2,2,0,0x73,0,0,0])
    if before==wanted:return
    if not backup.exists():
        backup.write_text(json.dumps({'button':BUTTON,'arguments':before.hex(),'scroll':read(device,0x6a,profile).hex()}))
    scroll=read(device,0x6a,profile)
    try:
        write(device,before) # verify exact roundtrip before changing assignment
        write(device,wanted)
        if read(device,0x6a,profile)!=scroll:raise RuntimeError('Scroll binding changed')
    except Exception:
        write(device,before)
        raise

def restore(device,backup):
    value=json.loads(backup.read_text())
    write(device,bytes.fromhex(value['arguments']))
