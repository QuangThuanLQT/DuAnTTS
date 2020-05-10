# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning

class ResCompany(models.Model):
    _inherit = "res.company"

    min_days_between_followup = fields.Integer('Minimum days between two follow-ups', help="Use this if you want to be sure than a minimum number of days occurs between two follow-ups.", default=6)

class followup(models.Model):
    _name = 'account_followup.followup'
    _description = 'Account Follow-up'
    _rec_name = 'name'

    followup_line_ids = fields.One2many('account_followup.followup.line', 'followup_id', 'Follow-up', copy=True, oldname="followup_line")
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account_followup.followup'))
    name = fields.Char(related='company_id.name', readonly=True)

    _sql_constraints = [('company_uniq', 'unique(company_id)', 'Only one follow-up per company is allowed')]


class followup_line(models.Model):
    _name = 'account_followup.followup.line'
    _description = 'Follow-up Criteria'
    _order = 'delay'

    @api.one
    def _get_default_template(self):
        try:
            return self.env.get('ir.model.data').get_object_reference('account_followup', 'email_template_account_followup_default')[1]
        except ValueError:
            return False

    name = fields.Char('Follow-Up Action', required=True, translate=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of follow-up lines.")
    delay = fields.Integer('Due Days', required=True,
                           help="The number of days after the due date of the invoice to wait before sending the reminder.  Could be negative if you want to send a polite alert beforehand.")
    followup_id = fields.Many2one('account_followup.followup', 'Follow Ups', required=True, ondelete="cascade")
    description = fields.Text('Printed Message', translate=True, default="""
        Dear %(partner_name)s,

Exception made if there was a mistake of ours, it seems that the following amount stays unpaid. Please, take appropriate measures in order to carry out this payment in the next 8 days.

Would your payment have been carried out after this mail was sent, please ignore this message. Do not hesitate to contact our accounting department.

Best Regards,
""")
    send_email = fields.Boolean('Send an Email', help="When processing, it will send an email", default=True)
    send_letter = fields.Boolean('Send a Letter', help="When processing, it will print a letter", default=True)
    manual_action = fields.Boolean('Manual Action', help="When processing, it will set the manual action to be taken for that customer. ", default=False)
    manual_action_note = fields.Text('Action To Do', placeholder="e.g. Give a phone call, check with others , ...")
    manual_action_responsible_id = fields.Many2one('res.users', 'Assign a Responsible', ondelete='set null')
    email_template_id = fields.Many2one('mail.template', 'Email Template', ondelete='set null',
                                        default=lambda self: self._get_default_template())

    _sql_constraints = [('days_uniq', 'unique(followup_id, delay)', 'Days of the follow-up levels must be different')]

    @api.constrains('description')
    def _check_description(self):
        for line in self:
            if line.description:
                try:
                    line.description % {'partner_name': '', 'date':'', 'user_signature': '', 'company_name': ''}
                except:
                    raise Warning(_('Your description is invalid, use the right legend or %% if you want to use the percent character.'))

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.one
    @api.depends('debit', 'credit')
    def _get_result(self):
        self.result = self.debit - self.credit

    followup_line_id = fields.Many2one('account_followup.followup.line', 'Follow-up Level',
                                       ondelete='restrict') #restrict deletion of the followup line
    followup_date = fields.Date('Latest Follow-up', index=True)
    result = fields.Monetary(compute='_get_result', method=True, string="Balance") #'balance' field is not the same