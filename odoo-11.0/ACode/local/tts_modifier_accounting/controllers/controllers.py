# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import timedelta
import json


class SaleGrossProifitController(http.Controller):
    @http.route('/print_sale_gross_proifit_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        sale_obj = request.env['account.invoice.line']
        date = fields.Date.today()
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'sale gross proifit ' + date + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        sale_obj.with_context(domain=domain).print_sale_gross_proifit_excel(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_invoice_export_overview', type='http', auth='user')
    def report_invoice_export_overview(self, token, **post):
        inv_obj = request.env['account.invoice']
        date = fields.Date.today()
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Invoice Export Overview ' + date + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        inv_obj.with_context(domain=domain).print_invoice_export_overview(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_invoice_export_detail', type='http', auth='user')
    def report_invoice_export_detail(self, token, **post):
        inv_obj = request.env['account.invoice']
        date = fields.Date.today()
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Invoice Export Detail ' + date + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        inv_obj.with_context(domain=domain).print_invoice_export_detail(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_vendor_bill_export_overview', type='http', auth='user')
    def report_vendor_bill_export_overview(self, token, **post):
        inv_obj = request.env['account.invoice']
        date = fields.Date.today()
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Vendor bill Export Overview ' + date + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        inv_obj.with_context(domain=domain).print_vendor_bill_export_overview(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_vendor_bill_export_detail', type='http', auth='user')
    def report_vendor_bill_export_detail(self, token, **post):
        inv_obj = request.env['account.invoice']
        date = fields.Date.today()
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Vendor bill Export Detail ' + date + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        inv_obj.with_context(domain=domain).print_vendor_bill_export_detail(response)
        response.set_cookie('fileToken', token)
        return response
