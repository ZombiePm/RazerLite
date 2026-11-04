"""One HID owner: responsive colors, slower device discovery and DPI checks."""
import json, logging, logging.handlers, pathlib, sys, threading, time
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'vendor'))
from openrazer_win.core.manager import DeviceManager
from openrazer_win.core.persistence import Persistence
from openrazer_win.protocol.chroma import extended_matrix_effect_static
from color_cycle import load_selection
import mouse_binding
STOP = threading.Event()
DATA = pathlib.Path('C:/ProgramData/RazerLite')

def apply_color(device,rgb):
    # The same extended-static protocol as the pinned recipes; use RAM storage
    # for animation frames. The final RGB is persisted by the session helper.
    zones=(0,4,1) if device.pid==0x99 else (5,)
    for led in zones:
        request=extended_matrix_effect_static(0,led,rgb)
        request.transaction_id=0x1f if device.pid==0x99 else 0x3f
        device.transport.send_payload(request,True)

def run():
    DATA.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(DATA/'hardware.log', maxBytes=524288, backupCount=2)
    logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s %(levelname)s %(message)s')
    manager = DeviceManager(bluetooth=False, persistence=Persistence(str(DATA/'state.json')))
    applied={};bound={};retry={};devices=[];selection=None
    scan_at=config_at=maintenance_at=0.;cfg=None
    try:
        while not STOP.is_set():
            now=time.monotonic()
            try:
                if now>=config_at:
                    cfg=json.loads((ROOT/'config.json').read_text());config_at=now+1
                if now>=scan_at:
                    devices=manager.scan();scan_at=now+3
                    applied={d:v for d,v in applied.items() if d in devices}
                    bound={d:v for d,v in bound.items() if d in devices}
                    retry={d:v for d,v in retry.items() if d in devices}
                if cfg.get('color_button',False):
                    try:selection=load_selection(DATA/'session'/'color.json')
                    except (OSError,ValueError,KeyError,TypeError):pass # keep last valid color
                rgb=selection['rgb'] if cfg.get('color_button',False) and selection else cfg['color']
                maintain=now>=maintenance_at
                for d in devices:
                    if d.pid not in (0x99,0x23f) or now<retry.get(d,0):continue
                    try:
                        signature=(tuple(rgb),cfg['brightness'])
                        previous=applied.get(d)
                        if previous is None or previous[0]!=signature or now-previous[1]>60:
                            apply_color(d,rgb)
                            if previous is None or previous[0][1]!=cfg['brightness']:
                                for zone in ('backlight','logo','scroll'):
                                    if d.has_effect('static',zone):
                                        try:d.set_brightness(cfg['brightness'],zone)
                                        except Exception as e:logging.warning('Brightness %s %s: %s',d.name,zone,e)
                            applied[d]=(signature,now)
                            event_ns=selection.get('event_ns',0) if selection else 0
                            latency=(time.time_ns()-event_ns)/1e6 if event_ns else -1
                            logging.info('Color applied %s rgb=%s input_latency_ms=%.1f',d.name,rgb,latency)
                        if not maintain:continue
                        if d.pid==0x99:
                            if cfg.get('color_button',False):
                                profile=mouse_binding.active_profile(d)
                                if bound.get(d)!=profile:
                                    mouse_binding.ensure(d,DATA/('button-original-profile-%s.json'%profile),profile)
                                    if d.get_device_mode()!='0:0':d.set_device_mode(0)
                                    bound[d]=profile
                                    logging.info('Color button verified in profile %s',profile)
                            target=min(int(cfg['dpi']),d.info.dpi_max)
                            if d.get_dpi()!=(target,target):
                                d.set_dpi(target)
                                if d.get_dpi()!=(target,target):raise RuntimeError('DPI readback mismatch')
                                logging.info('DPI restored to %s',target)
                        else:
                            try:
                                state=json.loads((DATA/'session'/'game.json').read_text())
                                gaming=bool(state['gaming']) and 0<=time.time()-state['time']<5
                            except (OSError,ValueError,KeyError):gaming=False
                            if d.get_game_mode()!=gaming:d.set_game_mode(gaming)
                    except Exception:
                        logging.exception('Device operation failed: %s',d.name)
                        applied.pop(d,None);retry[d]=time.monotonic()+1
                if maintain:maintenance_at=now+1
                STOP.wait(.02)
            except Exception:
                logging.exception('Hardware loop failed')
                manager.close();applied.clear();bound.clear();devices=[];scan_at=0
                STOP.wait(1)
    finally:
        for d in manager.devices:
            if d.pid==0x23f:
                try:d.set_game_mode(False)
                except Exception:pass
        manager.close()

if __name__=='__main__':run()
