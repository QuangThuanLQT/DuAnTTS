# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import base64

import StringIO
import xlsxwriter
from xlrd import open_workbook
import os


class import_purchase_order(models.TransientModel):
    _name = 'import.account.voucher'

    import_data = fields.Binary(string="File Import")
    file_name   = fields.Char()
    unt_unc     = fields.Boolean(string='Import Giấy báo nợ/có',default=False)

    @api.multi
    def import_xls(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)


                for row_no in range(sheet.nrows):
                    if row_no >= 1:
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

                        if line[4] or line[5]:
                            voucher_obj = self.env['account.voucher']
                            date = False
                            if line[0] and '-' in line[0]:
                                date = datetime.strptime(line[0].strip(), '%d-%m-%y').strftime(DEFAULT_SERVER_DATE_FORMAT)
                            if line[0] and '/' in line[0]:
                                date = datetime.strptime(line[0].strip(), '%d/%m/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)
                            number_voucher = line[1].strip()
                            tai_khoan_giao_dich = line[2].strip()
                            account_cash = self.env['account.account'].search([('code','=','1111')])
                            partner_id  = self.env['res.partner'].sudo().search([('name','ilike',line[6].strip())],limit=1)
                            if not partner_id and line[6]:
                                partner_obj = self.env['res.partner']
                                partner_id = partner_obj.create({'name': line[6].strip()})
                            if line[4] and float(line[4]) != 0:
                                name = line[3].strip()
                                account_id = self.env['account.account'].search([('code','=','331')])
                                price_unit = line[4] and -float(line[4]) if float(line[4]) < 0 else float(line[4])
                                # import Giay bao no
                                if self.unt_unc:
                                    self.env['account.voucher.unc'].create({
                                        'account_id'        : account_id.id,
                                        'date_create'       : date,
                                        'note'              : name,
                                        'amount'            : price_unit,
                                        'ref'               : number_voucher or '',
                                        'acc_number'        : tai_khoan_giao_dich,
                                        'partner_id'        : partner_id and partner_id.id or False,
                                    })
                                else:
                                    fields_get = voucher_obj._fields
                                    voucher_values = voucher_obj.with_context({'default_voucher_type': 'purchase', 'voucher_type': 'purchase'}).default_get(fields_get)

                                    voucher_values.update({
                                        'date' : date,
                                        'number_voucher' : number_voucher,
                                        'tai_khoan_giao_dich' : tai_khoan_giao_dich,
                                        'account_id': account_cash.id,
                                        'partner_id': partner_id and partner_id.id or False,
                                        'line_ids' : [(0,0,{
                                            'name' : name,
                                            'account_id' : account_id.id,
                                            'price_unit' : price_unit,
                                        })]
                                    })
                                    voucher_obj.create(voucher_values)
                            elif line[5] and float(line[5]) != 0:
                                name = line[3].strip()
                                account_id = self.env['account.account'].search([('code','=','131')])
                                price_unit = line[5] and -float(line[5]) if float(line[5]) < 0 else float(line[5])
                                fields_get = voucher_obj._fields
                                context ={'default_voucher_type': 'sale', 'voucher_type': 'sale'}
                                if self.unt_unc:
                                    context.update({'unt_unc':True})
                                voucher_values = voucher_obj.with_context(context).default_get(fields_get)
                                voucher_values.update({
                                    'date' : date,
                                    'number_voucher' : number_voucher,
                                    'tai_khoan_giao_dich' : tai_khoan_giao_dich,
                                    'account_id' : account_cash.id,
                                    'partner_id': partner_id and partner_id.id or False,
                                    'line_ids' : [(0,0,{
                                        'name' : name,
                                        'account_id' : account_id.id,
                                        'price_unit' : price_unit,
                                    })]
                                })
                                voucher_obj.create(voucher_values)

    @api.multi
    def export_xls(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet 1')

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 100)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 25)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        # body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        # body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['Ngày', 'Số bút toán', 'Tài khoản đích', 'Diễn giải', 'Nợ', 'Có','Người Nhận/Thu']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        if self.unt_unc:
            example_no_id  = self.env['account.voucher.unc'].search([],limit=1,order='id desc')
            for line in range(0, 1):
                row += 1
                worksheet.write(row, 0, example_no_id.date_create and datetime.strptime(example_no_id.date_create,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or '')
                worksheet.write(row, 1, example_no_id.ref or '')
                worksheet.write(row, 2, example_no_id.acc_number or '')
                worksheet.write(row, 3, example_no_id.note or '')
                worksheet.write(row, 4, -example_no_id.amount)
                worksheet.write(row, 5, '')
                worksheet.write(row, 6, example_no_id.partner_id.name or '')
        else:
            example_no_id = self.env['account.voucher'].search([('voucher_type', '=', 'purchase')], limit=1,order='id desc')
            for line in range(0, 1):
                row += 1
                worksheet.write(row, 0, example_no_id.date and datetime.strptime(example_no_id.date,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or '')
                worksheet.write(row, 1, example_no_id.number_voucher or '')
                worksheet.write(row, 2, example_no_id.tai_khoan_giao_dich or '')
                worksheet.write(row, 3, example_no_id.line_ids and example_no_id.line_ids[0].name or '')
                worksheet.write(row, 4, example_no_id.line_ids and -example_no_id.line_ids[0].price_unit)
                worksheet.write(row, 5, '')
                worksheet.write(row, 6, example_no_id.partner_id.name or '')

        example_co_id = self.env['account.voucher'].search([('voucher_type', '=', 'sale')], limit=1, order='id desc')

        for line in range(0,1):
            row += 1
            worksheet.write(row, 0, example_co_id.date and datetime.strptime(example_co_id.date,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or '')
            worksheet.write(row, 1, example_co_id.number_voucher or '')
            worksheet.write(row, 2, example_co_id.tai_khoan_giao_dich or '')
            worksheet.write(row, 3, example_co_id.line_ids and example_co_id.line_ids[0].name or '')
            worksheet.write(row, 4, '')
            worksheet.write(row, 5, example_co_id.line_ids and example_co_id.line_ids[0].price_unit or 0)
            worksheet.write(row, 6, example_co_id.partner_id.name or '')

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'Sample import format.xlsx',
            'datas_fname': 'Sample import format.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }
