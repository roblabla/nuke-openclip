# Nuke OpenClip

A simple plugin allowing Nuke to interact with OpenClip files.

## Installation

Add the following to your nuke config :

    from nukescripts import panels
    import sys
    sys.path.append('location/of/the/openclip/plugin')
    import add_clip
    panels.registerWidgetAsPanel('OpenClipWindow', 'Open Clip', 'im.cmc.OpenClipWindow')

## Standalone

The plugin can also be started in standalone mode, without nuke. Just run
`python add_clip.py` in your shell. You will need PySide installed.
