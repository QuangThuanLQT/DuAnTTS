# -*- coding: utf-8 -*-
import StringIO

import xlsxwriter
from odoo import models, fields, api, exceptions
from datetime import datetime
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class product_interest(models.Model):
    _name = 'product.interest'
    _order = 'date_interest desc'

    partner_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.product', string='Product Name')
    date_interest = fields.Datetime(string='Thời gian')
    default_code = fields.Char(compute='_get_default', string='Reference')
    list_price = fields.Float(compute='_get_default', string='Giá bán')
    qty_available = fields.Integer(compute='_get_default', string='SL tổng trong kho')
    sp_ban_chua_giao = fields.Integer(compute='_get_default', string='SL bán chưa giao')
    sp_da_bao_gia = fields.Integer(compute='_get_default', string='SL đã báo giá')
    sp_co_the_ban = fields.Integer(compute='_get_default', string='SL có thể bán')
    product_active = fields.Boolean(string='Sản phẩm đang kinh doanh', compute='_get_default')

    trang_thai_hd = fields.Selection([
        ('active', 'Đang kinh doanh'),
        ('unactive', 'Ngừng kinh doanh')
    ], compute='get_trang_thai_hd', string='Trạng thái', store=True)

    @api.depends('product_id','product_id.active')
    def get_trang_thai_hd(self):
        for rec in self:
            if rec.product_id.active:
                rec.trang_thai_hd = 'active'
            else:
                rec.trang_thai_hd = 'unactive'

    @api.multi
    def _get_default(self):
        for r in self:
            r.default_code = r.product_id.default_code
            r.list_price = r.product_id.list_price
            r.qty_available = r.product_id.qty_available
            r.sp_ban_chua_giao = r.product_id.sp_ban_chua_giao
            r.sp_da_bao_gia = r.product_id.sp_da_bao_gia
            r.sp_co_the_ban = r.product_id.sp_co_the_ban
            r.product_active = r.product_id.active

    @api.multi
    def change_product_interest_list(self, product_tmpl_id, type):
        product_tmpl_id = self.env['product.template'].browse(product_tmpl_id)
        user_id = self.env['res.users'].browse(self._uid)
        if type == 'add':
            for product_id in product_tmpl_id.product_variant_ids:
                self.create({
                    'partner_id': user_id.partner_id.id,
                    'product_id': product_id.id,
                    'date_interest': datetime.now(),
                })
        else:
            product_interest_ids = self.search([('product_id.product_tmpl_id', '=', product_tmpl_id.id),('partner_id', '=', user_id.partner_id.id)])
            product_interest_ids.unlink()

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M:%S')
        return resuft

    @api.model
    def get_product_interest_search(self, product_name):
        if product_name:
            product_id = self.search([('product_id.default_code', '=like','%' + product_name + '%')])
            return product_id.ids

    @api.model
    def print_product_interest_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        product_interest_ids = self.env['product.interest'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Product Interested')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')


        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 35)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:I', 15)
        summary_header = ['STT', 'Reference', 'Product Name', 'Thời gian', 'Giá bán',
                          'SL Tổng trong kho', 'SL đã bán chưa giao', 'SL đã báo giá', 'SL có thể bán']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for product_interest_id in product_interest_ids:
            row += 1

            worksheet.write(row, 0, row)
            worksheet.write(row, 1, product_interest_id.default_code or '')
            worksheet.write(row, 2, product_interest_id.product_id.display_name or '')
            worksheet.write(row, 3, self._get_datetime_utc(product_interest_id.date_interest) if product_interest_id.date_interest else '')
            worksheet.write(row, 4, product_interest_id.product_id.list_price or '',body_bold_color_number)
            worksheet.write(row, 5, product_interest_id.product_id.qty_available or '')
            worksheet.write(row, 6, product_interest_id.product_id.sp_ban_chua_giao or 0)
            worksheet.write(row, 7, product_interest_id.product_id.sp_da_bao_gia or 0)
            worksheet.write(row, 8, product_interest_id.product_id.sp_co_the_ban or 0)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()