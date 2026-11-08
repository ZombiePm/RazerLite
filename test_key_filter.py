import unittest
from key_filter import KeyFilter

class KeyFilterTests(unittest.TestCase):
    def test_forwarded_press_not_captured_when_focus_enters_game(self):
        f=KeyFilter()
        self.assertEqual(f.handle(0x5b,0x100,False,True),(False,None))
        self.assertEqual(f.handle(0x5b,0x100,True,True),(False,None))
        self.assertEqual(f.handle(0x5b,0x101,True,True),(False,None))
        self.assertFalse(f.presses)

    def test_blocked_press_keeps_release_blocked_after_alt_tab(self):
        f=KeyFilter()
        self.assertEqual(f.handle(0x5b,0x100,True,True),(True,None))
        self.assertEqual(f.handle(0x5b,0x100,False,True),(True,None))
        self.assertEqual(f.handle(0x5b,0x101,False,True),(True,None))
        self.assertEqual(f.handle(0x5b,0x100,False,True),(False,None))

    def test_all_other_keys_pass_through_focus_changes(self):
        f=KeyFilter()
        for key in range(256):
            if key in (0x5b,0x5c,0x87):continue
            for message,gaming in ((0x100,True),(0x100,False),(0x101,False),(0x104,True),(0x105,False)):
                self.assertEqual(f.handle(key,message,gaming,True),(False,None))
        self.assertFalse(f.presses)

    def test_injected_release_does_not_finish_physical_press(self):
        f=KeyFilter()
        f.handle(0x5c,0x104,True,True)
        self.assertEqual(f.handle(0x5c,0x105,False,True,True),(False,None))
        self.assertEqual(f.handle(0x5c,0x105,False,True),(True,None))

    def test_color_release_survives_configuration_change(self):
        f=KeyFilter()
        self.assertEqual(f.handle(0x87,0x100,False,True),(True,True))
        self.assertEqual(f.handle(0x87,0x100,False,False),(True,None))
        self.assertEqual(f.handle(0x87,0x101,False,False),(True,False))
        self.assertEqual(f.handle(0x87,0x101,False,False),(False,None))

    def test_orphan_releases_pass_through(self):
        f=KeyFilter()
        for key in (0x5b,0x5c,0x87):self.assertEqual(f.handle(key,0x101,True,True),(False,None))

if __name__=='__main__':unittest.main()
