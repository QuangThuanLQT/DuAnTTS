# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import StringIO
import xlsxwriter
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class account_invoice_ihr(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        vals['date_invoice'] = fields.Datetime.now()
        result = super(account_invoice_ihr, self).create(vals)
        return result

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.model
    def print_invoice_export_overview(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        invoice_ids = self.env['account.invoice'].search(domain)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Invoice Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Customer Code', 'Customers', 'Phone Customers', 'Invoice Date', 'Order Date',
                          'Number', 'Salesperson', 'Dua Date', 'Source Document','Total','Account Due','Status']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for invoice_id in invoice_ids:
            row += 1
            sale_id = False
            if 'RT0' in invoice_id.origin:
                sale_id = self.env['sale.order'].search([('name', '=', invoice_id.origin)], limit=1)
            worksheet.write(row, 0, invoice_id.partner_id.ref or '', text_style)
            worksheet.write(row, 1, invoice_id.partner_id.name or '', text_style)
            worksheet.write(row, 2, invoice_id.partner_id.phone or invoice_id.partner_id.mobile or '', text_style)
            worksheet.write(row, 3, datetime.strptime(invoice_id.date_invoice, "%Y-%m-%d").strftime("%d/%m/%Y") if invoice_id.date_invoice else '' or '', text_style)
            worksheet.write(row, 4, datetime.strptime(invoice_id.date_order, "%Y-%m-%d").strftime("%d/%m/%Y") if invoice_id.date_order else '' or '', text_style)
            worksheet.write(row, 5, invoice_id.number or '', text_style)
            worksheet.write(row, 6, sale_id.create_uid.name or '' if sale_id else invoice_id.user_id.name or '', text_style)
            worksheet.write(row, 7, datetime.strptime(invoice_id.date_due, "%Y-%m-%d").strftime("%d/%m/%Y") if invoice_id.date_due else '' or '', text_style)
            worksheet.write(row, 8, invoice_id.origin or '', text_style)
            worksheet.write(row, 9, invoice_id.amount_total_signed or 0, body_bold_color_number)
            worksheet.write(row, 10, invoice_id.residual_signed or 0, body_bold_color_number)
            worksheet.write(row, 11, dict(invoice_id.fields_get(['state'])['state']['selection'])[invoice_id.state] or '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_invoice_export_detail(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        invoice_ids = self.env['account.invoice'].search(domain)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Invoice Export Detail')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:R', 20)
        worksheet.set_column('N:N', 40)

        summary_header = ['Customer Code', 'Customers', 'Phone Customers', 'Invoice Date', 'Order Date',
                          'Number', 'Salesperson', 'Dua Date', 'Source Document', 'Total', 'Account Due', 'Status',
                          'Product variant Code', 'Product Variant Name', 'Quantity', 'Unit Price', 'Cost', 'Proifit']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for invoice_id in invoice_ids:
            for line in invoice_id.invoice_line_ids:
                row += 1
                sale_id = False
                if 'RT0' in invoice_id.origin:
                    sale_id = self.env['sale.order'].search([('name', '=', invoice_id.origin)], limit=1)
                worksheet.write(row, 0, invoice_id.partner_id.ref or '', text_style)
                worksheet.write(row, 1, invoice_id.partner_id.name or '', text_style)
                worksheet.write(row, 2, invoice_id.partner_id.phone or invoice_id.partner_id.mobile or '', text_style)
                worksheet.write(row, 3, datetime.strptime(invoice_id.date_invoice, "%Y-%m-%d").strftime("%d/%m/%Y") if invoice_id.date_invoice else '' or '', text_style)
                worksheet.write(row, 4, datetime.strptime(invoice_id.date_order, "%Y-%m-%d").strftime("%d/%m/%Y") if invoice_id.date_order else '' or '', text_style)
                worksheet.write(row, 5, invoice_id.number or '', text_style)
                # worksheet.write(row, 6, invoice_id.user_id.name or '', text_style)
                worksheet.write(row, 6, sale_id.create_uid.name or '' if sale_id else invoice_id.user_id.name or '', text_style)
                worksheet.write(row, 7, datetime.strptime(invoice_id.date_due, "%Y-%m-%d").strftime("%d/%m/%Y") if invoice_id.date_due else '' or '', text_style)
                worksheet.write(row, 8, invoice_id.origin or '', text_style)
                worksheet.write(row, 9, invoice_id.amount_total_signed or 0, body_bold_color_number)
                worksheet.write(row, 10, invoice_id.residual_signed or 0, body_bold_color_number)
                worksheet.write(row, 11,
                                dict(invoice_id.fields_get(['state'])['state']['selection'])[invoice_id.state] or '',
                                text_style)
                worksheet.write(row, 12, line.product_id.default_code or '', text_style)
                worksheet.write(row, 13, line.product_name_sub or '', text_style)
                worksheet.write(row, 14, -line.quantity if invoice_id.type == 'out_refund' else line.quantity or 0, body_bold_color_number)
                worksheet.write(row, 15, line.price_unit or 0, body_bold_color_number)
                worksheet.write(row, 16, line.cost_product_variant or 0, body_bold_color_number)
                worksheet.write(row, 17, line.price_unit - line.cost_product_variant or 0, body_bold_color_number)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_vendor_bill_export_overview(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        invoice_ids = self.env['account.invoice'].search(domain)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Vendor Bill Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Vendor Code', 'Vendor Name', 'Bill Date', 'Number', 'Dua Date', 'Source Document', 'Total', 'To Pay', 'Status']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for invoice_id in invoice_ids:
            row += 1
            # sale_id = False
            # if 'RT0' in invoice_id.origin:
            #     sale_id = self.env['sale.order'].search([('name', '=', invoice_id.origin)], limit=1)
            worksheet.write(row, 0, invoice_id.partner_id.ref or '', text_style)
            worksheet.write(row, 1, invoice_id.partner_id.name or '', text_style)
            worksheet.write(row, 2, datetime.strptime(invoice_id.date_invoice, "%Y-%m-%d").strftime(
                "%d/%m/%Y") if invoice_id.date_invoice else '' or '', text_style)
            worksheet.write(row, 3, invoice_id.number or '', text_style)
            worksheet.write(row, 4, datetime.strptime(invoice_id.date_due, "%Y-%m-%d").strftime(
                "%d/%m/%Y") if invoice_id.date_due else '' or '', text_style)
            worksheet.write(row, 5, invoice_id.origin or '', text_style)
            worksheet.write(row, 6, invoice_id.amount_total or 0, body_bold_color_number)
            worksheet.write(row, 7, invoice_id.residual_signed or 0, body_bold_color_number)
            worksheet.write(row, 8,
                            dict(invoice_id.fields_get(['state'])['state']['selection'])[invoice_id.state] or '',
                            text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_vendor_bill_export_detail(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        invoice_ids = self.env['account.invoice'].search(domain)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Invoice Export Detail')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:R', 20)
        worksheet.set_column('N:N', 40)

        summary_header = ['Vendor Code', 'Vendor name', 'Bill Date', 'Number', 'Dua Date', 'Source Document', 'Total', 'To Pay', 'Status',
                          'Product variant Code', 'Product Variant Name', 'Quantity', 'Unit Price', 'Bill Price','Tax']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for invoice_id in invoice_ids:
            for line in invoice_id.invoice_line_ids:
                row += 1
                sale_id = False
                if 'RT0' in invoice_id.origin:
                    sale_id = self.env['sale.order'].search([('name', '=', invoice_id.origin)], limit=1)
                worksheet.write(row, 0, invoice_id.partner_id.ref or '', text_style)
                worksheet.write(row, 1, invoice_id.partner_id.name or '', text_style)
                worksheet.write(row, 2, datetime.strptime(invoice_id.date_invoice, "%Y-%m-%d").strftime(
                    "%d/%m/%Y") if invoice_id.date_invoice else '' or '', text_style)
                worksheet.write(row, 3, invoice_id.number or '', text_style)
                worksheet.write(row, 4, datetime.strptime(invoice_id.date_due, "%Y-%m-%d").strftime(
                    "%d/%m/%Y") if invoice_id.date_due else '' or '', text_style)
                worksheet.write(row, 5, invoice_id.origin or '', text_style)
                worksheet.write(row, 6, invoice_id.amount_total or 0, body_bold_color_number)
                worksheet.write(row, 7, invoice_id.residual_signed or 0, body_bold_color_number)
                worksheet.write(row, 8,
                                dict(invoice_id.fields_get(['state'])['state']['selection'])[invoice_id.state] or '',
                                text_style)
                worksheet.write(row, 9, line.product_id.default_code or '', text_style)
                worksheet.write(row, 10, line.product_name_sub or '', text_style)
                worksheet.write(row, 11, -line.quantity if invoice_id.type == 'in_refund' else line.quantity or 0,
                                body_bold_color_number)
                worksheet.write(row, 12, line.price_unit or 0, body_bold_color_number)
                worksheet.write(row, 13, line.price_subtotal or 0, body_bold_color_number)
                worksheet.write(row, 14, line.invoice_line_tax_ids[0].name if line.invoice_line_tax_ids else '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

class res_partner_inherit(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_origin_text_search(self, name, field, model):
        record_ids = []
        if field == 'origin' and model != 'account.invoice':
            self.env.cr.execute(
                "select id from stock_picking where UPPER(origin) LIKE '%s'" % ("%" + name.upper() + "%"))
        if field == 'origin' and model == 'account.invoice':
            self.env.cr.execute("select id from account_invoice where origin LIKE '%s'" % ("%" + name + "%"))
        if field == 'number_origin':
            self.env.cr.execute("select id from account_invoice where number_origin LIKE '%s'" % ("%" + name + "%"))
        if field == 'note' and model == 'stock.picking':
            self.env.cr.execute("select id from stock_picking where UPPER(note) LIKE '%s'" % ("%" + name.upper() + "%"))
        if field == 'note' and model == 'sale.order':
            self.env.cr.execute("select id from sale_order where UPPER(note) LIKE '%s'" % ("%" + name.upper() + "%"))
        if field == 'notes' and model == 'purchase.order':
            self.env.cr.execute(
                "select id from purchase_order where UPPER(notes) LIKE '%s'" % ("%" + name.upper() + "%"))
        res_trans = self.env.cr.fetchall()
        for line in res_trans:
            record_ids.append(line[0])
        return record_ids

