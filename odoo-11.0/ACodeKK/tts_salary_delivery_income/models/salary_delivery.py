# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.exceptions import UserError

class tts_salary_delivery_income(models.Model):
    _name = 'salary.delivery.income'

    default_code = fields.Char(readonly=True)
    month = fields.Char(readonly=True)
    name = fields.Char(readonly=True)
    sl_hang_giao = fields.Float(digits=(16, 1), compute='get_tong_thu_nhap', store=True, readonly=True)
    sl_gh_bt = fields.Float(digits=(16, 1), readonly=True)
    sl_gh_tc = fields.Float(digits=(16, 1), readonly=True)
    thu_nhap = fields.Float(digits=(16, 0), readonly=True)
    phu_cap = fields.Float(digits=(16, 0))
    amount = fields.Float(digits=(16, 0), compute='get_tong_thu_nhap', store=True, readonly=True)
    ghi_chu = fields.Text()
    thang = fields.Char(readonly=True)
    nam = fields.Char(readonly=True)

    @api.depends('sl_gh_bt', 'sl_gh_tc', 'thu_nhap', 'phu_cap')
    def get_tong_thu_nhap(self):
        for rec in  self:
            rec.sl_hang_giao = rec.sl_gh_bt + rec.sl_gh_tc
            rec.amount = rec.thu_nhap + rec.phu_cap

    @api.multi
    def update_salary_delivery_income(self):
        record = self.env['income.inventory'].search([])
        for rec in record:
            phuong_thuc_giao_hang = rec.delivery_method
            if phuong_thuc_giao_hang != 'warehouse' and rec.delivery_done_date != False:
                date = datetime.strptime(rec.delivery_done_date, DEFAULT_SERVER_DATETIME_FORMAT)
                code = 'SKL' + str(rec.user_delivery_id.id) + '/' + date.strftime("%m%y")
                value = self.env['salary.delivery.income'].search([('default_code', '=', code)])
                tn = rec.thu_nhap
                if rec.giao_hang_tang_cuong == 'no':
                    sl_gh_bt = rec.kich_thuoc_don_hang.number_sign
                    sl_gh_tc = 0
                else:
                    sl_gh_bt = 0
                    sl_gh_tc = rec.kich_thuoc_don_hang.number_sign

                if not value:
                    value = rec.env['salary.delivery.income'].create({
                        'default_code': code,
                        'month': date.strftime("%m/%Y"),
                        'name': rec.user_delivery_id.name,
                        'sl_gh_bt': sl_gh_bt,
                        'sl_gh_tc': sl_gh_tc,
                        'thu_nhap': tn,
                        'thang': date.strftime("%m"),
                        'nam': date.strftime("%Y"),
                    })
                else:
                    if rec.giao_hang_tang_cuong == 'no':
                        sl_gh_bt = value.sl_gh_bt
                        sl_gh_bt += rec.kich_thuoc_don_hang.number_sign
                        thu_nhap = value.thu_nhap + tn
                        value.write({
                            'sl_gh_bt': sl_gh_bt,
                            'thu_nhap': thu_nhap,
                        })
                    else:
                        sl_gh_tc = value.sl_gh_tc
                        sl_gh_tc += rec.kich_thuoc_don_hang.number_sign
                        thu_nhap = value.thu_nhap + tn
                        value.write({
                            'sl_gh_tc': sl_gh_tc,
                            'thu_nhap': thu_nhap,
                        })
    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.model
    def export_overview_salary_delivery(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        thang = self.env['salary.delivery.income'].search(domain, limit=1).thang
        nam = self.env['salary.delivery.income'].search(domain, limit=1).nam
        # delivery_ids = self.env['income.inventory'].search(domain)
        delivery_ids = self.env['income.inventory'].search([('delivery_done_date', 'ilike', '%' + nam + '-' + thang + '%')])

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Thông tin chi tiết')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        header_bold_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_number.set_num_format('#,##0')
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})

        worksheet.set_column('A:A', 16)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 22)
        worksheet.set_column('E:E', 16)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 19)
        worksheet.set_column('H:H', 16)
        worksheet.set_column('I:I', 16)
        worksheet.set_column('J:J', 17)
        worksheet.set_column('K:K', 12)


        summary_header = ['Nhân viên giao hàng', 'Sale Order', 'Partner', 'Thời gian hoàn tất giao hàng', 'Kích thước đơn hàng', 'Giao hàng tăng cường',
                          'Phương thức giao hàng', 'Phường/Xã giao', 'Quận/Huyện giao', 'Tỉnh/Thành phố giao', 'Thu nhập']

        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for rec in delivery_ids:
            row += 1
            giao_hang_tang_cuong = dict(self.env['income.inventory'].fields_get(allfields=['giao_hang_tang_cuong'])['giao_hang_tang_cuong']['selection'])
            delivery_method = dict(self.env['income.inventory'].fields_get(allfields=['delivery_method'])['delivery_method']['selection'])
            delivery_done_date = ''
            if rec.delivery_done_date:
                delivery_done_date = rec._get_datetime_utc(rec.delivery_done_date)

            worksheet.write(row, 0, rec.user_delivery_id.name or '', text_style)
            worksheet.write(row, 1, rec.income_name or '', text_style)
            worksheet.write(row, 2, rec.partner_id.display_name or '', text_style)
            worksheet.write(row, 3, delivery_done_date or '', text_style)
            worksheet.write(row, 4, rec.kich_thuoc_don_hang.number_sign or '', text_style)
            worksheet.write(row, 5, giao_hang_tang_cuong.get(rec.giao_hang_tang_cuong) or '', text_style)
            worksheet.write(row, 6, delivery_method.get(rec.delivery_method) or '', text_style)
            worksheet.write(row, 7, rec.ward_id.name or '', text_style)
            worksheet.write(row, 8, rec.district_id.name or '', text_style)
            worksheet.write(row, 9, rec.city_id.name or '', text_style)
            worksheet.write(row, 10, rec.thu_nhap or '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()