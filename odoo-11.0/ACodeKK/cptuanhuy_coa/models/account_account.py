# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import base64
import StringIO
import xlsxwriter

class account_acocunt(models.Model):
    _inherit = 'account.account'

    @api.multi
    def _compute_account_debit_credit(self):
        for acc in self:
            if self._context.get('date_from'):
                date_from = self._context.get('date_from')
                start_date = (datetime.strptime(date_from, "%Y-%m-%d")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            else:
                date_from = False

            if self._context.get('date_to'):
                date_to = self._context.get('date_to')
                end_date = (datetime.strptime(date_to, "%Y-%m-%d")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            else:
                date_to = False

            if self._context.get('target_move') and self._context.get('target_move') == 'all':
                target_move = ['draft', 'posted']
            else:
                target_move = ['posted']
            before_debit = before_credit = current_debit = current_credit = 0
            # Fetch data list from account move line based on selected parameters
            if self._context.get('target_move') and self._context.get('date_from') and self._context.get('date_to'):
                query_before = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml 
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s  AND aml.date < '%s';""" % (acc.id, start_date)
                self.env.cr.execute(query_before)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        before_debit = move_before[0][0]
                        before_credit = move_before[0][1]

                query_current = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s AND aml.date >= '%s' AND aml.date <= '%s';""" % (acc.id, start_date, end_date)
                self.env.cr.execute(query_current)
                move_current = self.env.cr.fetchall()
                if move_current and len(move_current) > 0:
                    if move_current[0][0] or move_current[0][1]:
                        current_debit = move_current[0][0]
                        current_credit = move_current[0][1]


            elif self._context.get('target_move') and self._context.get('date_from') and not self._context.get(
                    'date_to'):
                query_before = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s  AND aml.date < '%s';""" % (acc.id, start_date)
                self.env.cr.execute(query_before)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        before_debit = move_before[0][0]
                        before_credit = move_before[0][1]

                query_current = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s AND aml.date >= '%s';""" % (acc.id, start_date)
                self.env.cr.execute(query_current)
                move_current = self.env.cr.fetchall()
                if move_current and len(move_current) > 0:
                    if move_current[0][0] or move_current[0][1]:
                        current_debit = move_current[0][0]
                        current_credit = move_current[0][1]


            elif self._context.get('target_move') and not self._context.get('date_from') and self._context.get(
                    'date_to'):
                query_before = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s  AND aml.date < '%s';""" % (acc.id, end_date)
                self.env.cr.execute(query_before)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        before_debit = move_before[0][0]
                        before_credit = move_before[0][1]

                query_current = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s AND aml.date >= '%s';""" % (acc.id, end_date)
                self.env.cr.execute(query_current)
                move_current = self.env.cr.fetchall()
                if move_current and len(move_current) > 0:
                    if move_current[0][0] or move_current[0][1]:
                        current_debit = move_current[0][0]
                        current_credit = move_current[0][1]


            elif self._context.get('target_move') and not self._context.get('date_from') and not self._context.get(
                    'date_to'):
                query_current = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                    FROM account_move_line aml
                                    LEFT JOIN account_move am ON (am.id = aml.move_id)
                                    WHERE aml.account_id = %s;""" % (acc.id)
                self.env.cr.execute(query_current)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        current_debit = move_before[0][0]
                        current_credit = move_before[0][1]
            temp_before = before_debit - before_credit
            if temp_before > 0:
                before_debit_total = temp_before
                before_credit_total = 0
            else:
                before_debit_total = 0
                before_credit_total = - temp_before
            # acc.current_debit = current_debit
            # acc.current_credit = current_credit
            temp = before_debit + current_debit - current_credit - before_credit
            if temp > 0:
                after_debit = temp
                after_credit = 0
            else:
                after_debit = 0
                after_credit = - temp
            return before_debit_total, before_credit_total, current_debit, current_credit, after_debit, after_credit

    before_debit = fields.Monetary(compute='_compute_account', string='Nợ đầu kì')
    before_credit = fields.Monetary(compute='_compute_account', string='Có đầu kì')
    current_debit = fields.Monetary(compute='_compute_account', string='Phát sinh Nợ')
    current_credit = fields.Monetary(compute='_compute_account', string='Phát sinh Có')
    after_debit = fields.Monetary(compute='_compute_account', string='Nợ cuối kì')
    after_credit = fields.Monetary(compute='_compute_account', string='Có cuối kì')

    @api.multi
    def _compute_account(self):
        for record in self:
            if record.code == '3331':
                True
            before_debit = before_credit = current_debit = current_credit = after_debit = after_credit = 0
            len_lv1 = len(record.code)
            child_account_lv1 = self.search([('code', '=like', record.code + "%")]).filtered(lambda r: len(r.code) == (len_lv1 + 1))
            if not child_account_lv1:
                before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = record._compute_account_debit_credit()
            else:
                for child in child_account_lv1:
                    before_debit_child = before_credit_child = current_debit_child = current_credit_child = after_debit_child = after_credit_child = 0
                    len_lv2 = len(child.code)
                    child_account_lv2 = self.search([('code', '=like', child.code + "%")]).filtered(lambda r: len(r.code) == (len_lv2 + 1))
                    if not child_account_lv2:
                        before_debit_child, before_credit_child, current_debit_child, current_credit_child, after_debit_child, after_credit_child = child._compute_account_debit_credit()
                    else:
                        for child_lv2 in child_account_lv2:
                            before_debit_child2 = before_credit_child2 = current_debit_child2 = current_credit_child2 = after_debit_child2 = after_credit_child2 = 0
                            len_lv3 = len(child.code)
                            child_account_lv3 = self.search([('code', '=like', child_lv2.code + "%")]).filtered(lambda r: len(r.code) == (len_lv3 + 1))
                            if not child_account_lv3:
                                before_debit_child2, before_credit_child2, current_debit_child2, current_credit_child2, after_debit_child2, after_credit_child2 = child_lv2._compute_account_debit_credit()
                            else:
                                for child_lv3 in child_account_lv3:
                                    before_debit_child3, before_credit_child3, current_debit_child3, current_credit_child3, after_debit_child3, after_credit_child3 = child_lv3._compute_account_debit_credit()
                                    before_debit_child2 += before_debit_child3
                                    before_credit_child2 += before_credit_child3
                                    current_debit_child2 += current_debit_child3
                                    current_credit_child2 += current_credit_child3
                                    after_debit_child2 += after_debit_child3
                                    after_credit_child2 += after_credit_child3
                            before_debit_child += before_debit_child2
                            before_credit_child += before_credit_child2
                            current_debit_child += current_debit_child2
                            current_credit_child += current_credit_child2
                            after_debit_child += after_debit_child2
                            after_credit_child += after_credit_child2
                    before_debit += before_debit_child
                    before_credit += before_credit_child
                    current_debit += current_debit_child
                    current_credit += current_credit_child
                    after_debit += after_debit_child
                    after_credit += after_credit_child
            record.update({
                'before_debit': before_debit,
                'before_credit': before_credit,
                'current_debit': current_debit,
                'current_credit': current_credit,
                'after_debit': after_debit,
                'after_credit': after_credit,
            })

    @api.model
    def print_excel(self, records):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('BangCanDoi')

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})


        worksheet.merge_range('A1:I1', self.env.user.company_id.name or '', body_bold_color)
        worksheet.merge_range('A2:I2', self.env.user.company_id.street or '', body_bold_color)
        worksheet.merge_range('A3:I3', 'BẢNG CÂN ĐỐI', header_bold_color)
        day_now = datetime.now().date().strftime('Ngày %d tháng %m năm %Y')
        worksheet.merge_range('A4:I4', day_now, header_bold_color)
        row = 4
        row += 1
        worksheet.write(row, 2, 'Tổng Nợ ĐK',header_bold_color)
        worksheet.write(row, 3, 'Tổng Có ĐK',header_bold_color)
        worksheet.write(row, 4, 'Tổng PS Nợ',header_bold_color)
        worksheet.write(row, 5, 'Tổng PS Có',header_bold_color)
        worksheet.write(row, 6, 'Tổng Nợ CK',header_bold_color)
        worksheet.write(row, 7, 'Tổng Có CK',header_bold_color)
        row += 1
        worksheet.write(row, 2, sum(res['before_debit'] for res in records))
        worksheet.write(row, 3, sum(res['before_credit'] for res in records))
        worksheet.write(row, 4, sum(res['current_debit'] for res in records))
        worksheet.write(row, 5, sum(res['current_credit'] for res in records))
        worksheet.write(row, 6, sum(res['after_debit'] for res in records))
        worksheet.write(row, 7, sum(res['after_credit'] for res in records))
        row += 1
        summary_header = ['Mã', 'Tên', 'Nợ đầu kì', 'Có đầu kì', 'Phát sinh Nợ', 'Phát sinh Có',
                          'Nợ cuối kì', 'Có cuối kì', 'Loại']


        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for record in records:
            row += 1
            worksheet.write(row, 0, record['code'])
            worksheet.write(row, 1, record['name'])
            worksheet.write(row, 2, record['before_debit'])
            worksheet.write(row, 3, record['before_credit'])
            worksheet.write(row, 4, record['current_debit'])
            worksheet.write(row, 5, record['current_credit'])
            worksheet.write(row, 6, record['after_debit'])
            worksheet.write(row, 7, record['after_credit'])
            worksheet.write(row, 8, record['user_type_id'] and record['user_type_id'][1] or '')

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'BangCanDoi_Excel.xlsx', 'datas_fname': 'BangCanDoi_Excel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return str(base_url) + str(download_url)
