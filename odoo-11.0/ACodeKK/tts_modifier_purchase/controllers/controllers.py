# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class PurchaseReportController(http.Controller):

    @http.route('/purchase_export_data_over', type='http', auth='user')
    def report_over(self, token, **post):
        purchase_obj = request.env['purchase.order']
        action = post.get('action',False)
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action == 'purchase.purchase_rfq':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Overview' + '.xlsx;')
                ]
            )
            purchase_obj.with_context(domain=domain).print_purchase_over(response)
        elif action == 'purchase.purchase_form_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Overview' + '.xlsx;')
                ]
            )
            purchase_obj.with_context(domain=domain).print_purchase_over(response, 'purchase')
        elif action == 'sale_purchase_returns.purchase_order_return_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Overview' + '.xlsx;')
                ]
            )
            purchase_obj.with_context(domain=domain).print_purchase_over(response, 'return')
        response.set_cookie('fileToken', token)
        return response

    @http.route('/purchase_export_data_detail', type='http', auth='user')
    def report_detail(self, token, **post):
        purchase_obj = request.env['purchase.order']
        action = post.get('action', False)
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action == 'purchase.purchase_rfq':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Detail' + '.xlsx;')
                ]
            )
            purchase_obj.with_context(domain=domain).print_purchase_detail(response)
        elif action == 'purchase.purchase_form_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Detail' + '.xlsx;')
                ]
            )
            purchase_obj.with_context(domain=domain).print_purchase_detail(response, 'purchase')
        elif action == 'sale_purchase_returns.purchase_order_return_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Detail' + '.xlsx;')
                ]
            )
            purchase_obj.with_context(domain=domain).print_purchase_detail(response, 'return')
        response.set_cookie('fileToken', token)
        return response
