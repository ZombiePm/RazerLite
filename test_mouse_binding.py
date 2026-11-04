import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent/'vendor'))
import mouse_binding as b
from openrazer_win.protocol.report import RazerReport
class Device:
 def __init__(self):
  self.transport=self;self.maps={};self.writes=[]
  for p in range(6):
   self.maps[p,96]=bytes([p,96,1,6,1,6,0,0,0,0])
   self.maps[p,106]=bytes([p,106,1,18,1,1,0,0,0,0])
 def send_payload(self,r,want):
  response=RazerReport()
  if r.command_class==5:response.arguments[0]=1
  elif r.command_id==0x8c:
   response.arguments[:10]=self.maps[tuple(r.arguments[:2])]
  else:
   self.writes.append(bytes(r.arguments[:10]))
   self.maps[tuple(r.arguments[:2])]=bytes(r.arguments[:10])
  return response
class Tests(unittest.TestCase):
 def test_active_profile_and_restore(self):
  d=Device();original=dict(d.maps)
  self.assertEqual(b.active_profile(d),1)
  with tempfile.TemporaryDirectory() as temp:
   path=pathlib.Path(temp)/'backup.json'
   b.ensure(d,path,1)
   self.assertEqual(d.maps[1,96][3:7],bytes([2,2,0,0x73]))
   self.assertEqual(d.maps[0,96],original[0,96])
   self.assertEqual(d.maps[1,106],original[1,106])
   count=len(d.writes);b.ensure(d,path,1);self.assertEqual(len(d.writes),count)
   b.restore(d,path)
   self.assertEqual(d.maps[1,96][3:],original[1,96][3:])
if __name__=='__main__':unittest.main()
