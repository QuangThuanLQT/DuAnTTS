# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models, _


class account_code(models.Model):
    _name = 'account.code'
    _auto = False
    

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        res = []
        for journal in self:
            currency = journal.code 
            name = "%s  %s" % (currency, journal.name)
            res += [(journal.id, name)]
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            account_code_ids = self.env['account.code'].search([('code', 'ilike', name)])
            args += ['|', ('id', 'in', account_code_ids.ids)]
        res = super(account_code, self.with_context(name_search_so=True)).name_search(name=name, args=args,
                                                                                    operator=operator, limit=limit)
        return res
    
    name = fields.Char("Name")
    code = fields.Char("Code")
    def _select(self):
        select_str = """
             SELECT min(aa.id) as id,
                     aa.code as code,
                     aa.name as name
        """
        return select_str

    def _from(self):
        from_str = """
                account_account aa
        """
        return from_str

    
    def _group_by(self):
        group_by_str = """
            GROUP BY aa.code,aa.name
        """
        return group_by_str
    
    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE or REPLACE VIEW %s as (
            %s
            FROM  %s 
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by())
        self.env.cr.execute(query)
    

class CoaWizard(models.TransientModel):
    _name = "coa.wizard"
    _description = "Chart Of Accounts"

    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'), ('all', 'All Entries')], 'Target Moves', default='posted')
    code = fields.Many2one('account.code',string="Code")
    account_currency = fields.Many2one('res.currency',string="Currency")
    company_id = fields.Many2one('res.company',string="Company")
    type_id = fields.Many2one('account.account.type',string="Type")

    @api.multi
    def chart_of_account_open_window(self):
        result_context = {}
        result_domain = []
        action = self.env.ref('clickable_chartofaccount.action_chart_of_accounts_tree').read()[0]
        result_context.update({'target_move': self.target_move})
        if self.date_from:
            result_context.update({'date_from': self.date_from})
        if self.date_to:
            result_context.update({'date_to': self.date_to, })
        if self.type_id:
            result_domain.append(('user_type_id','=',self.type_id.id))
        if self.account_currency:
            result_domain.append(('currency_id','=', self.account_currency.id))
        if self.company_id:
            result_domain.append(('company_id','=', self.company_id.id))
        if self.code:
            result_domain.append(('code','=', self.code.code))
        if result_context:
            action['context'] = str(result_context)
            action['domain']=str(result_domain)
        return action
    
    


CoaWizard()
