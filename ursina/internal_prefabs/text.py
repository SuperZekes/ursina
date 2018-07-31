import sys
import time
sys.path.append("..")
from ursina import *
from panda3d.core import TransparencyAttrib

from os import path
from panda3d.core import Filename
from panda3d.core import TextNode
import textwrap

from ursina.entity import Entity

# note:
# <scale:n> tag doesn't work well in the middle of text.
# only good for titles for now.

class Text(Entity):

    def __init__(self, text=None, **kwargs):
        super().__init__()
        self.name = 'text'
        self.scale *= 0.25 * scene.editor_font_size

        self.setColorScaleOff()
        self.text_nodes = list()
        # self.align = 'left'
        self.origin = (-.5, .5)
        # self.font = 'VeraMono.ttf'
        temp_text_node = TextNode('')
        self._font = temp_text_node.getFont()

        self.line_height = 1

        self.text_colors = {
            '<default>' : color.text_color,
            '<white>' : color.white,
            '<smoke>' : color.smoke,
            '<light_gray>' : color.light_gray,
            '<gray>' : color.gray,
            '<dark_gray>' : color.dark_gray,
            '<black>' : color.black,

            '<red>' : color.red,
            '<orange>' : color.orange,
            '<yellow>' : color.yellow,
            '<lime>' : color.lime,
            '<green>' : color.green,
            '<turquoise>' : color.turquoise,
            '<cyan>' : color.cyan,
            '<azure>' : color.azure,
            '<blue>' : color.blue,
            '<violet>' : color.violet,
            '<magenta>' : color.magenta,
            '<pink>' : color.pink,
            }

        self.tag = '<default>'
        self.color = self.text_colors['<default>']
        self.scale_override = 1

        if text:
            self.text = text
        #     # self.line_height = 1
        for key, value in kwargs.items():
            setattr(self, key, value)


    @property
    def text(self):
        t = ''
        y = 0
        for tn in self.text_nodes:
            if y != tn.getZ():
                t += '\n'
                y = tn.getZ()
            t += tn.node().text

        return t


    @text.setter
    def text(self, text):
        self.raw_text = text
        text = str(text)
        for tn in self.text_nodes:
            tn.remove_node()
        self.text_nodes.clear()

        if not '<' in text:
            self.create_text_section(text)
            return

        sections = list()
        section = ''
        tag = '<default>'
        temp_text_node = TextNode('temp_text_node')
        temp_text_node.setFont(self.font)
        x = 0
        y = 0

        i = 0
        while i < len(text):
            char = text[i]
            if char == '\n':
                sections.append([section, tag, x, y])
                section = ''
                y -= 1
                x = 0
                i += 1

            elif char == '<': # find tag
                sections.append([section, tag, x, y])
                x += temp_text_node.calcWidth(section)
                section = ''

                tag = ''
                for j in range(len(text)-i):
                    tag += text[i+j]
                    if text[i+j] == '>':
                        i += j+1
                        break
            else:
                section += char
                i += 1

        sections.append([section, tag, x, y])

        for s in sections:
            # print('---', s)
            self.create_text_section(text=s[0], tag=s[1], x=s[2], y=s[3])

        # self.origin = self.origin   # recalculate text alignment after assigning new text
        self.align()

    def create_text_section(self, text, tag='<default>', x=0, y=0):
        self.text_node = TextNode('t')
        self.text_node_path = self.attachNewNode(self.text_node)
        try:
            self.text_node.setFont(self._font)
        except:
            print('default font')
            pass    # default font
        self.text_node.setText(text)
        self.text_node.setPreserveTrailingWhitespace(True)
        self.text_node_path.setPos(x * self.scale_override, 0, (y * self.line_height) - .75)
        self.text_nodes.append(self.text_node_path)

        if tag in self.text_colors:
            lightness = color.to_hsv(self.color)[2]
            self.color = self.text_colors[tag]
            if not tag == '<default>':
                if lightness > .8:
                    self.color = color.tint(self.color, .2)
                else:
                    self.color = color.tint(self.color, -.3)

            self.text_node.setTextColor(self.color)

        if tag.startswith('<scale:'):
            scale = tag.split(':')[1]
            self.scale_override = scale = float(scale[:-1])

        self.text_node_path.setScale(self.scale_override)


        return self.text_node

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        self._font = loader.loadFont(value)
        # _font.setRenderMode(TextFont.RMPolygon)
        self._font.setPixelsPerUnit(100)
        # print('FONT FILE:', self._font)
        self.text = self.raw_text   # update text

    @property
    def line_height(self):
        try:
            return self._line_height
        except:
            return 1

    @line_height.setter
    def line_height(self, value):
        self._line_height = value
        self.text = self.raw_text

    @property
    def width(self):
        if not hasattr(self, 'text'):
            return 0

        temp_text_node = TextNode('temp')
        temp_text_node.setFont(self.font)

        longest_line_length = 0
        for line in self.text.split('\n'):
            longest_line_length = max(longest_line_length, temp_text_node.calcWidth(line))

        return longest_line_length  * self.scale_x


    @property
    def height(self):
        return (len(self.lines) * self.line_height * self.scale_y)

    @property
    def lines(self):
        return [l for l in self.text.split('\n') if len(l) > 0]


    @property
    def wordwrap(self):
        if hasattr(self, '_wordwrap'):
            return self._wordwrap
        else:
            return 0

    @wordwrap.setter
    def wordwrap(self, value):
        self._wordwrap = value

        linelength = 0
        newstring = ''
        i = 0
        while i < (len(self.raw_text)):
            char = self.raw_text[i]

            if char == '<':
                for j in range(len(self.raw_text) - i):
                    if self.raw_text[i+j] == '>':
                        break
                    newstring += self.raw_text[i+j]
                i += j + 0  # don't count tags

            else:
                if char == '\n':
                    linelength = 0

                # find length of word
                for l in range(min(100, len(self.raw_text) - i)):
                    if self.raw_text[i+l] == ' ':
                        break

                if linelength + l > value:  # add linebreak
                    newstring += '\n'
                    linelength = 0

                newstring += char
                linelength += 1
                i += 1

        newstring = newstring.replace('\n>', '>\n')
        # print('--------------------\n', newstring)
        self.text = newstring


    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = value
        if self.text:
            self.text = self.raw_text

    def align(self):
        value = self.origin
        linewidths = [self.text_nodes[0].node().calcWidth(line) for line in self.lines]
        # center text on both axes
        for tn in self.text_nodes:
            linenumber = abs(int(tn.getZ() / self.line_height))
            tn.setX(tn.getX() - linewidths[linenumber] / 2)
            tn.setX(tn.getX() - linewidths[linenumber] / 2 * value[0] * 2)

            halfheight = len(linewidths) * self.line_height / 2
            tn.setZ(tn.getZ() + halfheight) # center vertically
            tn.setZ(tn.getZ() - (halfheight * value[1] * 2))

        if hasattr(self, '_background'):
            self._background.origin = value

    @property
    def background(self):
        if hasattr(self, '_background'):
            return self._background
        return None

    @background.setter
    def background(self, value):
        if value in (True, False, 1, 0):
            print('enable/disable background')
            if not hasattr(self, '_background'):
                self.model = 'quad'
                # self._background = Entity(
                #     parent = self,
                #     model = 'quad',
                #     color = color.black,
                #     # scale = (self.width, self.height)
                #     scale_x = self.width * 4,
                #     scale_y = self.height * 4,
                #     origin = self.origin,
                #     z = .01
                #     )
                # self._background.model.set_scale(1.25, 1, 3) # remember that y and z are swapped
                # self._background.scale *= 1.6

class TextBackground(Entity):
    pass

if __name__ == '__main__':
    app = Ursina()
    origin = Entity()
    origin.model = 'quad'
    origin.scale *= .05

    descr = '''<scale:1.0><orange>Title\n<scale:1>Increase <red>max health
<default>with 25% <yellow>and raise attack with\n<green>100 <default>for 2 turns.'''
    # descr = descr.strip().replace('\n', ' ')
    replacements = {
        'hp' : '<red>hp <default>',
        'max health ' : '<red>max health <default>',
        'attack ' : '<orange>attack <default>'
    }
    # descr = multireplace(descr, replacements)
    # descr = '<scale:1.5><orange>Title \n<scale:1>Increase <red>max health <default>with 25%.'
    # descr = 'test text'.upper()
    test = Text(descr)
    # test.font = 'VeraMono.ttf'
    test.font = 'Inconsolata-Regular.ttf'
    # test.model = 'quad'
    # test.origin = (0, 0)
    test.background = True
    # test.origin = (.5, .5)
    # test.line_height = 2
    camera.add_script('editor_camera')
    app.run()
