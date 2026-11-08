"""Keep one forwarding decision for the entire press, including repeats and release.
Only Windows keys and the reserved color key are eligible for filtering.
No ordinary keystrokes are stored, changed or synthesized.
"""
WINDOWS_KEYS=frozenset((0x5b,0x5c))
COLOR_KEY=0x87
FILTERED_KEYS=WINDOWS_KEYS | {COLOR_KEY}
DOWN=frozenset((0x100,0x104))
UP=frozenset((0x101,0x105))

class KeyFilter:
    def __init__(self):
        self.presses={}

    def handle(self,key,message,gaming,color_enabled,injected=False):
        # Synthetic events must never consume or finish a physical press.
        if injected or key not in FILTERED_KEYS:
            return False,None
        if message in DOWN:
            if key in self.presses:
                return self.presses[key],None
            suppress=bool(gaming if key in WINDOWS_KEYS else color_enabled)
            self.presses[key]=suppress
            return suppress,True if key==COLOR_KEY and suppress else None
        if message in UP:
            suppress=self.presses.pop(key,False)
            return suppress,False if key==COLOR_KEY and suppress else None
        return False,None
