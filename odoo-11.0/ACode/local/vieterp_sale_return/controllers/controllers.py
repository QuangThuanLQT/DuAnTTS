# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class VietErpSaleReturn(http.Controller):
    @http.route('/print_sale_return_excel', type='http', auth='user')
    def report_sale_return(self, token, **post):
        sale_return_obj = request.env['sale.order']
        action = post.get('action', False)
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action == 'sale.action_quotations':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Quotations overview' + '.xlsx;')
                ]
            )
            sale_return_obj.with_context(domain=domain).print_sale_return_excel(response)
        elif action == 'sale.action_orders':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Sale Orders Overview' + '.xlsx;')
                ]
            )
            sale_return_obj.with_context(domain=domain).print_sale_return_excel(response)
        elif action == 'vieterp_sale_return.order_return_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Order Return Overview' + '.xlsx;')
                ]
            )
            sale_return_obj.with_context(domain=domain).print_sale_return_excel(response, 'return')

        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_sale_return_detail_excel', type='http', auth='user')
    def report_sale_return_detail(self, token, **post):
        sale_return_detail_obj = request.env['sale.order']
        action = post.get('action', False)
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action == 'sale.action_quotations':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Quotations Detail' + '.xlsx;')
                ]
            )
            sale_return_detail_obj.with_context(domain=domain).print_sale_return_detail_excel(response)
        elif action == 'sale.action_orders':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Sale Orders Detail' + '.xlsx;')
                ]
            )
            sale_return_detail_obj.with_context(domain=domain).print_sale_return_detail_excel(response)
        elif action == 'vieterp_sale_return.order_return_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Order Return Detail' + '.xlsx;')
                ]
            )
            sale_return_detail_obj.with_context(domain=domain).print_sale_return_detail_excel(response, 'return')


        response.set_cookie('fileToken', token)
        return response