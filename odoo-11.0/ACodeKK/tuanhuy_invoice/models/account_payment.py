# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class account_payment_inherit(models.Model):
    _inherit = 'account.payment'

    original_documents = fields.Char('Original documents')

    # _sql_constraints = [
    #     ('original_documents_unique', 'UNIQUE(original_documents)',
    #      'Unfortunately this original documents is already used, please choose a unique one')
    # ]

    @api.onchange('original_documents')
    def onchange_original_documents(self):
        if self.original_documents:
            original_documents = self.search([('original_documents', '=', self.original_documents)])
            if original_documents:
                warning = {
                    'title': _("Warning"),
                    'message': "Unfortunately this original documents is already used, please choose a unique one"
                }
                return {'warning': warning}
                # raise UserError(_("Unfortunately this original documents is already used, please choose a unique one"))
            else:
                journal_id = self.env['account.journal'].search([('type', 'in', ['cash']),('at_least_one_outbound', '=', True), ('name', '=', 'Cash')])
                if journal_id:
                    self.journal_id = journal_id[0].id

    # @api.model
    # def default_get(self, fields):
    #     rec = super(account_payment_inherit, self).default_get(fields)
    #     rec['communication'] = False
    #     return rec



