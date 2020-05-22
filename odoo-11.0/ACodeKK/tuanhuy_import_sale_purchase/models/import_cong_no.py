# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
import base64
import StringIO
import os
import tempfile
import shutil
import xlsxwriter
import json

from xlrd import open_workbook
import os


class import_cong_no(models.TransientModel):
    _name = 'import.cong.no'

    import_data = fields.Binary(string="File Import")
    file_name = fields.Char()
    name = fields.Text(string="Notes")
    check_import = fields.Boolean('Allow import', default=False)

    @api.multi
    def check_import_file(self):
        for record in self:
            data = base64.b64decode(record.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            data_list = {
                'product_not_find': [],
                'price_not_sync': [],
                'customer_not_find': [],
            }

            for row_no in range(sheet.nrows):
                if row_no >= 1:
                    line = (
                        map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                    partner_id = self.env['res.partner'].search([('name', '=', line[0].strip())], limit=1)
                    if not partner_id:
                        debit = float(line[2])
                        credit = float(line[3])
                        if debit != 0 or credit != 0:
                            data_list['customer_not_find'].append({
                                'line': row_no + 1,
                                'customer_name': line[0],
                            })

            return {
                'name': 'Import Warning Order',
                'type': 'ir.actions.act_window',
                'res_model': 'import.warning.order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'data': data_list,
                    'import_data': record.import_data,
                    'name_action': "import.cong.no",
                    'name_model': "import.cong.no",
                    'name': self.name,
                }
            }

    @api.model
    def default_get(self, fields):
        res = super(import_cong_no, self).default_get(fields)
        if 'import_data' in self._context:
            res['import_data'] = self._context.get('import_data')
            res['name'] = self._context.get('name')
        return res

    @api.multi
    def import_xls(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                journal_id = self.env['account.journal'].search([('sequence_id.name', '=', "Miscellaneous Operations")],
                                                                limit=1)

                account_move_id = self.env['account.move'].create({
                    'narration': self.name,
                    'journal_id': journal_id.id,
                    'date': datetime.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
                })
                count_line = 0
                count_line_used = 0
                line_data = []
                debit_sum = 0
                credit_sum = 0

                for row_no in range(sheet.nrows):
                    if row_no >= 1:
                        count_line += 1
                        line = (map(
                            lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                        debit = float(line[2])
                        credit = float(line[3])
                        if debit != 0 or credit != 0:
                            partner_id = self.env['res.partner'].search([('name', '=', line[0].strip())], limit=1)
                            if not partner_id:
                                if not record.check_import:
                                    raise UserError(_('Please check file first'))
                                else:
                                    partner_id = self.env['res.partner'].create({
                                        'name': line[0].strip(),
                                        'customer': True
                                    })

                            account_id = self.env['account.account'].search([('code', '=', line[1].strip())], limit=1)
                            if not account_id:
                                raise UserError(_('Không tìm thấy tài khoản code: %s') % line[1])

                            count_line_used += 1
                            data = {
                                'account_id': account_id.id,
                                'partner_id': partner_id.id,
                                'name': "/",
                                'debit': debit,
                                'credit': credit,
                            }

                            line_data.append((0, 0, data))
                            debit_sum += debit
                            credit_sum += credit

                account_id = self.env['account.account'].search([('code', '=', "4111")], limit=1)
                number_debit = debit_sum - credit_sum
                if number_debit < 0:
                    data = {
                        'account_id': account_id.id,
                        'name': "/",
                        'debit': -number_debit,
                        'credit': 0.00,
                    }
                    line_data.append((0, 0, data))
                if number_debit > 0:
                    data = {
                        'account_id': account_id.id,
                        'name': "/",
                        'debit': 0.00,
                        'credit': number_debit,
                    }
                    line_data.append((0, 0, data))

                account_move_id.write({
                    'line_ids': line_data
                })

                print
                count_line
                print
                count_line_used

    @api.multi
    def export_xls(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet 1')

        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        # body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        # body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['Khách hàng', 'Tài khoản (Code)', 'Debit', 'Credit']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        sample_debit_id = self.env['account.move.line'].search([('partner_id', '!=', False), ('debit', '!=', 0)],
                                                               limit=1, order='id desc')
        sample_credit_id = self.env['account.move.line'].search([('partner_id', '!=', False), ('credit', '!=', 0)],
                                                                limit=1, order='id desc')

        if sample_debit_id:
            for line in range(0, 1):
                row += 1
                worksheet.write(row, 0, sample_debit_id.partner_id.name or '')
                worksheet.write(row, 1, sample_debit_id.account_id.code or '')
                worksheet.write(row, 2, sample_debit_id.debit or 0)
                worksheet.write(row, 3, sample_debit_id.credit or 0)

        if sample_credit_id:
            for line in range(0, 1):
                row += 1
                worksheet.write(row, 0, sample_credit_id.partner_id.name or '')
                worksheet.write(row, 1, sample_credit_id.account_id.code or '')
                worksheet.write(row, 2, sample_credit_id.debit or 0)
                worksheet.write(row, 3, sample_credit_id.credit or 0)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'Sample Cong No format.xlsx',
            'datas_fname': 'Sample Cong No format.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }
