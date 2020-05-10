# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json

class VieterpProduct(http.Controller):
    @http.route('/print_product_excel', type='http', auth='user')
    def print_product_variant(self, token, **post):
        product_variant_obj = request.env['product.product']

        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Bien the san pham' + '.xlsx;')
            ]
        )
        product_variant_obj.with_context(domain=domain).print_product_excel(response)

        response.set_cookie('fileToken', token)
        return response
