# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class PriniziSaleOrder(http.Controller):

    @http.route('/prinizi_sale_export_print', type='http', auth='user')
    def prinizi_so_export_print(self, token, **post):
        sale_obj = request.env['sale.order']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Don hang export print' + '.xlsx;')
            ]
        )
        sale_obj.with_context(domain=domain).prinizi_so_export_print(response)
        response.set_cookie('fileToken', token)
        return response