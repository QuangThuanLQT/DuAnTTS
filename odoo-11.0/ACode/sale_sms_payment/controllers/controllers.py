# -*- coding: utf-8 -*-
from odoo import http

# class SaleSmsPayment(http.Controller):
#     @http.route('/sale_sms_payment/sale_sms_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_sms_payment/sale_sms_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_sms_payment.listing', {
#             'root': '/sale_sms_payment/sale_sms_payment',
#             'objects': http.request.env['sale_sms_payment.sale_sms_payment'].search([]),
#         })

#     @http.route('/sale_sms_payment/sale_sms_payment/objects/<model("sale_sms_payment.sale_sms_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_sms_payment.object', {
#             'object': obj
#         })