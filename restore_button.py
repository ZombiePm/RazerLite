"""Restore the saved physical button assignment, with RazerLite stopped."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent/'vendor'))
from openrazer_win.core.manager import DeviceManager
import mouse_binding
backup=pathlib.Path('C:/ProgramData/RazerLite/button-original.json')
backups=sorted(backup.parent.glob('button-original-profile-*.json'))
if backup.exists():backups.insert(0,backup)
if backups:
    with DeviceManager(bluetooth=False) as manager:
        device=manager.by_pid(0x99)
        if device is None:raise RuntimeError('Connect Basilisk V3 to restore its button')
        for saved in backups:mouse_binding.restore(device,saved)
        print('Original lower-button function restored')
