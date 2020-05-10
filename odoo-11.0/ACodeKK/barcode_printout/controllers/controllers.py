# -*- coding: utf-8 -*-
import barcode
from barcode.writer import BaseWriter, create_svg_object, SIZE, COMMENT, _set_attributes
import os
from odoo import http
from odoo.http import request

class SVGWriter(BaseWriter):

    def __init__(self):
        BaseWriter.__init__(self, self._init, self._create_module,
                            self._create_text, self._finish)
        self.compress = False
        self.dpi = 25
        self._document = None
        self._root = None
        self._group = None
        # self.module_height = 8

    def _init(self, code):
        width, height = self.calculate_size(len(code[0]), len(code), self.dpi)
        self._document = create_svg_object()
        self._root = self._document.documentElement
        attributes = dict(width=SIZE.format(width), height=SIZE.format(height))
        _set_attributes(self._root, **attributes)
        self._root.appendChild(self._document.createComment(COMMENT))
        # create group for easier handling in 3rd party software
        # like corel draw, inkscape, ...
        group = self._document.createElement('g')
        attributes = dict(id='barcode_group')
        _set_attributes(group, **attributes)
        self._group = self._root.appendChild(group)
        background = self._document.createElement('rect')
        attributes = dict(width='100%', height='100%',
                          style='fill:{0}'.format(self.background))
        _set_attributes(background, **attributes)
        self._group.appendChild(background)

    def _create_module(self, xpos, ypos, width, color):
        element = self._document.createElement('rect')
        attributes = dict(x=SIZE.format(xpos), y=SIZE.format(ypos),
                          width=SIZE.format(width),
                          height=SIZE.format(self.module_height),
                          style='fill:{0};'.format(color))
        _set_attributes(element, **attributes)
        self._group.appendChild(element)

    def _create_text(self, xpos, ypos):
        element = self._document.createElement('text')
        attributes = dict(x=SIZE.format(xpos), y=SIZE.format(ypos),
                          style='fill:{0};font-size:{1}pt;text-anchor:'
                                'middle;'.format(self.foreground,
                                                 self.font_size))
        _set_attributes(element, **attributes)
        # check option to override self.text with self.human (barcode as
        # human readable data, can be used to print own formats)
        if self.human != '':
            barcodetext = self.human
        else:
            barcodetext = self.text
        text_element = self._document.createTextNode(barcodetext)
        element.appendChild(text_element)
        self._group.appendChild(element)

    def _finish(self):
        if self.compress:
            return self._document.toxml(encoding='UTF-8')
        else:
            return self._document.toprettyxml(indent=4 * ' ', newl=os.linesep,
                                              encoding='UTF-8')

    def save(self, filename, output):
        return output
        # if self.compress:
        #     _filename = '{0}.svgz'.format(filename)
        #     f = gzip.open(_filename, 'wb')
        #     f.write(output)
        #     f.close()
        # else:
        #     _filename = '{0}.svg'.format(filename)
        #     with open(_filename, 'wb') as f:
        #         f.write(output)
        # return _filename

class BarcodePrintout(http.Controller):

    @http.route('/svg/barcode/<path:value>/<string:text>', type='http', auth="public")
    def svg_barcode(self, value, text):
        writer = SVGWriter()
        ean = barcode.get('code128', value, writer)
        output = ean.save(value, options={'module_height': 5, 'font_size': 7, 'module_width': 0.3}, text=text)

        return request.make_response(output, headers=[('Content-Type', 'image/svg+xml')])