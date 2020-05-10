# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime, date,timedelta
from dateutil.relativedelta import relativedelta


import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class ReportAccountFinancialReport_inheirt(models.Model):
    _inherit = "account.financial.html.report"

    @api.multi
    def get_lines(self, context_id, line_id=None):
        res = super(ReportAccountFinancialReport_inheirt, self).get_lines(context_id, line_id)
        tyso_taichinh = self.env.ref('report_cac_ty_so_tai_chinh.tuanhuy_tyso_taichinh_report')
        if self.id == tyso_taichinh.id:
            date1 = datetime.now()
            date2 = date1 - relativedelta(months=3)
            date3 = date2 - relativedelta(months=3)
            date4 = date3 - relativedelta(months=3)
            date5 = date4 - relativedelta(months=3)

            for line in (filter(lambda x: x['level'] == 0, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    line['report'] = [number, "", '{0:,.1f}'.format(record.current_year) if number else "",
                                      '{0:,.1f}'.format(record.last_year) if number else "", "", ""]
            for line in (filter(lambda x: x['level'] == 1, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    code = record.code if record.code else ""
                    if code == 'tinh_thanh_khoan':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '1%'),  # Tien
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('debit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('credit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '3%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = 'Dòng tiền về kịp để thanh toán nợ'
                        if q1_value < 1:
                            message = 'Cảnh báo: Dòng tiền về không kịp để thanh toán nợ'

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]
                    if code == 'cau_truc_von':
                        line['report'] = ["", "", "", "", "",
                                          "Doanh nghiệp có đang vay nợ quá nhiều? Tài sản có ‘Đủ’ trả nợ"]
                    if code == 'kha_nang_sinh_loi':
                        line['report'] = ["", "", "", "", "",
                                          "Doanh nghiệo có tạo ra lợi nhuận ‘bền vững’ từ hoạt động kinh doanh"]
                    if code == 'hieu_qua_sd_tai_san':
                        line['report'] = ["", "", "", "", "",
                                          "Chiến lượt doanh nghiệp sẽ ảnh hưởng đến hiệu quả sử dụng tài sản"]
                    if code == 'kha_nang_sinh_tien':
                        line['report'] = ["", "", "", "", "",
                                          "Độ mạnh của khả năng sinh tiền - Dòng tiền là chỉ số kết quả"]
            for line in (filter(lambda x: x['level'] == 2, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    code = record.code if record.code else ''
                    if code == 'kntt_no_ngan_han':

                        short_asset_items = self.env['account.move.line'].search([
                            '|', '|', '|',
                            ('account_id.code', '=like', '11%'), # Tien
                            ('account_id.code', '=like', '131%'), # Cong No
                            ('account_id.code', '=like', '141%'),  # Tam Ung
                            ('account_id.code', '=like', '15%'), # Ton Kho
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('debit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('credit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '3%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = 'Khả năng thanh toán ngắn hạn tốt'
                        if q1_value < 1:
                            message = 'Cảnh báo: tài sản ngắn hạn không đủ bù đắp cho nợ ngắn hạn'

                        line['report'] = ['%.2f' %(q1_value), '', '', '', '', message]

                    if code == 'kntt_nhanh':

                        short_asset_items = self.env['account.move.line'].search([
                            '|', '|',
                            ('account_id.code', '=like', '11%'),  # Tien
                            ('account_id.code', '=like', '131%'),  # Cong No
                            ('account_id.code', '=like', '141%'),  # Tam Ung
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('debit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('credit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '3%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = 'Khả năng thanh toán nhanh tốt'
                        if q1_value < 1:
                            message = 'Cảnh báo: Khả năng thanh toán nhanh ở mức thấp'

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'kntt_tuc_thoi':

                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '11%'),  # Tien
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('debit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('credit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '3%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = 'Khả năng thanh toán tức thời tốt'
                        if q1_value < 1:
                            message = 'Cảnh báo: Khả năng thanh toán tức thời ở mức thấp'

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'no_ngan_hang_von_csh':

                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '34%'),  # Vay
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '411%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = ''
                        if q1_value > 1:
                            message = 'Cảnh báo: Khoản vay vượt vốn chủ sở hữu'

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'kntt_lai_vay':
                        line['report'] = ['', '', '', '', '', '']
                    if code == 'tong_no_tong_ts':

                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '34%'),  # Vay
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '1%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = ''
                        if q1_value > 1:
                            message = 'Cảnh báo: Công ty đang vay nợ ở mức rất cao'

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'tong_no_con_csh':

                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '34%'),  # Vay
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '411%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit)

                        message = ''
                        if q1_value > 1:
                            message = 'Cảnh báo: Đòn bẩy tài chính với hệ số cao'

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'tang_truong_dt':
                        line['report'] = ["", "", "", "", "", "Doanh thu Q1|2016 giảm 14.39% so với Q4|2015"]
                    if code == 'ty_trong_lng':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '911%'),  # Vay
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '511%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit) * 100

                        message = ''
                        if q1_value > 1:
                            message = ''

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]
                    if code == 'doanh_thu_thuan':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '911%'),  # Vay
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '511%'),
                            ('date', '<=', date1)
                        ])
                        shot_debit_items_return = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '521%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items_return.mapped('debit')) if shot_debit_items_return else 0)

                        q1_value = (short_asset / short_debit) * 100

                        message = ''
                        if q1_value > 1:
                            message = ''

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]
                    if code == 'loi_nhuan_von_csh':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '911%'),  # Vay
                            ('date', '<=', date1)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (
                        sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '411%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('debit')) if shot_debit_items_return else 0)

                        q1_value = (short_asset / short_debit) * 100

                        message = ''
                        if q1_value > 1:
                            message = ''

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'loi_nhuan_von_csh_no_dai_han':
                        line['report'] = ["", "", "", "", "", ""]

                    if code == 'doanh_thu_tong_ts':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '511%'),  # DT
                            ('date', '<=', date1),
                            ('date', '>=', date2)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '1%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit) * 100

                        message = ''
                        if q1_value > 1:
                            message = ''

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]
                    if code == 'loi_nhuan_tong_ts':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '911%'),  # LN
                            ('date', '<=', date1),
                            ('date', '>=', date2)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '1%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit) * 100

                        message = ''
                        if q1_value > 1:
                            message = ''

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]
                    if code == 'suc_san_xuat_cua_tscd':
                        short_asset_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '821%'),  # LN
                            ('date', '<=', date1),
                            ('date', '>=', date2)
                        ])
                        short_asset = (sum(short_asset_items.mapped('credit')) if short_asset_items else 0) - (sum(short_asset_items.mapped('debit')) if short_asset_items else 0)

                        shot_debit_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '1%'),
                            ('date', '<=', date1)
                        ])
                        short_debit = (sum(shot_debit_items.mapped('debit')) if shot_debit_items else 0) - (sum(shot_debit_items.mapped('credit')) if shot_debit_items else 0)

                        q1_value = (short_asset / short_debit) * 100

                        message = ''
                        if q1_value > 1:
                            message = ''

                        line['report'] = ['%.2f' % (q1_value), '', '', '', '', message]

                    if code == 'chu_ky_tien_mat':
                        line['report'] = ["", "", "", "", "", ""]
                    if code == 'dong_tien_hdkd_doanh_thu_thuan':
                        line['report'] = ["", "", "", "", "", "Công ty có khả năng sinh tiền từ HĐKD thấp"]

        return res

    def get_template(self):
        res = super(ReportAccountFinancialReport_inheirt, self).get_template()
        tyso_taichinh = self.env.ref('report_cac_ty_so_tai_chinh.tuanhuy_tyso_taichinh_report')
        if tyso_taichinh and self.id == tyso_taichinh.id:
            return 'report_cac_ty_so_tai_chinh.report_ty_so_tai_chinh'
        return res

class AccountFinancialReportContext_inherit(models.TransientModel):
    _inherit = 'account.financial.html.report.context'

    def check_quy(self,date):
        if date.month and date.month in (1, 2, 3):
            return 'Q1'
        if date.month and date.month in (4, 5, 6):
            return 'Q2'
        if date.month and date.month in (7, 8, 9):
            return 'Q3'
        if date.month and date.month in (10, 11, 12):
            return 'Q4'

    def get_columns_names(self):
        res = super(AccountFinancialReportContext_inherit, self).get_columns_names()
        ref = self.env.ref('report_cac_ty_so_tai_chinh.tuanhuy_tyso_taichinh_report')
        if self.report_id and self.report_id.id == ref.id:
            date1 = datetime.now()
            date2 = date1 - relativedelta(months=3)
            date3 = date2 - relativedelta(months=3)
            date4 = date3 - relativedelta(months=3)
            date5 = date4 - relativedelta(months=3)
            q1 = self.check_quy(date1) + '|%s' % (date1.year)
            q2 = self.check_quy(date2) + '|%s' % (date2.year)
            q3 = self.check_quy(date3) + '|%s' % (date3.year)
            q4 = self.check_quy(date4) + '|%s' % (date4.year)
            q5 = self.check_quy(date5) + '|%s' % (date5.year)
            return [
                _('Khoản Mục'),
                _(q1),
                _(q2),
                _(q3),
                _(q4),
                _(q5),
                _('Ghi Chú')
            ]
        return res

    @api.multi
    def get_columns_types(self):
        res = super(AccountFinancialReportContext_inherit, self).get_columns_types()
        ref = self.env.ref('report_cac_ty_so_tai_chinh.tuanhuy_tyso_taichinh_report')
        if self.report_id and self.report_id.id == ref.id:
            return [
                'text',
                'number',
                'number',
                'number',
                'number',
                'number',
                'text'
            ]
        return res

    @api.multi
    def get_with_columns(self):
        return ['30%','6%','6%','6%','6%','6%','40%']