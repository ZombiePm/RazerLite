"""Immediate queue wakeup; retries sharing violations without losing the selection."""
import logging,queue,time
from color_cycle import ColorController,load_selection,save_selection,PALETTE

def run(events,path,stop):
    path.parent.mkdir(parents=True,exist_ok=True)
    try:selection=load_selection(path)
    except (OSError,ValueError,KeyError,TypeError):selection={'index':0,'rgb':PALETTE[0]}
    controller=ColorController(selection)
    pending=None;event_ns=0;warned=False
    while not stop.is_set():
        try:
            down,event_ns=events.get(timeout=.025 if controller.held or pending else .25)
            changed=controller.press(time.monotonic()) if down else controller.release()
            if changed:pending=controller.snapshot(event_ns)
        except queue.Empty:
            if controller.tick(time.monotonic()):pending=controller.snapshot(time.time_ns())
        if pending is not None:
            try:
                save_selection(path,pending);pending=None;warned=False
            except OSError:
                if not warned:logging.exception('Color save failed; retaining selection for retry')
                warned=True
                # Do not lose a click, stop processing input, or spin on a locked file.
                stop.wait(.01)
