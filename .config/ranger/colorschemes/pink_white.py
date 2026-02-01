# Pink and White colorscheme for ranger
# Matches fastfetch icon with pink and white accents

from __future__ import (absolute_import, division, print_function)

from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import (
    black, blue, cyan, green, magenta, red, white, yellow, default,
    normal, bold, reverse, dim, BRIGHT,
    default_colors,
)


class pink_white(ColorScheme):
    progress_bar_color = magenta

    def use(self, context):
        fg, bg, attr = default_colors

        if context.reset:
            return default_colors

        elif context.in_browser:
            if context.selected:
                attr = reverse
                fg = magenta
                fg += BRIGHT
            else:
                attr = normal
                fg = white
            if context.empty or context.error:
                fg = red
                attr |= bold
            if context.border:
                fg = magenta
            if context.media:
                if context.image:
                    fg = magenta
                    fg += BRIGHT
                else:
                    fg = magenta
            if context.container:
                fg = magenta
                attr |= bold
            if context.directory:
                attr |= bold
                fg = magenta
                fg += BRIGHT
            elif context.executable and not \
                    any((context.media, context.container,
                         context.fifo, context.socket)):
                attr |= bold
                fg = white
                fg += BRIGHT
            if context.socket:
                attr |= bold
                fg = magenta
            if context.fifo or context.device:
                fg = white
                if context.device:
                    attr |= bold
                    fg += BRIGHT
            if context.link:
                fg = white if context.good else magenta
                fg += BRIGHT
            if context.tag_marker and not context.selected:
                attr |= bold
                fg = magenta
                fg += BRIGHT
            if not context.selected and (context.cut or context.copied):
                attr |= bold
                fg = magenta
            if context.main_column:
                if context.selected:
                    attr |= bold
                if context.marked:
                    attr |= bold
                    fg = magenta
                    fg += BRIGHT
            if context.badinfo:
                if attr & reverse:
                    bg = red
                else:
                    fg = red

            if context.inactive_pane:
                fg = white
                attr |= dim

        elif context.in_titlebar:
            attr |= bold
            if context.hostname:
                fg = magenta if context.good else red
                fg += BRIGHT
            elif context.directory:
                fg = magenta
                fg += BRIGHT
            elif context.tab:
                if context.good:
                    fg = white
                    bg = magenta
            elif context.link:
                fg = white
                fg += BRIGHT

        elif context.in_statusbar:
            if context.permissions:
                if context.good:
                    fg = white
                elif context.bad:
                    fg = red
            if context.marked:
                attr |= bold | reverse
                fg = magenta
                fg += BRIGHT
            if context.frozen:
                attr |= bold | reverse
                fg = white
                fg += BRIGHT
            if context.message:
                if context.bad:
                    attr |= bold
                    fg = red
                    fg += BRIGHT
                else:
                    fg = white
            if context.loaded:
                bg = self.progress_bar_color
            if context.vcsinfo:
                fg = magenta
                attr &= ~bold
            if context.vcscommit:
                fg = white
                attr &= ~bold
            if context.vcsdate:
                fg = magenta
                attr &= ~bold

        if context.text:
            if context.highlight:
                attr |= reverse
                fg = magenta
                fg += BRIGHT

        if context.in_taskview:
            if context.title:
                fg = magenta
                fg += BRIGHT

            if context.selected:
                attr |= reverse

            if context.loaded:
                if context.selected:
                    fg = self.progress_bar_color
                else:
                    bg = self.progress_bar_color

        if context.vcsfile and not context.selected:
            attr &= ~bold
            if context.vcsconflict:
                fg = red
            elif context.vcsuntracked:
                fg = white
            elif context.vcschanged:
                fg = magenta
            elif context.vcsunknown:
                fg = red
            elif context.vcsstaged:
                fg = magenta
                fg += BRIGHT
            elif context.vcssync:
                fg = white
            elif context.vcsignored:
                fg = default

        elif context.vcsremote and not context.selected:
            attr &= ~bold
            if context.vcssync or context.vcsnone:
                fg = white
            elif context.vcsbehind:
                fg = red
            elif context.vcsahead:
                fg = magenta
            elif context.vcsdiverged:
                fg = magenta
                fg += BRIGHT
            elif context.vcsunknown:
                fg = red

        return fg, bg, attr
