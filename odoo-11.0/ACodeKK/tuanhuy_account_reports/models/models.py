# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import base64
import StringIO
import xlsxwriter

class tuanhuy_hdkd_reports(models.Model):
    _name = 'tuanhuy.hdkd.report'

    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date', required=True)
    attachment_id = fields.Many2one('ir.attachment')
    send_email = fields.Boolean(default=False)
    email = fields.Char(string='Email')

    def cron_send_mail_hdkd_report(self):
        report_ids = self.env['tuanhuy.hdkd.report'].search([('send_email','=',True)])
        for report_id in report_ids:
            try:
                if report_id.email:
                    report_id.send_email = False
                    report_id.with_context(get_attachment=True).print_report_excel()
                    mail_values = {
                        'email_from': "",
                        'email_to': report_id.email,
                        'subject': 'Hoạt động kinh doanh report',
                        'body_html': "",
                        'attachment_ids': [(4, report_id.attachment_id.id)]
                    }
                    mail = self.env['mail.mail'].create(mail_values)
                    mail.send()
                report_id.send_email = False
            except:
                report_id.send_email = False

    @api.multi
    def send_mail_report(self):
        self.send_email = True

    @api.multi
    def print_report_excel(self):
        self.ensure_one()

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet('Baocaokqkd')

        worksheet.set_column('A:F', 15)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)

        bold = workbook.add_format({'bold': True})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '13', 'align': 'left', 'valign': 'vcenter'})
        header_bold_table = workbook.add_format(
            {'bold': True, 'border': 1, 'font_size': '13', 'align': 'center', 'valign': 'vcenter'})
        body_bold_table = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '13', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        title_report = workbook.add_format(
            {'bold': True, 'font_size': '16', 'align': 'center', 'valign': 'vcenter'})
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'font_size': '13',
            'valign': 'vcenter'
        })
        body_chuky_table = workbook.add_format(
            {'bold': True, 'border': 0, 'font_size': '13', 'align': 'center', 'valign': 'vcenter'})

        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        back_color = 'A1:G1'
        worksheet.merge_range(back_color, unicode("SHOWROOM", "utf-8"), header_bold_color)
        worksheet.merge_range('A2:G2', unicode("38 Trần Kế Xương, Hải Châu, Đà Nẵng", "utf-8"), header_bold_color)
        worksheet.merge_range('A4:G4', unicode("BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH", "utf-8"), title_report)
        worksheet.merge_range('A5:F5', unicode("Kì báo cáo", "utf-8"), header_bold_color)
        worksheet.write('G5:G5', self.start_date, header_bold_color)
        worksheet.write('H5:H5', self.end_date, header_bold_color)
        row = 7
        worksheet.merge_range(row, 0, row, 5, unicode("Chỉ tiêu", "utf-8"), header_bold_table)
        worksheet.write(row, 6, unicode("Mã số", "utf-8"), header_bold_table)
        worksheet.write(row, 7, unicode("%s" %(self.end_date), "utf-8"), header_bold_table)

        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("1", "utf-8"), header_bold_table)
        worksheet.write(row, 6, unicode("2", "utf-8"), header_bold_table)
        worksheet.write(row, 7, unicode("4", "utf-8"), header_bold_table)

        journal_items = self.env['account.move.line'].search([
            '|',
            ('account_id.code', 'ilike', '511'),
            ('account_id.code', 'ilike', '512'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_credit_01 = sum(journal_items.mapped('credit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("1. Doanh thu bán hàng và cung cấp dịch vụ ", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("01", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_credit_01, money)

        # journal_items = self.env['account.move.line'].search([
        #     '|',
        #     ('account_id.code', 'ilike', '111'),
        #     ('account_id.code', 'ilike', '112'),
        #     ('date', '>=', self.start_date),
        #     ('date', '<=', self.end_date)
        # ])

        # account_voucher = self.env['account.voucher'].search([
        #     ('date', '>=', self.start_date),
        #     ('date', '<=', self.end_date),
        #     ('journal_id.type', '=', 'sale'),
        #     ('voucher_type', '=', 'sale')
        # ])
        # account_voucher_line = account_voucher.mapped('line_ids').ids
        # account_voucher_line = self.env['account.voucher.line'].search([('id','in',account_voucher_line),('account_id.code','=','131')])
        # total_debit_02 = sum(account_voucher_line.mapped('price_unit'))
        #
        # account_payment_gbn = self.env['account.payment.gbn'].search([
        #     ('date_create', '>=', self.start_date),
        #     ('date_create', '<=', self.end_date),
        #     ('account_id.code', '=', '131'),
        # ])
        #
        # total_debit_02 += sum(account_payment_gbn.mapped('amount'))

        account_invoice_ids = self.env['account.invoice'].search([
            ('date_invoice', '>=', self.start_date),
            ('date_invoice', '<=', self.end_date),
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('state','=','paid'),
        ])

        total_debit_02 = sum(account_invoice_ids.mapped('amount_untaxed'))

        # total_debit_02 = sum(journal_items.mapped('debit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("a. Doanh Thu về tiền mặt + Ngân hàng", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("02", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_debit_02, money)

        # journal_items = self.env['account.move.line'].search([
        #     ('account_id.code', 'ilike', '131'),
        #     ('date', '>=', self.start_date),
        #     ('date', '<=', self.end_date)
        # ])
        # total_debit_03 = sum(journal_items.mapped('debit')) if journal_items else 0

        total_debit_03 = total_credit_01 - total_debit_02
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("b. Doanh Thu Về công nợ", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("03", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_debit_03, money)

        journal_items = self.env['account.move.line'].search([
            ('account_id.code', 'ilike', '521'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_credit_04 = sum(journal_items.mapped('debit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("2. Các khoản giảm trừ doanh thu:"
                                                      "- Hàng bán bị trả lại" , "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("04", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_credit_04, money)

        total_05 = total_credit_01 - total_credit_04
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (05 = 01 - 04)", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("05", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_05, money)

        journal_items = self.env['account.move.line'].search([
            ('account_id.code', 'ilike', '632'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_debit_06 = sum(journal_items.mapped('debit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("4. Giá vốn hàng bán", "utf-8"),
                              body_bold_table)
        worksheet.write(row, 6, unicode("06", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_debit_06, money)

        journal_items = self.env['account.move.line'].search([
            ('account_id.code', 'ilike', '632'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_credit_07 = sum(journal_items.mapped('credit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("5. Các khoản giảm trừ giá vốn: \n                                  - Giá vốn hàng trả lại", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("07", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_credit_07, money)
        worksheet.set_row(row, 35)

        total_08 = total_debit_06 - total_credit_07
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("6. Giá vốn hàng bán hàng bán ra (08=06-07)", "utf-8"),
                              body_bold_table)
        worksheet.write(row, 6, unicode("08", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_08, money)

        total_09 = total_05 - total_08
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("7. Lợi nhuận gộp về bán hàng và cung cấp dịch vụ (09=05-08)", "utf-8"),
                              body_bold_table)
        worksheet.write(row, 6, unicode("09", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_09, money)

        journal_items = self.env['account.move.line'].search([
            ('account_id.code', 'ilike', '641'),
            # ('account_id.code', 'ilike', '642'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_debit_10 = sum(journal_items.mapped('debit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("8. Chi phí bán hàng", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("10", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_debit_10, money)

        journal_items = self.env['account.move.line'].search([
            # ('account_id.code', 'ilike', '334'),
            ('account_id.code', 'ilike', '642'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_debit_11 = sum(journal_items.mapped('debit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("9. Chi phí lương tháng %s/%s" %(start_date.month, start_date.year), "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("11", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_debit_11, money)

        total_12 = total_09 - (total_debit_10 + total_debit_11)
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("10. Lợi nhuận thuần từ hoạt động kinh doanh (12 = 09 - (10 + 11))", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("12", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_12, money)

        journal_items = self.env['account.move.line'].search([
            '|',
            ('account_id.code', 'ilike', '711'),
            ('account_id.code', 'ilike', '715'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_credit_13 = sum(journal_items.mapped('credit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("11. Thu nhập khác + lãi ngân hàng", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("13", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_credit_13, money)

        journal_items = self.env['account.move.line'].search([
            ('account_id.code', 'ilike', '811'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        total_debit_14 = sum(journal_items.mapped('debit')) if journal_items else 0
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("12. Chi phí khác", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("14", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_debit_14, money)

        total_15 = total_credit_13 - total_debit_14
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("13. Lợi nhuận khác (15 = 13- 14)", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("15", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_15, money)

        total_16 = total_12 + total_15
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("14. Tổng lợi nhuận kế toán trước thuế (16=12+15)", "utf-8"), body_bold_table)
        worksheet.write(row, 6, unicode("16", "utf-8"), body_bold_table)
        worksheet.write(row, 7, total_16, money)

        row += 2
        worksheet.merge_range(row, 0, row, 2, unicode("Người lập biểu", "utf-8"),
                              body_chuky_table)
        worksheet.merge_range(row, 6, row, 7, unicode("Giám đốc", "utf-8"),
                              body_chuky_table)
        row += 1
        worksheet.merge_range(row, 0, row, 2, unicode("(Ký, họ tên)", "utf-8"),
                              body_chuky_table)
        worksheet.merge_range(row, 6, row, 7, unicode("(Ký, họ tên)", "utf-8"),
                              body_chuky_table)



        worksheet_2 = workbook.add_worksheet('TỔNG HỢP')
        tonghop_sheet = self.create_tonghop_sheet(worksheet_2, workbook)

        accounts = [
            '511',
            '632',
            '811',
            '711',
            '521',
            '131',
            '331',
            '111',
            '112',
            '641',
            '642',
        ]
        for account_code in accounts:
            account_sheet = workbook.add_worksheet(account_code)
            self.create_sheet_account(account_sheet, workbook, account_code)

        baocaotonkho = workbook.add_worksheet('TonKho')
        self.create_sheet_tonkho(baocaotonkho, workbook)


        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'Baocao_HDKD.xlsx', 'datas_fname': 'Baocao_HDKD.xlsx', 'datas': result})
        self.attachment_id = attachment_id
        if 'get_attachment' in self._context:
            return True
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    def round_number(self, number):
        return number # math.floor(number / 100) * 100

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
        conditions = []
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
        no_before_amount = co_before_amount = 0
        if self.start_date:
            data_before = self.env['account.move.line'].search(conditions_before)
            for data_line in data_before:
                no_before += data_line.debit
                co_before += data_line.credit

        no_before = self.round_number(no_before)
        co_before = self.round_number(co_before)
        if (no_before - co_before) > 0:
            no_before_amount = no_before - co_before
            co_before_amount = 0
        elif (co_before - no_before) > 0:
            co_before_amount = co_before - no_before
            no_before_amount = 0
        row += 1
        worksheet.write(row, 3, unicode("Số dư đầu kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 4, account_code, body_bold_table)
        worksheet.write(row, 8, no_before_amount, money)
        worksheet.write(row, 9, co_before_amount, money)

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

            line_name = data_line.name
            if line_name == '/':
                if data_line.ref:
                    if 'SO' in data_line.ref:
                        line_name = 'Bán hàng'
                    elif 'PO' in data_line.ref:
                        line_name = 'Mua hàng'
                    elif 'RTP' in data_line.ref:
                        line_name = 'Trả hàng mua'
                    elif 'RT0' in data_line.ref:
                        line_name = 'Trả hàng bán'
                else:
                    if data_line.account_id.code == '331':
                        line_name = 'Bán hàng'
            temp = no_before_amount - co_before_amount + data_line.debit - data_line.credit
            if temp > 0:
                no_before_amount = temp
                co_before_amount = 0
            else:
                co_before_amount = - temp
                no_before_amount = 0
            worksheet.write(row, 0, data_line.date, body_bold_table)
            worksheet.write(row, 1, data_line.date, body_bold_table)
            worksheet.write(row, 2, data_line.ref or '', body_bold_table)
            worksheet.write(row, 3, line_name, body_bold_table)
            worksheet.write(row, 4, data_line.account_id.code, body_bold_table)
            worksheet.write(row, 5, doiung, body_bold_table)
            worksheet.write(row, 6, data_line.debit, money)
            worksheet.write(row, 7, data_line.credit, money)
            worksheet.write(row, 8, no_before_amount, money)
            worksheet.write(row, 9, co_before_amount, money)

        no_current = self.round_number(no_current)
        co_current = self.round_number(co_current)

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

        no_end = self.round_number(no_end)
        co_end = self.round_number(co_end)

        row += 1
        worksheet.write(row, 3, unicode("Số dư cuối kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 4, account_code, body_bold_table)
        worksheet.write(row, 5, "", body_bold_table)
        worksheet.write(row, 6, "", body_bold_table)
        worksheet.write(row, 7, "", body_bold_table)
        worksheet.write(row, 8, no_end, money)
        worksheet.write(row, 9, co_end, money)

    def create_sheet_tonkho(self, worksheet, workbook):
        data = self.get_product_data(self.start_date, self.end_date)
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'cce0ff', 'border': 1,})
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter', 'border': 1,})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter', 'border': 1,})
        body_bold_color_number.set_num_format('#,##0')
        body_bold_color_number2 = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'dddddd', 'border': 1,})
        body_bold_color_number2.set_num_format('#,##0')
        back_color = 'C2:E2'
        worksheet.merge_range(back_color, unicode("TỔNG HỢP TỒN KHO", "utf-8"), merge_format)
        worksheet.write(3, 0, unicode("Kỳ báo cáo:", "utf-8"), body_bold_color)
        worksheet.write(3, 9, self.start_date, body_bold_color)
        if self.end_date:
            worksheet.write(3, 10, self.end_date, body_bold_color)

        worksheet.set_column('A:A', 60)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('K:K', 20)

        row = 5
        worksheet.merge_range(row, 0, row + 1, 0, unicode("Sản Phẩm", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 1, row + 1, 1, unicode("Mã nội bộ", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 2, row + 1, 2, unicode("ĐVT", "utf-8"), header_bold_color)
        count = 0
        col = 2
        summary_header = ['Đầu kỳ', 'Nhập kho', 'Xuất kho', 'Cuối kỳ']
        summary_header_2 = ['Số lượng', 'Giá trị', 'Số lượng', 'Giá trị', 'Số lượng', 'Giá trị', 'Số lượng', 'Giá trị']
        [worksheet.merge_range(row, (3 + header_cell * 2), row, (3 + header_cell * 2 + 1),
                               unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        row += 1
        [worksheet.write(row, 3 + header_cell, unicode(summary_header_2[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header_2)) if summary_header_2[header_cell]]
        row += 1
        worksheet.merge_range(row, 0, row, 2, unicode("Tên kho : Kho Tổng (%s )" %len(data['lines']) ), body_bold_color)
        worksheet.write(row, 3, data['total']['first_qty'], body_bold_color_number2)
        worksheet.write(row, 4, data['total']['price_first'], body_bold_color_number2)
        worksheet.write(row, 5, data['total']['incoming_qty'], body_bold_color_number2)
        worksheet.write(row, 6, data['total']['price_incoming'], body_bold_color_number2)
        worksheet.write(row, 7, data['total']['outgoing_qty'], body_bold_color_number2)
        worksheet.write(row, 8, data['total']['price_outgoing'], body_bold_color_number2)
        worksheet.write(row, 9, data['total']['last_qty'], body_bold_color_number2)
        worksheet.write(row, 10, data['total']['price_last'], body_bold_color_number2)

        for line in data['lines']:
            row += 1
            worksheet.write(row, 0, line['name'], body_bold_color)
            worksheet.write(row, 1, line['default_code'], body_bold_color)
            worksheet.write(row, 2, line['product_uom'], body_bold_color)
            worksheet.write(row, 3, line['first_qty'], body_bold_color_number)
            worksheet.write(row, 4, line['price_first'], body_bold_color_number)
            worksheet.write(row, 5, line['incoming_qty'], body_bold_color_number)
            worksheet.write(row, 6, line['price_incoming'], body_bold_color_number)
            worksheet.write(row, 7, line['outgoing_qty'], body_bold_color_number)
            worksheet.write(row, 8, line['price_outgoing'], body_bold_color_number)
            worksheet.write(row, 9, line['last_qty'], body_bold_color_number)
            worksheet.write(row, 10, line['price_last'], body_bold_color_number)

    def get_product_data(self, date_from, date_to):
        line = []
        location = False
        i = 1
        data = {
            'ids': self.ids,
            'model': 'ton.kho.report',
            'lines': [],
        }
        total_first = total_in = total_out = total_last_qty = 0
        total_first_price = total_in_price = total_out_price = total_last_qty_price = 0

        product_query = """SELECT 
        pp.id as id,
        pt.name as name, 
        pp.default_code as default_code, 
        uom.name as uom_name
        FROM product_product pp
        INNER JOIN product_template pt
        INNER JOIN product_uom uom
        ON uom.id = pt.uom_id
        ON pp.product_tmpl_id = pt.id
        """
        self.env.cr.execute(product_query)
        product_data = self.env.cr.fetchall()
        for product in product_data:
            # print i
            product_id  = product[0]
            product_name = product[1]
            product_code = product[2]
            product_uom  = product[3]

            first_qty_in = first_qty_out = incoming_qty = outgoing_qty = last_qty = 0
            first_qty_in_price = outgoing_price = incoming_price = first_qty_out_price = 0.0

            accounts = self.env['account.account'].search([('code', '=like', '156%')])

            debit_before_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.debit > 0
                AND aml.date < '%s' 
                AND aml.product_id = '%s' """ % (', '.join(str(id) for id in accounts.ids), date_from, product_id)
            self.env.cr.execute(debit_before_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                first_qty_in += move_before[0][0] or 0
                first_qty_in_price += move_before[0][1] or 0

            credit_before_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.credit > 0
                AND aml.date < '%s' 
                AND aml.product_id = '%s' """ % (', '.join(str(id) for id in accounts.ids), date_from, product_id)
            self.env.cr.execute(credit_before_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                first_qty_out += move_before[0][0] or 0
                first_qty_out_price += move_before[0][2] or 0

            ton_dauky = first_qty_in - first_qty_out
            ton_dauky_price = first_qty_in_price - first_qty_out_price

            debit_current_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.debit > 0
                AND aml.date >= '%s'
                AND aml.date <= '%s'
                AND aml.product_id = '%s' """ % (
            ', '.join(str(id) for id in accounts.ids), date_from, date_to, product_id)

            self.env.cr.execute(debit_current_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                incoming_qty += move_before[0][0] or 0
                incoming_price += move_before[0][1] or 0

            credit_current_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.credit > 0
                AND aml.date >= '%s'
                AND aml.date <= '%s'
                AND aml.product_id = '%s' """ % (
            ', '.join(str(id) for id in accounts.ids), date_from, date_to, product_id)
            self.env.cr.execute(credit_current_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                outgoing_qty += move_before[0][0] or 0
                outgoing_price += move_before[0][2] or 0

            last_qty = ton_dauky + incoming_qty - outgoing_qty
            last_price = ton_dauky_price + incoming_price - outgoing_price

            # res = product.with_context({'location': location, 'from_date': self.start_date, 'to_date': self.end_date})._compute_quantities_dict()
            total_first += ton_dauky
            total_in += incoming_qty
            total_out += outgoing_qty
            total_last_qty += last_qty
            total_first_price += ton_dauky_price
            total_in_price += incoming_price
            total_out_price += outgoing_price
            total_last_qty_price += last_price

            product_data = {
                'name': product_name,
                'default_code': product_code,
                'product_uom': product_uom,
                'first_qty': ton_dauky,
                'price_first': ton_dauky_price,
                'incoming_qty': incoming_qty,
                'price_incoming': incoming_price,
                'outgoing_qty': outgoing_qty,
                'price_outgoing': outgoing_price,
                'last_qty': last_qty,
                'price_last': last_price,
            }
            data['lines'].append(product_data)
            i += 1
        data['total'] = {
            'first_qty': total_first,
            'price_first': total_first_price,
            'incoming_qty': total_in,
            'price_incoming': total_in_price,
            'outgoing_qty': total_out,
            'price_outgoing': total_out_price,
            'last_qty': total_last_qty,
            'price_last': total_last_qty_price,
        }
        return data


    def create_tonghop_sheet(self, worksheet, workbook):
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        header_bold_table = workbook.add_format(
            {'bold': True, 'border': 1, 'font_size': '12', 'align': 'left', 'valign': 'vcenter'})
        body_bold_table = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '12', 'align': 'left', 'valign': 'vcenter'})
        title_report = workbook.add_format(
            {'bold': True, 'font_size': '18', 'align': 'center', 'valign': 'vcenter'})
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        money_bold = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'bold': True,
        })
        back_color = 'A1:G1'

        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 60)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)

        worksheet.merge_range(back_color, unicode("SHOWROOM", "utf-8"), header_bold_color)
        worksheet.merge_range('A2:D2', unicode("38 Trần Kế Xương, Hải Châu, Đà Nẵng", "utf-8"), header_bold_color)
        worksheet.merge_range('A4:D4', unicode("BÁO CÁO TỔNG HỢP DOANH THU THÁNG %s/%s" %(start_date.month, start_date.year), "utf-8"), title_report)
        worksheet.merge_range('A5:D5', unicode("TẠI SHOWROOM", "utf-8"), header_bold_color)
        total = 0
        row = 6
        worksheet.write(row, 0, unicode("STT", "utf-8"), header_bold_table)
        worksheet.write(row, 1, unicode("Diễn giải", "utf-8"), header_bold_table)
        worksheet.write(row, 2, unicode("Số tiền", "utf-8"), header_bold_table)
        worksheet.write(row, 3, unicode("Công ty Cổ Phần Cơ Điện ", "utf-8"), header_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 2, start_date.strftime('%d/%m/%Y'), body_bold_table)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        data_money = self.get_move_from_account(self.start_date, self.end_date, ['111', '112'])
        worksheet.write(row, 0, unicode("1", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Tiền ", "utf-8"), header_bold_table)
        worksheet.write(row, 2, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Tiền mặt : ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['111']['total'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_money['111']['total']

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("- Tồn đầu kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['111']['ton_before'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("- Thu tiền trong kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['111']['co_current'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("- Chi tiền trong kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['111']['no_current'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Tiền gởi Ngân hàng: ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['112']['total'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_money['112']['total']

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("- Tồn đầu kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['112']['ton_before'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("- Thu tiền trong kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['112']['co_current'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode(" - Chi tiền trong kỳ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_money['112']['no_current'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        data_partner = self.get_total_by_customer(self.start_date, self.end_date, ['131', '331'])
        worksheet.write(row, 0, unicode("2", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("PHẢI THU KHÁCH HÀNG", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_partner['131']['total'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_partner['131']['total']
        for line in data_partner['131']['data']:
            if line['total'] != 0:
                row += 1
                worksheet.write(row, 0, "", body_bold_table)
                worksheet.write(row, 1, line['partner_name'], body_bold_table)
                worksheet.write(row, 2, line['total'], money)
                worksheet.write(row, 3, "", body_bold_table)


        row += 1
        data_product = self.get_total_by_product(self.start_date, self.end_date, ['156', '511', '521'])
        worksheet.write(row, 0, unicode("3", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("HÀNG TỒN KHO", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_product['156']['total'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_product['156']['total']
        for line in data_product['156']['data']:
            if line['total'] != 0:
                row += 1
                worksheet.write(row, 0, "", body_bold_table)
                worksheet.write(row, 1, line['brand_name'], body_bold_table)
                worksheet.write(row, 2, line['total'], money)
                worksheet.write(row, 3, "", body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("4", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("PHẢI TRẢ NHÀ CUNG CẤP", "utf-8"), header_bold_table)
        worksheet.write(row, 2, - data_partner['331']['total'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += -data_partner['331']['total']
        for line in data_partner['331']['data']:
            if line['total'] != 0:
                row += 1
                worksheet.write(row, 0, "", body_bold_table)
                worksheet.write(row, 1, line['partner_name'], body_bold_table)
                worksheet.write(row, 2, - line['total'], money)
                worksheet.write(row, 3, "", body_bold_table)


        row += 1
        worksheet.write(row, 0, unicode("6", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("DOANH THU BÁN HÀNG", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_product['511']['total_co'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_product['511']['total_co']
        for line in data_product['511']['data']:
            if line['co_current'] != 0:
                row += 1
                worksheet.write(row, 0, "", body_bold_table)
                worksheet.write(row, 1, line['brand_name'], body_bold_table)
                worksheet.write(row, 2, line['co_current'], money)
                worksheet.write(row, 3, "", body_bold_table)

        row += 1
        data_account = self.get_total_from_account(self.start_date, self.end_date, ['632', '641', '334', '811', '642'])
        worksheet.write(row, 0, unicode("7", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("GIÁ VỐN", "utf-8"), money_bold)
        worksheet.write(row, 2, data_account['632']['no_amount'], money)
        worksheet.write(row, 3, "", body_bold_table)
        total += data_account['632']['no_amount']

        row += 1
        worksheet.write(row, 0, unicode("8", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("HÀNG TRẢ LẠI", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_product['521']['total_no'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_product['521']['total_no']

        for line in data_product['521']['data']:
            if line['no_current'] != 0:
                row += 1
                worksheet.write(row, 0, "", body_bold_table)
                worksheet.write(row, 1, line['brand_name'], body_bold_table)
                worksheet.write(row, 2, line['no_current'], money)
                worksheet.write(row, 3, "", body_bold_table)


        row += 1
        worksheet.write(row, 0, unicode("9", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("GIÁ VỐN HÀNG TRẢ LẠI", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_account['632']['co_amount'], money_bold)
        worksheet.write(row, 3, "", body_bold_table)
        total += data_account['632']['co_amount']

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Giá vốn hàng trả lại ", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_account['632']['co_amount'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("10", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("CÁC KHOẢN CHI PHÍ ", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_account['641']['no_amount'] + data_account['642']['no_amount'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_account['641']['no_amount']
        total += data_account['642']['no_amount']
        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Chi phí bán hàng", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_account['641']['no_amount'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Chi Phí lương + bhxh", "utf-8"), body_bold_table)
        worksheet.write(row, 2, data_account['642']['no_amount'], money)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("11", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("CHI PHÍ KHÁC", "utf-8"), header_bold_table)
        worksheet.write(row, 2, data_account['811']['no_amount'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += data_account['811']['no_amount']

        data_account_other = self.get_total_by_customer(self.start_date, self.end_date, ['3388'])
        row += 1
        worksheet.write(row, 0, unicode("12", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("PHẢI TRẢ KHÁC", "utf-8"), header_bold_table)
        worksheet.write(row, 2, - data_account_other['3388']['total'], money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)
        total += - data_account_other['3388']['total']
        for line in data_account_other['3388']['data']:
            if line['no_current'] != 0:
                row += 1
                worksheet.write(row, 0, "", body_bold_table)
                worksheet.write(row, 1, line['partner_name'], body_bold_table)
                worksheet.write(row, 2, - line['total'], money)
                worksheet.write(row, 3, "", body_bold_table)

        row += 1
        worksheet.write(row, 0, unicode("", "utf-8"), body_bold_table)
        worksheet.write(row, 1, unicode("Tổng Cộng ", "utf-8"), header_bold_table)
        worksheet.write(row, 2, total, money_bold)
        worksheet.write(row, 3, unicode("", "utf-8"), body_bold_table)

    def get_move_from_account(self, start_date, end_date, list_acc):
        data = {}
        for account in list_acc:
            aml_before = self.env['account.move.line'].search([('account_id.code', '=like', account + '%'), ('date', '<', start_date)])
            aml_current = self.env['account.move.line'].search([('account_id.code', '=like', account + '%'), ('date', '>=', start_date), ('date', '<=', end_date)])
            no_current = 0
            co_current = 0
            for line in aml_current:
                no_current += line.debit
                co_current += line.credit
            no_before = 0
            co_before = 0
            for line in aml_before:
                no_before += line.debit
                co_before += line.credit
            data[account] = {
                'ton_before': no_before - co_before,
                'no_current': no_current,
                'co_current': co_current,
                'total': no_before + no_current - co_before - co_current,
            }
        return data

    def get_total_by_customer(self, start_date, end_date, list_acc):
        data = {}
        for account in list_acc:
            data_line_report = []
            account_ids = self.env['account.account'].search([('code', '=like', account + "%")])
            query_string = "SELECT DISTINCT partner_id FROM account_move_line WHERE account_id IN (%s) ORDER BY partner_id" % (', '.join(str(id) for id in account_ids.ids))
            self.env.cr.execute(query_string)
            lines = self.env.cr.fetchall()
            total_no = 0
            total_co = 0
            total_dauky = 0
            for line in lines:
                line_data = {'partner_ref': '', 'partner_name': ''}
                conditions = [('account_id', 'in', account_ids.ids)]
                conditions_before = [('account_id', 'in', account_ids.ids)]

                if self.start_date:
                    conditions.append(('date', '>=', self.start_date))
                    conditions_before.append(('date', '<', self.start_date))
                if self.end_date:
                    conditions.append(('date', '<=', self.end_date))
                partner_id = line[0] or False
                if partner_id:
                    partner = self.env['res.partner'].browse(partner_id)
                    conditions.append(('partner_id', '=', partner.id))
                    conditions_before.append(('partner_id', '=', partner.id))
                    line_data.update({
                        'partner_ref': partner.ref or partner.id,
                        'partner_name': partner.name,
                    })
                else:
                    conditions.append(('partner_id', '=', False))
                    conditions_before.append(('partner_id', '=', False))

                no_before = 0.0
                co_before = 0.0
                if self.start_date:
                    data_before = self.env['account.move.line'].search(conditions_before)
                    for data_line in data_before:
                        no_before += data_line.debit
                        co_before += data_line.credit

                no_before = self.round_number(no_before)
                co_before = self.round_number(co_before)
                dauky = no_before - co_before
                total_dauky += no_before - co_before
                no_current = 0.0
                co_current = 0.0
                current_data = self.env['account.move.line'].search(conditions)  # , order='partner_id asc, date asc'
                for data_line in current_data:
                    no_current += data_line.debit
                    co_current += data_line.credit

                no_current = self.round_number(no_current)
                co_current = self.round_number(co_current)
                total_no += no_current
                total_co += co_current
                # no_end = 0.0
                # co_end = 0.0
                # sum_cong_no = no_before + no_current - co_before - co_current
                # if sum_cong_no < 0:
                #     co_end = - sum_cong_no
                # else:
                #     no_end = sum_cong_no
                #
                # no_end = self.round_number(no_end)
                # co_end = self.round_number(co_end)
                line_data.update({
                    'dauky': dauky,
                    # 'co_before': co_before,
                    'no_current': no_current,
                    'co_current': co_current,
                    'total': dauky + no_current  - co_current,
                    # 'no_end': no_end,
                    # 'co_end': co_end,
                })
                data_line_report.append(line_data)
            data[account] = {
                'data': data_line_report,
                'total_dauky': total_dauky,
                'total_no': total_no,
                'total_co': total_co,
                'total': total_dauky + total_no - total_co
            }
        return data
    def get_total_by_product(self, start_date, end_date, list_acc):
        data = {}
        for account in list_acc:
            data_line_report = []
            account_ids = self.env['account.account'].search([('code', '=like', account + "%")])
            lines = ['LS', 'Schneider', 'Các hãng khác']
            # query_string = """SELECT DISTINCT pt.brand_name FROM account_move_line aml LEFT JOIN product_product pp ON pp.id = aml.product_id
				# 									 LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id  WHERE account_id IN (%s) ORDER BY pt.brand_name""" % (', '.join(str(id) for id in account_ids.ids))
            # self.env.cr.execute(query_string)
            # lines = self.env.cr.fetchall()
            total_no = 0
            total_co = 0
            total_dauky = 0
            for line in lines:
                data_line_report
                line_data = {'brand_name': line}
                conditions = [('account_id', 'in', account_ids.ids)]
                condition_before = [('account_id', 'in', account_ids.ids)]
                if self.start_date:
                    conditions.append(('date', '>=', self.start_date))
                    condition_before.append(('date', '<', self.start_date))
                if self.end_date:
                    conditions.append(('date', '<=', self.end_date))
                no_before = 0.0
                co_before = 0.0
                before_data = self.env['account.move.line'].search(condition_before)
                for data_line in before_data:
                    if line == 'Các hãng khác':
                        if data_line.product_id.product_tmpl_id.brand_name not in ['LS', 'Schneider']:
                            no_before += data_line.debit
                            co_before += data_line.credit
                    else:
                        if data_line.product_id.product_tmpl_id.brand_name == line:
                            no_before += data_line.debit
                            co_before += data_line.credit
                dauky = no_before - co_before
                total_dauky += dauky
                no_current = 0.0
                co_current = 0.0
                current_data = self.env['account.move.line'].search(conditions)  # , order='partner_id asc, date asc'
                for data_line in current_data:
                    if line == 'Các hãng khác':
                        if data_line.product_id.product_tmpl_id.brand_name not in ['LS', 'Schneider']:
                            no_current += data_line.debit
                            co_current += data_line.credit
                    else:
                        if data_line.product_id.product_tmpl_id.brand_name == line:
                            no_current += data_line.debit
                            co_current += data_line.credit
                total_no += no_current
                total_co += co_current
                line_data.update({
                    'dauky': dauky,
                    'no_current': no_current,
                    'co_current': co_current,
                    'total': dauky + no_current - co_current,
                })
                data_line_report.append(line_data)
            data[account] = {
                'data': data_line_report,
                'total_dauky': total_dauky,
                'total_no': total_no,
                'total_co': total_co,
                'total': total_dauky + total_no - total_co
            }
        return data
    def get_total_from_account(self, start_date, end_date, list_account, has_partner_only=False):
        data = {}
        for account in list_account:
            account_ids = self.env['account.account'].search([('code', '=like', account + "%")])
            conditions = [('account_id', 'in', account_ids.ids)]
            conditions_before = [('account_id', 'in', account_ids.ids)]
            if self.start_date:
                conditions.append(('date', '>=', start_date))
                conditions_before.append(('date', '<', start_date))
            if self.end_date:
                conditions.append(('date', '<=', end_date))

            if has_partner_only:
                conditions_before.append(('partner_id', '!=', False))
                conditions.append(('partner_id', '!=', False))

            aml_before = self.env['account.move.line'].search(conditions_before)
            no_before = 0
            co_before = 0
            for line in aml_before:
                no_before += line.debit
                co_before += line.credit
            dauky = no_before - co_before

            aml = self.env['account.move.line'].search(conditions)
            no_amount = 0
            co_amount = 0
            for line in aml:
                no_amount += line.debit
                co_amount += line.credit
            data[account] = {
                'dauky': dauky,
                'no_amount': no_amount,
                'co_amount': co_amount,
                'total': dauky + no_amount - co_amount
            }
        return data




