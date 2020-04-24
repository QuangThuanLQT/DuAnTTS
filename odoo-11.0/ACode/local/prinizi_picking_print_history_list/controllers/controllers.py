# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class PriniziPickingPrintHistoryList(http.Controller):

    @http.route('/picking_lich_su_in_export', type='http', auth='user')
    def report_lich_su_in_export(self, token, **post):
        picking_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Export lich su in' + '.xlsx;')
            ]
        )
        picking_obj.with_context(domain=domain).report_lich_su_in_excel(response)
        response.set_cookie('fileToken', token)
        return response