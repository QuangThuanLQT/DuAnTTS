from odoo import models, fields, api,_

class account_voucher_line(models.Model):
    _inherit = 'account.voucher.line'

    @api.model
    def default_get(self, fields):
        res = super(account_voucher_line, self).default_get(fields)
        if self.env.context.get('collect_type',False):
            collect_type = self.env.context.get('collect_type',False)
            if collect_type == 'sale':
                res['account_id'] = self.env['account.account'].search([('code','=','131')]).id or False
        if self.env.context.get('pay_type',False):
            pay_type = self.env.context.get('pay_type',False)
            if pay_type == 'manager_pay':
                res['account_id'] = self.env['account.account'].search([('code', '=', '6428')]).id or False
            elif pay_type == 'other_pay':
                res['account_id'] = self.env['account.account'].search([('code', '=', '6427')]).id or False
            elif pay_type == 'payroll':
                res['account_id'] = self.env['account.account'].search([('code', '=', '3341')]).id or False
            elif pay_type == 'community_pay':
                res['account_id'] = self.env['account.account'].search([('code', '=', '3381')]).id or False
            elif pay_type == 'project_cost':
                res['account_id'] = self.env['account.account'].search([('code', '=', '632')]).id or False
            elif pay_type == 'other_cost':
                res['account_id'] = self.env['account.account'].search([('code', '=', '811')]).id or False
        return res

    def _get_name_of_line(self):
        if 'voucher_type' in self._context and self._context['voucher_type'] == 'sale':
            return 'Thu'
        if 'voucher_type' in self._context and self._context['voucher_type'] == 'purchase':
            return 'Chi'

    name = fields.Text(string='Description', default=_get_name_of_line, required=True)