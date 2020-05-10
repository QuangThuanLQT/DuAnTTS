# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class account_voucher(models.Model):
    _inherit = 'account.voucher'

    def _get_number_voucher(self):
        phieuthu_action  = self.env.ref('account_voucher.action_sale_receipt')
        phieuchi_action = self.env.ref('account_voucher.action_purchase_receipt')
        if self._context and 'params' in self._context and 'action' in self._context['params']:
            if self._context['params'].get('action') == phieuchi_action.id:
                # sequence = self.env['ir.sequence'].search([('code', '=', 'seq_account_chi')], limit=1)
                # next = sequence.get_next_char(sequence.number_next_actual)
                # return str(int(next) + 1)
                phieuchi = self.env['account.voucher'].search([
                    ('journal_id.type', '=', 'purchase'),
                    ('voucher_type', '=', 'purchase'),
                    ('number_voucher', '!=', False)
                ], order="number_voucher_sub desc", limit=1)
                number = 0
                if phieuchi and phieuchi.number_voucher:
                    try:
                        number = int(phieuchi.number_voucher.split("-")[0])
                    except:
                        pass
                else:
                    number = 0
                return number + 1
            elif self._context['params'].get('action') == phieuthu_action.id:
                # sequence = self.env['ir.sequence'].search([('code', '=', 'seq_account_thu')], limit=1)
                # next = sequence.get_next_char(sequence.number_next_actual)
                # return str(int(next) + 1)
                phieuthu = self.env['account.voucher'].search([
                    ('journal_id.type', '=', 'sale'),
                    ('voucher_type', '=', 'sale'),
                    ('number_voucher', '!=', False)
                ], order="number_voucher_sub desc", limit=1)
                number = 0
                if phieuthu and phieuthu.number_voucher:
                    try:
                        number = int(phieuthu.number_voucher.split("-")[0])
                    except:
                        pass
                else:
                    number = 0
                return number + 1


    number_voucher = fields.Char(string="Number Voucher", default=_get_number_voucher)
    number_voucher_sub = fields.Integer(string="Number Voucher",compute='_get_number_voucher',store=True)
    pay_now = fields.Selection([
        ('pay_now', 'Pay Directly'),
        ('pay_later', 'Pay Later'),
    ], 'Payment', index=True, readonly=True, states={'draft': [('readonly', False)]}, default='pay_now')
    collect_type = fields.Selection([('sale','Collect Sale')], string='Collect Type', default='sale')
    pay_type = fields.Selection([('manager_pay','Chi tiền quản lý'),('other_pay','Chi tiền khác'),
                                     ('payroll','Chi tiền lương'),('community_pay','Chi tiền cộng đồng'),('project_cost','Chi phí dự án'),
                                     ('other_cost','Chi phí khác')
                                     ], string='Loại')
    explain = fields.Char(string="Explain", compute="_get_account_from_line")
    explain_sub = fields.Char(string="Diễn giải")
    account_line_id = fields.Many2one('account.account', string="Account", compute=False, related='line_ids.account_id')
    account_line_id_sub = fields.Many2many('account.account', string="Tài Khoản", compute="_get_account_from_line")
    record_checked = fields.Boolean('Done')

    @api.depends('number_voucher')
    def _get_number_voucher(self):
        for rec in self:
            number = 0
            try:
                number = int(rec.number_voucher)
            except:
                pass
            rec.number_voucher_sub = number


    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        move_line = super(account_voucher, self).first_move_line_get(move_id, company_currency, current_currency)
        if move_line and move_line.get('name', False) == '/':
            if self.line_ids and len(self.line_ids):
                move_line.update({
                    'name': ', '.join([line.name or '' for line in self.line_ids]),
                })
        return move_line

    @api.onchange('date')
    def onchange_date(self):
        for record in self:
            if record.date:
                record.account_date = record.date

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    def update_check_account_voucher(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.record_checked = False


    # @api.model
    # def create(self, values):
    #     phieuthu_action = self.env.ref('account_voucher.action_sale_receipt')
    #     phieuchi_action = self.env.ref('account_voucher.action_purchase_receipt')
    #     if self._context and 'params' in self._context and 'action' in self._context['params']:
    #         if self._context['params'].get('action') == phieuthu_action.id:
    #             sequence = self.env['ir.sequence'].next_by_code('seq_account_thu')
    #             # values['number_voucher'] = str(int(sequence))
    #         elif self._context['params'].get('action') == phieuchi_action.id:
    #             sequence = self.env['ir.sequence'].next_by_code('seq_account_chi')
    #             # values['number_voucher'] = str(int(sequence))
    #     line = super(account_voucher, self).create(values)
    #     return line

    @api.multi
    def account_move_get(self):
        move = super(account_voucher, self).account_move_get()
        move.update({
            'ref' : self.number_voucher,
        })
        return move

    @api.multi
    def _get_account_from_line(self):
        for record in self:
            record.explain = ""
            record.account_line_id = False
            for line in record.line_ids:
                if line.name:
                    record.explain += line.name + ", "
                if line.account_id:
                    record.account_line_id_sub = [(4,line.account_id.id)]
            # if record.explain_sub != record.explain:
            #     explain_sub_spl = record.explain_sub.split(',')
            #     explain_spl = record.explain.split(',')
            #     for i in range(0,len(explain_sub_spl)):
            #         if explain_sub_spl[i] != explain_spl[i]:
            #             record.line_ids.filtered(lambda l: l.name == explain_spl[i]).write({
            #                 'name' : explain_sub_spl[i]
            #             })
            if record.explain_sub != record.explain:
                record.write({
                    'explain_sub': record.explain
                })


    @api.model
    def default_get(self, fields):
        res = super(account_voucher, self).default_get(fields)
        res.update({
            'payment_journal_id': 5,
        })
        return res

    @api.depends('company_id', 'pay_now', 'account_id')
    def _compute_payment_journal_id(self):
        super(account_voucher, self)._compute_payment_journal_id()
        for voucher in self:
            if voucher.pay_now != 'pay_now':
                continue
            domain = [
                ('type', '=', 'cash'),
                ('company_id', '=', voucher.company_id.id),
            ]
            voucher.payment_journal_id = self.env['account.journal'].search(domain, limit=1)
            voucher.account_id = voucher.payment_journal_id.default_debit_account_id

    @api.multi
    def multi_proforma_voucher(self):
        ids = self.env.context.get('active_ids', [])
        account_voucher_ids = self.browse(ids)
        for voucher_id in account_voucher_ids:
            if voucher_id.state in ('draft'):
                voucher_id.proforma_voucher()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        return super(account_voucher, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
