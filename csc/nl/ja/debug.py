#python-encoding: UTF-8

from csc.nl.ja.util  import *
import re

class JaDebug():
    ''' Handles Debug Output for csc.nl.ja
    Note: Not pretty.  Probably never will be.
    '''

    def __init__(self, colorize = True):
        self.colors = {}
        self.colors['header'] = '\033[092m' if colorize else ''
        self.colors['index']  = '\033[095m' if colorize else ''
        self.colors['error']  = '\033[091m' if colorize else ''
        self.colors['hl1']    = '\033[094m' if colorize else ''
        self.colors['hl2']    = '\033[096m' if colorize else ''
        self.colors['hl3']    = '\033[093m' if colorize else ''
        self.colors['hl4']    = '\033[090m' if colorize else ''
        self.colors['hl5']    = '\033[088m' if colorize else ''
        self.colors['off']    = '\033[0m'   if colorize else ''
        self.colors['normal'] = ''

    def header (self, string): return self.colors['header'] + ja_enc(string) + self.colors['off']
    def index  (self, string): return self.colors['index']  + ja_enc(string) + self.colors['off']
    def error  (self, string): return self.colors['error']  + ja_enc(string) + self.colors['off']
    def hl1    (self, string): return self.colors['hl1']    + ja_enc(string) + self.colors['off']
    def hl2    (self, string): return self.colors['hl2']    + ja_enc(string) + self.colors['off']
    def hl3    (self, string): return self.colors['hl3']    + ja_enc(string) + self.colors['off']
    def hl4    (self, string): return self.colors['hl4']    + ja_enc(string) + self.colors['off']
    def hl5    (self, string): return self.colors['hl5']    + ja_enc(string) + self.colors['off']
    def normal (self, string): return string

    @lazy_property
    def indent(self):
        return '      '

    styles = \
    {
        'none': \
        {
            'vert':         ' '.encode('utf-8'),
            'header':       '  '.encode('utf-8'),
            'bottom':       ' '.encode('utf-8'),
        },

        'single': \
        {
            'vert':         unichr(0x2502).encode('utf-8'),
            'header':       ( '' ).encode('utf-8'),
            'bottom':       ( unichr(0x2514) + unichr(0x2500) ).encode('utf-8'),
        },

        'double': \
        {
            'vert':         unichr(0x2551).encode('utf-8'),
            'header':       ( '' ).encode('utf-8'),
            'bottom':       ( unichr(0x2559) + unichr(0x2500) ).encode('utf-8'),
        }
    }

    def guide_area(self, lines, indent, op = None):
        ''' Adds guides for tree display '''
        if len(lines) == 0:
            return lines

        pos = len(self.indent) * indent

        op = op or {}
        if not op.has_key('style'):              op['style']   = 'single'
        if not self.styles.has_key(op['style']): op['style']   = 'single'
        if not op.has_key('color'):              op['color']   = self.colors['normal']

        style = self.styles[op['style']]

        def replace_char(string, index, char):
            char   = ja_enc(char)
            length = len(char.decode('utf-8'))

            if len(string) < index + 1:
                string = string + (' ' * (index - len(string)))

            return string[0:index] + op['color'] + char + self.colors['off'] + string[index + length:]

        for index, line in enumerate(lines):
            char = ' '

            if index == len(lines) - 1: char = style['bottom']
            else:                       char = style['vert']

            lines[index] = replace_char(line, pos, char)

    def header_line(self, line, indent, op = None):
        ''' Creates a header line in tree display '''
        op = op or {}
        if not op.has_key('style'): op['style'] = 'single'
        if not op.has_key('color'): op['color'] = self.colors['normal']

        style = self.styles[op['style']]

        i = ja_enc(self.indent * indent)

        return i + ( op['color'] + self.colors['off'] + line )

    @staticmethod
    def dump_lines_token(inst, indent, color):
        ''' Dumps an array of lines for token objects '''

        c = JaDebug(color)
        i = ja_enc(c.indent * indent) + '    '

        options = []
        lines   = []

        if inst.base_form:    lines.append(i + c.hl4(ja_enc('base_form:  ')) + c.hl1(inst.base_form))
        if inst.pos:          lines.append(i + c.hl4(ja_enc('pos:        ')) + c.hl1(inst.pos) + (" (" + c.hl1(inst.pos_string[len(inst.pos)+1:]) + ")" if inst.pos != inst.pos_string else ""))
        if inst.conj_form:    lines.append(i + c.hl4(ja_enc('conj_form:  ')) + c.hl1(inst.conj_form))
        if inst.infl_type:    lines.append(i + c.hl4(ja_enc('infl_type:  ')) + c.hl1(inst.infl_type))
        if inst.reading:      lines.append(i + c.hl4(ja_enc('reading:    ')) + c.hl1(inst.reading) + (" (" + c.hl1(inst.prounciation) + ")" if inst.prounciation and inst.prounciation != inst.reading else ""))

        guide_op = \
        {
            'color':  c.colors['normal'],
            'style':  'single'
        }
        c.guide_area(lines, indent, guide_op)

        prop = filter(lambda v: re.match('is_', v[0]) and v[1], inst.get_properties().items())
        prop.sort()
        prop_str = '{' + ', '.join([ c.hl4(x[0][3:].upper()) for x in prop ]) + '}'

        guide_op['color'] = c.colors['header']
        header            = c.header_line((c.error if inst.is_stopword else c.header)(inst.node_type + ": ") + "『" + c.hl3(str(inst)) + "』 " + prop_str, indent, guide_op)
        lines.insert(0, header)

        return lines

    @staticmethod
    def dump_lines_word(inst, indent, color):
        ''' Dumps an array of lines for word objects '''

        c = JaDebug(color)
        i = ja_enc(c.indent * indent)

        lines = []
        for child in inst.children:
            lines += child.dump_lines(indent + 1, color)
            lines.append('')

        guide_op = \
        {
            'color':   c.colors['hl3'] if ( len(inst.children) > 1 ) else c.colors['normal'],
            'style':   'double'        if ( len(inst.children) > 1 ) else 'single',
        }
        c.guide_area(lines, indent, guide_op)

        prop = filter(lambda v: re.match('is_', v[0]) and v[1], inst.get_properties().items())
        prop.sort()
        prop_str = '{' + ', '.join([ c.hl4(x[0][3:].upper()) for x in prop ]) + '}'

        guide_op['color'] = c.colors['header']
        header            = c.header_line((c.error if inst.is_stopword else c.header)(inst.node_type + ": ") + "『" + c.hl3(str(inst)) + "』 " + prop_str, indent, guide_op)
        lines.insert(0, header)

        return lines

    @staticmethod
    def dump_lines_chunk(inst, indent, color):
        ''' Dumps an array of lines for chunk objects '''

        c = JaDebug(color)
        i = ja_enc(c.indent * indent)

        lines = []
        for child in inst.children:
            lines += child.dump_lines(indent + 1, color)
            lines.append('')

        guide_op = \
        {
            'color': c.colors['hl3'] if ( len(inst.children) > 1 ) else c.colors['normal'],
            'style': 'double'        if ( len(inst.children) > 1 ) else 'single',
        }
        c.guide_area(lines, indent, guide_op)

        prop = filter(lambda v: re.match('is_', v[0]) and v[1], inst.get_properties().items())
        prop.sort()
        prop_str = '{' + ', '.join([ c.hl4(x[0][3:].upper()) for x in prop ]) + '}'

        guide_op['color'] = c.colors['header']
        header            = c.header_line((c.error if inst.is_stopword else c.header)(inst.node_type + ": ") + "『" + c.hl3(str(inst)) + "』 " + prop_str, indent, guide_op)
        lines.insert(0, header)

        return lines

    @staticmethod
    def dump_lines_utterance(inst, indent, color):
        ''' Dumps an array of lines for utterance objects '''

        c = JaDebug(color)
        i = ja_enc(c.indent * indent)

        lines = []
        for child in inst.children:
            lines += child.dump_lines(indent + 1, color)
            lines.append('')

        guide_op = \
        {
            'color':   c.colors['hl3'] if ( len(inst.children) > 1 ) else c.colors['normal'],
            'style':   'double'        if ( len(inst.children) > 1 ) else 'single',
        }
        c.guide_area(lines, indent, guide_op)

        guide_op['color'] = c.colors['header']
        header            = c.header_line((c.error if inst.is_stopword else c.header)(inst.node_type + ": ") + "『" + c.hl3(str(inst)) + "』", indent, guide_op)
        lines.insert(0, header)

        return lines

