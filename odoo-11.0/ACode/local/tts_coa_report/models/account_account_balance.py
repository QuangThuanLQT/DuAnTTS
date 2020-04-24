# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import base64
import StringIO
import xlsxwriter
from calendar import monthrange
from odoo import models, fields, api


class account_account_balance(models.TransientModel):
    _name = 'account.account.balance'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    def get_data_account(self, start_date, end_date, acc):
        before_debit = before_credit = current_debit = current_credit = 0
        # Fetch data list from account move line based on selected parameters
        if start_date and end_date:
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
                                WHERE aml.account_id = %s AND aml.date >= '%s' AND aml.date <= '%s';""" % (
                acc.id, start_date, end_date)
            self.env.cr.execute(query_current)
            move_current = self.env.cr.fetchall()
            if move_current and len(move_current) > 0:
                if move_current[0][0] or move_current[0][1]:
                    current_debit = move_current[0][0]
                    current_credit = move_current[0][1]


        elif start_date and not end_date:
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


        elif not start_date and end_date:
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


        elif not start_date and not end_date:
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
            before_debit = temp_before
            before_credit = 0
        else:
            before_debit = 0
            before_credit = - temp_before
        temp = before_debit + current_debit - current_credit - before_credit
        if temp > 0:
            after_debit = temp
            after_credit = 0
        else:
            after_debit = 0
            after_credit = - temp
        return before_debit, before_credit, current_debit, current_credit, after_debit, after_credit

    def get_data(self, start_date, end_date):
        list_account_3 = []
        account_data = []
        account4_data = []
        account_query_data = []

        query = """SELECT id, code, name FROM account_account WHERE LENGTH(code) = 3;"""
        self.env.cr.execute(query)
        account3_data = self.env.cr.fetchall()
        for line in account3_data:
            if line[0]:
                list_account_3.append(line[0])
                data = {
                    'id': line[0],
                    'code': line[1],
                    'name': line[2]
                }
                account_data.append(data)
        for account in account_data:
            childs = self.env['account.account'].search(
                [('code', '=like', account.get('code') + "%"), ('id', '!=', account.get('id'))]).filtered(lambda line: len(line.code) == 4)
            if not childs:
                account_id = self.env['account.account'].browse(account.get('id'))
                before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = self.get_data_account(
                    start_date, end_date, account_id)
                account.update({
                    'parent_before_debit': before_debit,
                    'parent_before_credit': before_credit,
                    'parent_current_debit': current_debit,
                    'parent_current_credit': current_credit,
                    'parent_after_debit': after_debit,
                    'parent_after_credit': after_credit,
                    'lines': []
                })
            else:
                lines = []
                parent_before_debit = parent_before_credit = parent_current_debit = parent_current_credit = parent_after_debit = parent_after_credit = 0
                for child in childs:
                    list_account_3.append(child.id)

                    childs_lv2 = self.env['account.account'].search(
                        [('code', '=like', child.code + "%"), ('id', '!=', child.id)])

                    if not childs_lv2:
                        before_debit_lv1, before_credit_lv1, current_debit_lv1, current_credit_lv1, after_debit_lv1, after_credit_lv1 = self.get_data_account(
                            start_date, end_date, child)
                        parent_before_debit += before_debit_lv1
                        parent_before_credit += before_credit_lv1
                        parent_current_debit += current_debit_lv1
                        parent_current_credit += current_credit_lv1
                        parent_after_debit += after_debit_lv1
                        parent_after_credit += after_credit_lv1
                        data_child = {
                            'id': child.id,
                            'code': child.code,
                            'name': child.name,
                            'before_debit': before_debit_lv1,
                            'before_credit': before_credit_lv1,
                            'current_debit': current_debit_lv1,
                            'current_credit': current_credit_lv1,
                            'after_debit': after_debit_lv1,
                            'after_credit': after_credit_lv1,
                            'lines': [],
                        }
                        lines.append(data_child)
                    else:
                        line_lv2 = []
                        before_debit_lv1 = before_credit_lv1 = current_debit_lv1 = current_credit_lv1 = after_debit_lv1 = after_credit_lv1 = 0
                        for child_lv2 in childs_lv2:
                            list_account_3.append(child_lv2.id)
                            before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = self.get_data_account(
                                start_date, end_date, child_lv2)
                            before_debit_lv1 += before_debit
                            before_credit_lv1 += before_credit
                            current_debit_lv1 += current_debit
                            current_credit_lv1 += current_credit
                            after_debit_lv1 += after_debit
                            after_credit_lv1 += after_credit

                            data_child_lv2 = {
                                'id': child_lv2.id,
                                'code': child_lv2.code,
                                'name': child_lv2.name,
                                'before_debit': before_debit,
                                'before_credit': before_credit,
                                'current_debit': current_debit,
                                'current_credit': current_credit,
                                'after_debit': after_debit,
                                'after_credit': after_credit,
                                'lines': [],
                            }
                            line_lv2.append(data_child_lv2)

                        data_child = {
                            'id': child.id,
                            'code': child.code,
                            'name': child.name,
                            'before_debit': before_debit_lv1,
                            'before_credit': before_credit_lv1,
                            'current_debit': current_debit_lv1,
                            'current_credit': current_credit_lv1,
                            'after_debit': after_debit_lv1,
                            'after_credit': after_credit_lv1,
                            'lines': line_lv2,
                        }
                        lines.append(data_child)

                        parent_before_debit += before_debit_lv1
                        parent_before_credit += before_credit_lv1
                        parent_current_debit += current_debit_lv1
                        parent_current_credit += current_credit_lv1
                        parent_after_debit += after_debit_lv1
                        parent_after_credit += after_credit_lv1

                account.update({
                    'lines': lines,
                    'parent_before_debit': parent_before_debit,
                    'parent_before_credit': parent_before_credit,
                    'parent_current_debit': parent_current_debit,
                    'parent_current_credit': parent_current_credit,
                    'parent_after_debit': parent_after_debit,
                    'parent_after_credit': parent_after_credit
                })

        query_acc4 = """SELECT id, code, name FROM account_account WHERE LENGTH(code) = 4 and id not in (%s);""" % (
        ', '.join(str(id) for id in list_account_3))
        self.env.cr.execute(query_acc4)
        query_acc4 = self.env.cr.fetchall()
        for line in query_acc4:
            if line[0]:
                list_account_3.append(line[0])
                data = {
                    'id': line[0],
                    'code': line[1],
                    'name': line[2]
                }
                account4_data.append(data)
        for account in account4_data:
            childs = self.env['account.account'].search(
                [('code', '=like', account.get('code') + "%"), ('id', '!=', account.get('id'))])
            if not childs:
                account_id = self.env['account.account'].browse(account.get('id'))
                before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = self.get_data_account(
                    start_date, end_date, account_id)
                account.update({
                    'parent_before_debit': before_debit,
                    'parent_before_credit': before_credit,
                    'parent_current_debit': current_debit,
                    'parent_current_credit': current_credit,
                    'parent_after_debit': after_debit,
                    'parent_after_credit': after_credit,
                    'lines': []
                })
            else:
                lines = []
                parent_before_debit = parent_before_credit = parent_current_debit = parent_current_credit = parent_after_debit = parent_after_credit = 0
                for child in childs:
                    list_account_3.append(child.id)
                    before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = self.get_data_account(
                        start_date, end_date, child)
                    parent_before_debit += before_debit
                    parent_before_credit += before_credit
                    parent_current_debit += current_debit
                    parent_current_credit += current_credit
                    parent_after_debit += after_debit
                    parent_after_credit += after_credit
                    data_child = {
                        'id': child.id,
                        'code': child.code,
                        'name': child.name,
                        'before_debit': before_debit,
                        'before_credit': before_credit,
                        'current_debit': current_debit,
                        'current_credit': current_credit,
                        'after_debit': after_debit,
                        'after_credit': after_credit,
                        'lines': []
                    }
                    lines.append(data_child)
                account.update({
                    'lines': lines,
                    'parent_before_debit': parent_before_debit,
                    'parent_before_credit': parent_before_credit,
                    'parent_current_debit': parent_current_debit,
                    'parent_current_credit': parent_current_credit,
                    'parent_after_debit': parent_after_debit,
                    'parent_after_credit': parent_after_credit
                })

        account_query = """SELECT id, code, name FROM account_account WHERE id not in (%s);""" % (
        ', '.join(str(id) for id in list_account_3))
        self.env.cr.execute(account_query)
        account_query_list = self.env.cr.fetchall()
        for line in account_query_list:
            if line[0]:
                list_account_3.append(line[0])
                data = {
                    'id': line[0],
                    'code': line[1],
                    'name': line[2]
                }
                account_query_data.append(data)
        for account in account_query_data:
            childs = self.env['account.account'].search(
                [('code', '=like', account.get('code') + "%"), ('id', '!=', account.get('id'))])
            if not childs:
                account_id = self.env['account.account'].browse(account.get('id'))
                before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = self.get_data_account(
                    start_date, end_date, account_id)
                account.update({
                    'parent_before_debit': before_debit,
                    'parent_before_credit': before_credit,
                    'parent_current_debit': current_debit,
                    'parent_current_credit': current_credit,
                    'parent_after_debit': after_debit,
                    'parent_after_credit': after_credit,
                    'lines': []
                })
            else:
                lines = []
                parent_before_debit = parent_before_credit = parent_current_debit = parent_current_credit = parent_after_debit = parent_after_credit = 0
                for child in childs:
                    list_account_3.append(child.id)
                    before_debit, before_credit, current_debit, current_credit, after_debit, after_credit = self.get_data_account(
                        start_date, end_date, child)
                    parent_before_debit += before_debit
                    parent_before_credit += before_credit
                    parent_current_debit += current_debit
                    parent_current_credit += current_credit
                    parent_after_debit += after_debit
                    parent_after_credit += after_credit
                    data_child = {
                        'id': child.id,
                        'code': child.code,
                        'name': child.name,
                        'before_debit': before_debit,
                        'before_credit': before_credit,
                        'current_debit': current_debit,
                        'current_credit': current_credit,
                        'after_debit': after_debit,
                        'after_credit': after_credit,
                        'lines': []
                    }
                    lines.append(data_child)
                account.update({
                    'lines': lines,
                    'parent_before_debit': parent_before_debit,
                    'parent_before_credit': parent_before_credit,
                    'parent_current_debit': parent_current_debit,
                    'parent_current_credit': parent_current_credit,
                    'parent_after_debit': parent_after_debit,
                    'parent_after_credit': parent_after_credit,
                })
        data = account_data + account4_data + account_query_data
        return data

    def export_data_excel(self):
        data = self.get_data(self.start_date, self.end_date)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('BaoCao')

        title_report = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        title_report_2 = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })
        header_bold_left = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': 'cce0ff',
        })
        header_bold_left_child = workbook.add_format({
            'bold': False,
            'font_size': '11',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
        })
        body_bold_table = workbook.add_format(
            {'bold': True, 'border': 1, 'font_size': '12', 'bg_color': 'cce0ff', 'align': 'center',
             'valign': 'vcenter'})
        body_bold_table_child = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '12', 'align': 'center', 'valign': 'vcenter'})

        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'bold': True,
            'bg_color': 'cce0ff',
        })
        money_child = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)

        worksheet.merge_range('A1:I1', unicode("BẢNG CÂN ĐỐI PHÁT SINH", "utf-8"), title_report)
        worksheet.merge_range('A2:I2', unicode("Từ ngày: %s   Đên ngày: %s" %(self.start_date or '', self.end_date or ''), "utf-8"), title_report_2)

        worksheet.write(3, 1, "STT", header_bold_color)
        worksheet.write(3, 2, "Tên tài khoản", header_bold_color)
        worksheet.merge_range('D4:E4', "Số dư đầu kì", header_bold_color)
        worksheet.merge_range('F4:G4', "Số phát sinh trong kì", header_bold_color)
        worksheet.merge_range('H4:I4', "Số dư cuối kì", header_bold_color)

        worksheet.write(4, 1, "", header_bold_color)
        worksheet.write(4, 2, "", header_bold_color)
        worksheet.write(4, 3, "Nợ", header_bold_color)
        worksheet.write(4, 4, "Có", header_bold_color)
        worksheet.write(4, 5, "Nợ", header_bold_color)
        worksheet.write(4, 6, "Có", header_bold_color)
        worksheet.write(4, 7, "Nợ", header_bold_color)
        worksheet.write(4, 8, "Có", header_bold_color)

        row = 5
        for account in sorted(data, key=lambda k: k['code']) :
            worksheet.write(row, 1, account.get('code'), body_bold_table)
            worksheet.write(row, 2, account.get('name'), header_bold_left)
            worksheet.write(row, 3, account.get('parent_before_debit'), money)
            worksheet.write(row, 4, account.get('parent_before_credit'), money)
            worksheet.write(row, 5, account.get('parent_current_debit'), money)
            worksheet.write(row, 6, account.get('parent_current_credit'), money)
            worksheet.write(row, 7, account.get('parent_after_debit'), money)
            worksheet.write(row, 8, account.get('parent_after_credit'), money)
            row += 1
            for child in account.get('lines'):
                worksheet.write(row, 1, child.get('code'), body_bold_table_child)
                worksheet.write(row, 2, child.get('name'), header_bold_left_child)
                worksheet.write(row, 3, child.get('before_debit'), money_child)
                worksheet.write(row, 4, child.get('before_credit'), money_child)
                worksheet.write(row, 5, child.get('current_debit'), money_child)
                worksheet.write(row, 6, child.get('current_credit'), money_child)
                worksheet.write(row, 7, child.get('after_debit'), money_child)
                worksheet.write(row, 8, child.get('after_credit'), money_child)
                row += 1
                for child_lv2 in child.get('lines'):
                    worksheet.write(row, 1, child_lv2.get('code'), body_bold_table_child)
                    worksheet.write(row, 2, child_lv2.get('name'), header_bold_left_child)
                    worksheet.write(row, 3, child_lv2.get('before_debit'), money_child)
                    worksheet.write(row, 4, child_lv2.get('before_credit'), money_child)
                    worksheet.write(row, 5, child_lv2.get('current_debit'), money_child)
                    worksheet.write(row, 6, child_lv2.get('current_credit'), money_child)
                    worksheet.write(row, 7, child_lv2.get('after_debit'), money_child)
                    worksheet.write(row, 8, child_lv2.get('after_credit'), money_child)
                    row += 1

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'BaoCao.xlsx', 'datas_fname': 'BaoCao.xlsx', 'datas': result})
        self.attachment_id = attachment_id
        if 'get_attachment' in self._context:
            return True
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {"type": "ir.actions.act_url",
                "url": str(download_url)}
        True
