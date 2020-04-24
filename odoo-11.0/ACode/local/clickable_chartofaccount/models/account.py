from odoo import models, fields, api, _
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    type = fields.Selection(selection_add=[('view', 'View')])

AccountAccountType()

class Account(models.Model):
    _inherit = 'account.account'

    @api.multi
    def _compute_account_debit_credit_balance(self):
        for acc in self:
            data_list = []
            if self._context.get('date_from'):
                date_from = self._context.get('date_from')
            else:
                date_from = False
    
            if self._context.get('date_to'):
                date_to = self._context.get('date_to')
            else:
                date_to = False
    
            if self._context.get('target_move') and self._context.get('target_move') == 'all':
                target_move = ['draft', 'posted']
            else:
                target_move = ['posted']
            date_list =[]
            #Fetch data list from account move line based on selected parameters
            if self._context.get('target_move') and self._context.get('date_from') and self._context.get('date_to'):
                data_list = self.env['account.move.line'].search([('account_id','=',acc.id),
                                                                  ('move_id.state','in',target_move),
                                                                  ('date','>=',date_from),
                                                                  ('date','<=',date_to)])
            elif self._context.get('target_move') and self._context.get('date_from') and not self._context.get('date_to'):
                data_list = self.env['account.move.line'].search([('account_id','=',acc.id),
                                                                  ('move_id.state','in',target_move),
                                                                  ('date','>=',date_from)])
            elif self._context.get('target_move') and not self._context.get('date_from') and self._context.get('date_to'):
                data_list = self.env['account.move.line'].search([('account_id','=',acc.id),
                                                                  ('move_id.state','in',target_move),
                                                                  ('date','<=',date_to)])
            elif self._context.get('target_move') and not self._context.get('date_from') and not self._context.get('date_to'):
                data_list = self.env['account.move.line'].search([('account_id','=',acc.id),
                                                                  ('move_id.state','in',target_move)])
            #Assigned credit debit value to fields of account
            if len(data_list)>0:
                debit = 0.0
                credit = 0.0
                balance = 0.0
                for each_data in data_list:
                    debit += each_data.debit
                    credit += each_data.credit
                acc.debit = debit
                acc.credit = credit
                acc.balance = (debit-credit)

    parent_id = fields.Many2one('account.account', string='Parent')
    child_account_ids = fields.One2many('account.account', 'parent_id', string='Child Accounts')
    balance = fields.Monetary(compute='_compute_account_debit_credit_balance', string='Balance')
    debit = fields.Monetary(compute='_compute_account_debit_credit_balance', string='Debit')
    credit = fields.Monetary(compute='_compute_account_debit_credit_balance', string='Credit')