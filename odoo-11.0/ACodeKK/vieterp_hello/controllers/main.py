# -*- coding: utf-8 -*-
from odoo import http

class VietERP(http.Controller):
    @http.route('/vieterp/hello/', auth='public')
    def hello(self, **kw):
        return "Hello, world"