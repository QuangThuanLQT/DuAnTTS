# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import base64
import StringIO
import xlsxwriter


class SaleReportExcel(models.Model):
    _name = 'sale.report.excel'

    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date', required=True)

    @api.multi
    def print_report_excel(self):
        self.ensure_one()

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        accounts = [
            '511',
            '521',
        ]
        for account_code in accounts:
            account_sheet = workbook.add_worksheet(account_code)
            sheet = self.create_sheet_account(account_sheet, workbook, account_code)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'Baocao_BanHang_Excel.xlsx', 'datas_fname': 'Baocao_BanHang_Excel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}



    def create_sheet_account(self, worksheet, workbook, account_code):
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        header_body_color = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'center',
            'valign': 'vcenter',
        })
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': 'cce0ff',
            'border': 1,
        })
        body_bold_table = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '12', 'align': 'left', 'valign': 'vcenter'})
        title_report = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        back_color = 'A1:G1'

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 60)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 15)

        worksheet.merge_range('A1:G1', unicode("SỔ CHI TIẾT CÁC TÀI KHOẢN %s" %(account_code,), "utf-8"), title_report)
        worksheet.merge_range('A2:G2', unicode("Tài khoản: %s; Tháng %s năm %s" % (account_code, start_date.month, start_date.year), "utf-8"), header_body_color)

        accounts = self.env['account.account'].search([
            ('code', '=like', account_code + '%')
        ])
        if accounts:
            conditions = []
            conditions_before = []
            if len(accounts) > 1:
                conditions = [('account_id', 'in', accounts.ids)]
                conditions_before = [('account_id', 'in', accounts.ids)]
            elif len(accounts) == 1:
                conditions = [('account_id', '=', accounts.id)]
                conditions_before = [('account_id', '=', accounts.id)]

            if self.start_date:
                conditions.append(('date', '>=', self.start_date))
                conditions_before.append(('date', '<', self.start_date))
            if self.end_date:
                conditions.append(('date', '<=', self.end_date))

            header = [
                'Ngày hạch toán',
                'Ngày chứng từ',
                'Số chứng từ',
                'Diễn giải',
                'Tài khoản',
                'TK đối ứng',
                'Phát sinh Nợ',
                'Phát sinh Có',
                'Dư Nợ',
                'Dư Có'
            ]
            row = 3

            [worksheet.write(row, header_cell, unicode(header[header_cell], "utf-8"), header_bold_color) for
             header_cell in
             range(0, len(header)) if header[header_cell]]

            no_before = 0.0
            co_before = 0.0
            if self.start_date:
                data_before = self.env['account.move.line'].search(conditions_before)
                for data_line in data_before:
                    no_before += data_line.debit
                    co_before += data_line.credit

            # no_before = self.round_number(no_before)
            # co_before = self.round_number(co_before)

            row += 1
            worksheet.write(row, 3, unicode("Số dư đầu kỳ", "utf-8"), body_bold_table)
            worksheet.write(row, 4, account_code, body_bold_table)
            worksheet.write(row, 8, no_before, money)
            worksheet.write(row, 9, co_before, money)

            no_current = 0.0
            co_current = 0.0
            data_line_report = []
            current_data = self.env['account.move.line'].search(conditions, order='date asc, ref asc')  # , order='partner_id asc, date asc'
            for data_line in current_data:
                no_current += data_line.debit
                co_current += data_line.credit
                doiung = ''
                move_id = data_line.move_id
                if data_line.debit > data_line.credit:
                    list = []
                    for line in move_id.line_ids:
                        if line.credit > 0 and line.account_id.code not in list:
                            list.append(line.account_id.code)
                    doiung = ', '.join(list)

                elif data_line.debit < data_line.credit:
                    list = []
                    for line in move_id.line_ids:
                        if line.debit > 0 and line.account_id.code not in list:
                            list.append(line.account_id.code)
                    doiung = ', '.join(list)
                else:
                    list = []
                    for line in move_id.line_ids.filtered(lambda l: l.account_id.code != data_line.account_id.code):
                        if line.account_id.code not in list:
                            list.append(line.account_id.code)
                    doiung = ', '.join(list)


                row += 1

                worksheet.write(row, 0, data_line.date, body_bold_table)
                worksheet.write(row, 1, data_line.date, body_bold_table)
                worksheet.write(row, 2, data_line.ref or '', body_bold_table)
                worksheet.write(row, 3, data_line.name, body_bold_table)
                worksheet.write(row, 4, data_line.account_id.code, body_bold_table)
                worksheet.write(row, 5, doiung, body_bold_table)
                worksheet.write(row, 6, data_line.debit, money)
                worksheet.write(row, 7, data_line.credit, money)
                worksheet.write(row, 8, no_before + no_current, money)
                worksheet.write(row, 9, co_before + co_current, money)

            # no_current = self.round_number(no_current)
            # co_current = self.round_number(co_current)

            row += 1
            worksheet.write(row, 3, unicode("Cộng", "utf-8"), body_bold_table)
            worksheet.write(row, 4, account_code, body_bold_table)
            worksheet.write(row, 5, "", body_bold_table)
            worksheet.write(row, 6, no_current, money)
            worksheet.write(row, 7, co_current, money)
            worksheet.write(row, 8, "", body_bold_table)
            worksheet.write(row, 9, "", body_bold_table)

            no_end = 0.0
            co_end = 0.0
            sum_cong_no = no_before + no_current - co_before - co_current
            if sum_cong_no < 0:
                co_end = - sum_cong_no
            else:
                no_end = sum_cong_no

            # no_end = self.round_number(no_end)
            # co_end = self.round_number(co_end)

            row += 1
            worksheet.write(row, 3, unicode("Số dư cuối kỳ", "utf-8"), body_bold_table)
            worksheet.write(row, 4, account_code, body_bold_table)
            worksheet.write(row, 5, "", body_bold_table)
            worksheet.write(row, 6, "", body_bold_table)
            worksheet.write(row, 7, "", body_bold_table)
            worksheet.write(row, 8, no_end, money)
            worksheet.write(row, 9, co_end, money)
        else:
            header = [
                'Ngày hạch toán',
                'Ngày chứng từ',
                'Số chứng từ',
                'Diễn giải',
                'Tài khoản',
                'TK đối ứng',
                'Phát sinh Nợ',
                'Phát sinh Có',
                'Dư Nợ',
                'Dư Có'
            ]
            row = 3

            [worksheet.write(row, header_cell, unicode(header[header_cell], "utf-8"), header_bold_color) for
             header_cell in
             range(0, len(header)) if header[header_cell]]

            row += 1
            worksheet.write(row, 3, unicode("Số dư đầu kỳ", "utf-8"), body_bold_table)
            worksheet.write(row, 4, account_code, body_bold_table)
            worksheet.write(row, 8, 0, money)
            worksheet.write(row, 9, 0, money)

            row += 1
            worksheet.write(row, 3, unicode("Cộng", "utf-8"), body_bold_table)
            worksheet.write(row, 4, account_code, body_bold_table)
            worksheet.write(row, 5, "", body_bold_table)
            worksheet.write(row, 6, 0, money)
            worksheet.write(row, 7, 0, money)
            worksheet.write(row, 8, "", body_bold_table)
            worksheet.write(row, 9, "", body_bold_table)

            row += 1
            worksheet.write(row, 3, unicode("Số dư cuối kỳ", "utf-8"), body_bold_table)
            worksheet.write(row, 4, account_code, body_bold_table)
            worksheet.write(row, 5, "", body_bold_table)
            worksheet.write(row, 6, "", body_bold_table)
            worksheet.write(row, 7, "", body_bold_table)
            worksheet.write(row, 8, 0, money)
            worksheet.write(row, 9, 0, money)
