import tempfile,pathlib,unittest
from color_cycle import PALETTE,load_index,advance,PressLatch
class Tests(unittest.TestCase):
 def test_persistence_wrap_and_invalid(self):
  with tempfile.TemporaryDirectory() as temp:
   p=pathlib.Path(temp)/'color.json'
   self.assertEqual(load_index(p),0)
   for i in range(1,15):self.assertEqual(advance(p),i%len(PALETTE))
   p.write_text('{"index": -1}');self.assertEqual(load_index(p),0)
   p.write_text('broken');self.assertEqual(load_index(p),0)
 def test_hold_and_release(self):
  latch=PressLatch()
  self.assertTrue(latch.feed(True));self.assertFalse(latch.feed(True))
  self.assertFalse(latch.feed(False));self.assertTrue(latch.feed(True))

class ControllerTests(unittest.TestCase):
 def test_tap_hold_and_stop(self):
  from color_cycle import ColorController
  c=ColorController({'index':0,'rgb':PALETTE[0]})
  self.assertTrue(c.press(10));self.assertEqual(c.rgb,PALETTE[1])
  self.assertFalse(c.press(10.1));self.assertFalse(c.tick(10.2))
  self.assertTrue(c.tick(11.05));mid=list(c.rgb)
  self.assertNotEqual(mid,PALETTE[1]);self.assertNotEqual(mid,PALETTE[2])
  c.release();self.assertFalse(c.tick(50));self.assertEqual(c.rgb,mid)
 def test_retry_does_not_lose_click(self):
  import queue,threading,time
  from unittest.mock import patch
  import color_worker
  from color_cycle import load_selection,save_selection
  with tempfile.TemporaryDirectory() as temp:
   p=pathlib.Path(temp)/'color.json';events=queue.SimpleQueue();stop=threading.Event()
   calls=[]
   def save(path,value):
    calls.append(value)
    if len(calls)<3:raise PermissionError('synthetic sharing violation')
    save_selection(path,value)
   with patch.object(color_worker,'save_selection',save),patch.object(color_worker.logging,'exception'):
    t=threading.Thread(target=color_worker.run,args=(events,p,stop));t.start()
    events.put((True,time.time_ns()));events.put((False,time.time_ns()))
    deadline=time.monotonic()+2
    while not p.exists() and time.monotonic()<deadline:time.sleep(.01)
    stop.set();t.join(1)
   self.assertTrue(p.exists());self.assertEqual(load_selection(p)['index'],1)
   self.assertFalse(load_selection(p)['held'])

if __name__=='__main__':unittest.main()
