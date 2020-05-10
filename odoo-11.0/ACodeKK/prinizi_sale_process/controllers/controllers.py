# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class PriniziSaleProcess(http.Controller):

    @http.route('/prinizi_internal_sale_export_overview', type='http', auth='user')
    def prinizi_internal_sale_export_overview(self, token, **post):
        sale_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Internal sale export overview' + '.xlsx;')
            ]
        )
        sale_obj.with_context(domain=domain).internal_sale_export_overview(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/prinizi_internal_sale_export_detail', type='http', auth='user')
    def prinizi_internal_sale_export_detail(self, token, **post):
        sale_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Internal sale export detail' + '.xlsx;')
            ]
        )
        sale_obj.with_context(domain=domain).internal_sale_export_detail(response)
        response.set_cookie('fileToken', token)
        return response