# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class PickingReportController(http.Controller):

    @http.route('/receipt_history_export_data', type='http', auth='user')
    def receipt_history_export_detail(self, token, **post):
        pikcing_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Lich su nhan hang' + '.xlsx;')
            ]
        )
        pikcing_obj.with_context(domain=domain).print_receipt_history_excel(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/picking_receipt_export_data', type='http', auth='user')
    def report_picking_receipt_detail(self, token, **post):
        pikcing_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Export Receipt time log' + '.xlsx;')
            ]
        )
        pikcing_obj.with_context(domain=domain).print_picking_receipt_excel(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/picking_delivery_export_data', type='http', auth='user')
    def report_picking_delivery_detail(self, token, **post):
        pikcing_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Export Delivery time log' + '.xlsx;')
            ]
        )
        pikcing_obj.with_context(domain=domain).print_delivery_export_excel(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/picking_export_overview', type='http', auth='user')
    def picking_export_over(self, token, **post):
        picking_obj = request.env['income.inventory']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Income_Inventory' + '.xlsx;')
            ]
        )
        picking_obj.with_context(domain=domain).export_over_data(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/exported_picking_overview', type='http', auth='user')
    def exported_picking_overview(self, token, **post):
        picking_obj = request.env['stock.picking']
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Exported History' + '.xlsx;')
            ]
        )
        picking_obj.with_context(domain=domain).print_exported_overview(response)
        response.set_cookie('fileToken', token)
        return response
