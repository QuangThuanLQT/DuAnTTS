# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class InventoryController(http.Controller):
    @http.route('/export_overview', type='http', auth='user')
    def inventory_export_over(self, token, **post):
        inventory_obj = request.env['stock.inventory']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Inventory Overview' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        inventory_obj.with_context(domain=domain).export_overview(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/export_detail', type='http', auth='user')
    def inventory_export_detail(self, token, **post):
        inventory_obj = request.env['stock.inventory']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Inventory Detail' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        inventory_obj.with_context(domain=domain).export_detail(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/export_not_sellable_product', type='http', auth='user')
    def report_export(self, token, **post):
        product_obj = request.env['product.product']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Not Sellable Products' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        product_obj.with_context(domain=domain).export_not_sellable_product(response)
        response.set_cookie('fileToken', token)
        return response
