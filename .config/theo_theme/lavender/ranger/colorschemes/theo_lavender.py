from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class THEO(ColorScheme):
    def use(self, context):
        fg = 255
        bg = 232
        if context.in_browser:
            if context.selected:
                fg = 255
                bg = 238
            elif context.directory:
                fg = 183   # lavender
        if context.in_titlebar:
            fg = 183
        return fg, bg
