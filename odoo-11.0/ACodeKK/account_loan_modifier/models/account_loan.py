# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging
import math

class AccountLoanPost(models.TransientModel):
    _inherit = "account.loan.post"

    loan_id = fields.Many2one('account.loan',required=False)


class account_loan_modifier(models.Model):
    _inherit = 'account.loan'

    asset_ids = fields.Many2many('account.asset.asset', string='Mã tài sản thế chấp')
    period_number = fields.Integer('Số kỳ hoàn thành')
    # asset_value_ids = fields.One2many('account.asset.value','loan_id',string='Mã tài sản thế chấp')

    estimate_value_ids = fields.One2many('account.asset.value', 'loan_id', string='Tài sản thế chấp')
    color = fields.Char(compute='get_color_view')
    tien_con_no = fields.Monetary(currency_field='currency_id', string='Số tiền còn nợ ',compute='compute_theo_ky',)
    tien_tra_goc_theo_ky = fields.Monetary(currency_field='currency_id', string='Số tiền trả gốc theo kỳ',compute='compute_theo_ky',)
    tien_lai_theo_ky = fields.Monetary(currency_field='currency_id', string='Số tiền lãi theo kỳ',compute='compute_theo_ky',)
    end_date = fields.Date('Ngày đáo hạn',compute='compute_theo_ky')
    remain_period = fields.Integer('Số kỳ còn lại',compute='compute_theo_ky')
    asset_code = fields.Char('Mã tài sản thế chấp',compute='get_asset_code')
    average_rate = fields.Float('Lãi suất bình quân',compute='compute_theo_ky',digits=(8, 6))

    @api.multi
    def unlink(self):
        self.env['account.loan.post'].search([('loan_id','in',self.ids)]).unlink()
        move_ids = self.env['account.move'].search([('loan_id','in',self.ids)])
        if move_ids:
            move_ids.button_cancel()
            move_ids.unlink()
        res = super(account_loan_modifier, self).unlink()
        return res

    @api.multi
    def get_asset_code(self):
        for record in self:
            if record.estimate_value_ids:
               record.asset_code = ', '.join([line.asset_id.asset_id.account_asset_code or '' for line in record.estimate_value_ids])


    @api.multi
    def compute_theo_ky(self):
        today = datetime.now().date().strftime(DF)
        for record in self:
            if record.line_ids.mapped('date'):
                record.end_date = max(record.line_ids.mapped('date'))
            line_id = self.env['account.loan.line'].search([('loan_id','=',record.id),('date','>=',today)],order='date asc',limit=1)
            if record.line_ids and record.line_ids.mapped('rate'):
                record.average_rate = sum(record.line_ids.mapped('rate'))/len(record.line_ids)
            if line_id:
                record.tien_con_no = line_id.pending_principal_amount
                record.tien_tra_goc_theo_ky = line_id.principal_amount
                record.tien_lai_theo_ky = line_id.interests_amount
                record.remain_period = len(self.env['account.loan.line'].search([('loan_id','=',record.id),('date','>=',today)],order='date asc').ids)
            else:
                record.tien_con_no = record.tien_tra_goc_theo_ky = record.tien_lai_theo_ky = record.remain_period = 0

    def compute_posted_lines(self):
        """
        Recompute the amounts of not finished lines. Useful if rate is changed
        """
        amount = self.loan_amount
        for line in self.line_ids.sorted('sequence'):
            if line.move_ids:
                amount = line.final_pending_principal_amount
            else:
                line.rate = self.rate_period
                line.pending_principal_amount = amount
                line.check_amount()
                amount -= line.principal_amount
                line.payment_amount = line.principal_amount + line.interests_amount
        if self.long_term_loan_account_id:
            self.check_long_term_principal_amount()

    @api.multi
    def compute_draft_lines(self):
        self.ensure_one()
        self.fixed_periods = self.periods
        self.fixed_loan_amount = self.loan_amount
        self.line_ids.unlink()
        amount = self.loan_amount
        if self.start_date:
            date = datetime.strptime(self.start_date, DF).date()
        else:
            date = datetime.today().date()
        delta = relativedelta(months=self.method_period)
        if not self.payment_on_first_period:
            date += delta
        for i in range(1, self.periods + 1):
            line = self.env['account.loan.line'].create(
                self.new_line_vals(i, date, amount)
            )
            line.check_amount()
            date += delta
            amount -= line.principal_amount
        if self.long_term_loan_account_id:
            self.check_long_term_principal_amount()

    @api.multi
    def get_color_view(self):
        for record in self:
            move_ids = self.env['account.move'].search([('loan_id', '=', record.id)])
            record.color = ''
            if record.state == 'posted':
            # CKV đang mở : màu xanh biển
                record.color = 'blue'
            # CKV quá hạn chưa làm bút toán : màu hồng
                value = []
                for line in record.line_ids:
                    current_day = datetime.now().date()
                    date_day = datetime.strptime(line.date, DF).date()
                    if date_day < current_day:
                        value.append(line)
                    for line in value:
                        move_id = move_ids.filtered(lambda r: r.date == line.date)
                        if move_id:
                            True
                        else:
                            record.color = 'pink'

            # CKV còn 3 ngày nữa đến hạn trả tiền lãi,gốc : màu đỏ
                    if date_day.month < current_day.month and date_day.year == current_day.year:
                        True
                    else:
                        if (date_day - current_day).days >= 0 and (date_day - current_day).days <= 3:
                            record.color = 'red'
            # CKV đang soạn thảo : màu cam đậm
            if record.state == 'draft':
                record.color = 'orange'
            # CKV đã huỷ / hết hạn : màu xám
            if record.state == 'cancelled':
                record.color = 'gray'
            if record.line_ids:
                max_date = max([line.date for line in record.line_ids])
                if max_date:
                    current_day = datetime.now().date()
                    date_day = datetime.strptime(max_date, DF).date()
                    if date_day.year < current_day.year:
                        record.color = 'gray'
                    if date_day.month < current_day.month and date_day.year == current_day.year:
                        record.color = 'gray'
                    if date_day.month == current_day.month and date_day.year == current_day.year:
                        if date_day < current_day:
                            record.color = 'gray'

    @api.depends('line_ids', 'currency_id', 'loan_amount')
    def _compute_total_amounts(self):
        for record in self:
            lines = record.line_ids.filtered(lambda r: r.move_ids)
            record.payment_amount = sum(lines.mapped('principal_amount')) or 0.
            record.interests_amount = sum(lines.mapped('interests_amount')) or 0.
            record.pending_principal_amount = record.loan_amount - record.payment_amount


class account_asset_value(models.Model):
    _name = 'account.asset.value'

    # asset_id = fields.Many2one('account.asset.asset', string='Định giá thế chấp')
    asset_id = fields.Many2one('bank.estimate', string='Định giá thế chấp')
    mortgage_value = fields.Float(string='Giá trị tài sản đã thế chấp', related='asset_id.mortgage_value')
    loan_id = fields.Many2one('account.loan')
    amount  = fields.Float(string='Giá trị tài sản thế chấp')
    remaind_value = fields.Float(string='Giá trị tài sản còn lại', related='asset_id.remaind_value')
    account_guarantee_id = fields.Many2one('account.guarantee')

    @api.onchange('asset_id')
    def onchange_remaind_value(self):
        if self.remaind_value > self.loan_id.loan_amount:
            self.amount = self.loan_id.loan_amount
        else:
            self.amount = self.remaind_value

class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    already_asset_value = fields.Float(string='Giá trị tài sản đã thế chấp',compute='get_already_asset_value')

    @api.multi
    def get_already_asset_value(self):
        for record in self:
            value_ids = self.env['account.asset.value'].sudo().search([('asset_id','=',record.id or False),('loan_id.state','=','posted')])
            record.already_asset_value = sum(value_ids.mapped('amount'))

class account_guarantee(models.Model):
    _inherit = 'account.guarantee'

    asset_ids = fields.Many2many('account.asset.asset', string='Mã tài sản thế chấp')
    estimate_value_ids = fields.One2many('account.asset.value', 'account_guarantee_id', string='Tài sản thế chấp')
    color = fields.Char(compute='get_color_view')

    @api.multi
    def get_color_view(self):
        for record in self:
            record.color = ''
            if record.state == 'approved':
                # BL Chấp thuận: màu xanh biển
                record.color = 'blue'
                # BL còn 3 ngày đến hạn : màu đỏ
                current_day = datetime.now().date()
                date_day = datetime.strptime(record.end_date, DF).date()
                if date_day.month == current_day.month and date_day.year == current_day.year and record.guarantee_type_id == self.env.ref('account_guarantee.guarantee_type_4'):
                    if (date_day - current_day).days >= 0 and (date_day - current_day).days <= 3:
                        record.color = 'red'
            # BL đang soạn thảo : màu cam đậm
            if record.state == 'draft':
                record.color = 'orange'
            if record.state == 'requested':
                record.color = 'pink'

class account_bank(models.Model):
    _inherit = 'bank.estimate'

    loan_ids = fields.Many2many('account.loan', compute='get_loan_id')
    guarantee_ids = fields.Many2many('account.guarantee', compute='get_guarantee_id')
    color = fields.Char(compute='get_color_view')

    @api.multi
    def get_color_view(self):
        for record in self:
            record.color = ''
            if record.state == 'ready':
            # TSCCTC sẵn sàng hoặc đang hoạt động: màu xanh biển
                record.color = 'blue'
            if record.state == 'progress':
                record.color = 'blue'
                # TSCCTC đang hoạt động, hết hạn mức: màu đỏ
                if record.mortgage_value > 0 and record.remaind_value <= 0 :
                    record.color = 'red'
                # TSCCTC đang hoạt động, còn 1 tháng nữa giải phóng: màu xanh lá
                for loan_id in record.loan_ids:
                    max_date = max(line.date for line in loan_id.line_ids)
                    if max_date:
                        current_day = datetime.now().date()
                        date_day = datetime.strptime(max_date, DF).date()
                        if (date_day - current_day).days >= 0 and (date_day - current_day).days <= 30:
                            record.color = 'green'
                # TSCCTC đang hoạt động, CKV hết hạn: màu xám
                    last_date = ''
                    if max_date > last_date:
                            last_date = max_date
                    if max_date:
                            current_day = datetime.now().date()
                            date_day = datetime.strptime(last_date, DF).date()
                            if date_day.year < current_day.year:
                                record.color = 'gray'
                            if date_day.month < current_day.month and date_day.year == current_day.year:
                                record.color = 'gray'
                            if date_day.month == current_day.month and date_day.year == current_day.year:
                                if date_day < current_day:
                                    record.color = 'gray'



            # TSCCTC đang soạn thảo : màu cam đậm
            if record.state == 'draft':
                record.color = 'orange'
            # TSCCTC đã huỷ : màu xám
            if record.state == 'cancelled':
                record.color = 'gray'

    @api.multi
    def get_loan_id(self):
        for record in self:
            list = []
            value_ids = self.env['account.asset.value'].search([('loan_id', '!=', False)])
            for line in value_ids:
                if line.asset_id == record and line.loan_id.id not in list:
                    list.append(line.loan_id.id)
            record.loan_ids = [(6, 0, list)]

    @api.multi
    def get_guarantee_id(self):
        for record in self:
            list = []
            value_ids = self.env['account.asset.value'].search([('account_guarantee_id', '!=', False)])
            for line in value_ids:
                if line.asset_id == record and line.account_guarantee_id.id not in list:
                    list.append(line.account_guarantee_id.id)
            record.guarantee_ids = [(6, 0, list)]

