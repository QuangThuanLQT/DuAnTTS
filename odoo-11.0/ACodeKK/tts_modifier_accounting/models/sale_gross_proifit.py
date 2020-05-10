# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import StringIO
import xlsxwriter
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class sale_gross_proifit(models.Model):
    _inherit = 'account.invoice.line'

    date = fields.Datetime(related="invoice_id.create_date", store=True)
    invoice_code = fields.Char(related="invoice_id.number")
    total_bill = fields.Monetary(related="invoice_id.amount_total")
    internal_reference = fields.Char(related="product_id.default_code")
    cost_product_variant = fields.Float(compute='get_cost_product_variant')
    gross_proifit = fields.Float(compute = "_get_gross_proifit")
    product_name_sub = fields.Char(compute="_get_product_name")

    @api.multi
    def _get_product_name(self):
        for rec in self:
            product_name_sub = "[%s] " % (rec.product_id.default_code)
            if product_name_sub in rec.product_id.display_name:
                rec.product_name_sub = rec.product_id.display_name.replace(product_name_sub,'')
            else:
                rec.product_name_sub = rec.product_id.display_name

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('sale_gross_proifit', False):
            res = super(sale_gross_proifit, self).search_read(domain=domain, fields=fields, offset=offset,
                                                      limit=limit, order=order)

            def convertVals(x):
                if x.get('id', False):
                    invoice_line_id = self.env['account.invoice.line'].browse(x.get('id', False))
                    if invoice_line_id.invoice_id.type in ('out_refund'):
                        x['quantity'] = -x['quantity']
                return x

            res = map(lambda x: convertVals(x), res)
            return res
        return super(sale_gross_proifit, self).search_read(domain=domain, fields=fields, offset=offset,
                                                   limit=limit, order=order)

    @api.multi
    def get_cost_product_variant(self):
        for rec in self:
            order_id = rec.sale_line_ids.mapped('order_id')
            if order_id:
                order_id = order_id[0]
                if order_id.sale_order_return:
                    if order_id.sale_order_return_ids:
                        order_return = order_id.sale_order_return_ids[0]
                        if order_return.invoice_ids:
                            invoice_id = order_return.invoice_ids[0]
                            rec.cost_product_variant = rec.product_id.get_history_price(rec.company_id.id, invoice_id.create_date)
                        else:
                            rec.cost_product_variant = rec.product_id.get_history_price(rec.company_id.id,
                                                                                        order_return.confirmation_date)
                    else:
                        rec.cost_product_variant = rec.product_id.get_history_price(rec.company_id.id, rec.create_date)
                else:
                    rec.cost_product_variant = rec.product_id.get_history_price(rec.company_id.id, rec.create_date)
            else:
                rec.cost_product_variant = rec.product_id.get_history_price(rec.company_id.id, rec.create_date)

    @api.multi
    def _get_gross_proifit(self):
        for rec in self:
            rec.gross_proifit = rec.price_unit - rec.cost_product_variant

    @api.model
    def print_sale_gross_proifit_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sale gross proifit')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Thời gian', 'Mã Invoice', 'Tổng tiền hóa đơn', 'Mã hàng', 'Tên hàng',
                          'Số lượng', 'Giá bán/SP', 'Giá vốn/SP', 'Lãi gộp/SP']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for invoice_line_id in invoice_line_ids:
            row += 1
            quantity = invoice_line_id.quantity
            if invoice_line_id.invoice_id.type in ("out_refund"):
                quantity = -1 * invoice_line_id.quantity
            worksheet.write(row, 0, self.env['account.invoice']._get_datetime_utc(invoice_line_id.date) if invoice_line_id.date else '')
            worksheet.write(row, 1, invoice_line_id.invoice_code or '')
            worksheet.write(row, 2, invoice_line_id.total_bill,body_bold_color_number)
            worksheet.write(row, 3, invoice_line_id.internal_reference or '')
            worksheet.write(row, 4, invoice_line_id.product_name_sub)
            worksheet.write(row, 5, quantity)
            worksheet.write(row, 6, invoice_line_id.price_unit,body_bold_color_number)
            worksheet.write(row, 7, invoice_line_id.cost_product_variant,body_bold_color_number)
            worksheet.write(row, 8, invoice_line_id.gross_proifit,body_bold_color_number)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()