# -*- coding: utf-8 -*-
from odoo import http

# class VieterpCustomer(http.Controller):
#     @http.route('/vieterp_customer/vieterp_customer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vieterp_customer/vieterp_customer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vieterp_customer.listing', {
#             'root': '/vieterp_customer/vieterp_customer',
#             'objects': http.request.env['vieterp_customer.vieterp_customer'].search([]),
#         })

#     @http.route('/vieterp_customer/vieterp_customer/objects/<model("vieterp_customer.vieterp_customer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vieterp_customer.object', {
#             'object': obj
#         })