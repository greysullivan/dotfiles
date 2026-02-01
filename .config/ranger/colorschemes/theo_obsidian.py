from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class THEO(ColorScheme):
    def use(self, context):
        fg = 255
        bg = 232
        if context.in_browser:
            if context.selected:
                fg = 252
                bg = 236
            elif context.directory:
                fg = 110   # steel-blue
        if context.in_titlebar:
            fg = 110
        return fg, bg
