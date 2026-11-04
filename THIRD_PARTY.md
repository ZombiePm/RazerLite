# Third-party code and protocol references

RazerLite is distributed under **GPL-3.0-or-later**. See [LICENSE](LICENSE).

## OpenRazer for Windows

`vendor/openrazer_win` is an unmodified source copy of [Ar4ikov/openrazer-win](https://github.com/Ar4ikov/openrazer-win), version 1.5.2, commit `2423b2ef24b983a938280fd0ef9e4b7d38cb62ad`.

Copyright belongs to its upstream contributors. Its code is GPL-2.0-or-later; the original GPL text and the upstream CC-BY-SA text are preserved in `vendor/LICENSES`. Upstream's Python implementation and device/protocol tables build on [OpenRazer](https://github.com/openrazer/openrazer). Existing source notices remain intact.

## Mouse button protocol

`mouse_binding.py` implements the class 0x02 button-mapping protocol using the reference implementation in [GavinViney/openrazer-win](https://github.com/GavinViney/openrazer-win/blob/472a4faab5fa72339839f7f0d222c689d2886dd5/src/openrazer_win/mouse.py), commit `472a4faab5fa72339839f7f0d222c689d2886dd5`.

The reference is copyright (C) 2026 Gavin Viney, GPL-3.0-or-later. RazerLite uses GPL-3.0-or-later for the combined distribution, retaining the original upstream licenses. This is an independent project, not affiliated with Razer.
