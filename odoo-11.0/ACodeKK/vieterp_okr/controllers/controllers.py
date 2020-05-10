# -*- coding: utf-8 -*-
from odoo import http

# class VieterpOkr(http.Controller):
#     @http.route('/vieterp_okr/vieterp_okr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vieterp_okr/vieterp_okr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vieterp_okr.listing', {
#             'root': '/vieterp_okr/vieterp_okr',
#             'objects': http.request.env['vieterp_okr.vieterp_okr'].search([]),
#         })

#     @http.route('/vieterp_okr/vieterp_okr/objects/<model("vieterp_okr.vieterp_okr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vieterp_okr.object', {
#             'object': obj
#         })