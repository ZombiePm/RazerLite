"""Palette, smooth hold controller and durable selection (no Windows dependencies)."""
import json
PALETTE = [[0,255,0],[0,255,255],[0,80,255],[180,0,255],[255,0,0],[255,180,0],[255,255,255]]

def load_selection(path):
    value=json.loads(path.read_text())
    index=value['index']
    if type(index) is not int or not 0 <= index < len(PALETTE):raise ValueError('Invalid color index')
    rgb=value.get('rgb',PALETTE[index])
    if not isinstance(rgb,list) or len(rgb)!=3 or any(type(v) is not int or not 0<=v<=255 for v in rgb):
        raise ValueError('Invalid RGB')
    return {**value,'index':index,'rgb':rgb}

def load_index(path):
    try:return load_selection(path)['index']
    except (OSError,ValueError,KeyError,TypeError):return 0

def save_selection(path,value):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value))
    tmp.replace(path)

def advance(path):
    index=(load_index(path)+1)%len(PALETTE)
    save_selection(path,{'index':index,'rgb':PALETTE[index]})
    return index

class PressLatch:
    def __init__(self): self.held=False
    def feed(self,down):
        trigger=down and not self.held
        self.held=down
        return trigger

class ColorController:
    HOLD_DELAY=.35
    LEG_SECONDS=1.4
    def __init__(self,selection):
        self.index=selection['index'];self.rgb=list(selection['rgb'])
        self.held=False;self.started=0.;self.start_index=self.index
    def press(self,now):
        if self.held:return False
        self.held=True;self.started=now
        self.index=(self.index+1)%len(PALETTE);self.start_index=self.index
        self.rgb=list(PALETTE[self.index])
        return True
    def release(self):
        was_held=self.held;self.held=False
        return was_held
    def tick(self,now):
        if not self.held or now<self.started+self.HOLD_DELAY:return False
        phase=(now-self.started-self.HOLD_DELAY)/self.LEG_SECONDS
        segment=int(phase);fraction=phase-segment
        self.index=(self.start_index+segment)%len(PALETTE)
        a=PALETTE[self.index];b=PALETTE[(self.index+1)%len(PALETTE)]
        rgb=[round(x+(y-x)*fraction) for x,y in zip(a,b)]
        changed=rgb!=self.rgb;self.rgb=rgb
        return changed
    def snapshot(self,event_ns):
        return {'index':self.index,'rgb':list(self.rgb),'held':self.held,'event_ns':event_ns}
