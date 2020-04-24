# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from lxml import etree
from . import account_followup_print
from odoo.exceptions import Warning

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(res_partner, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                          toolbar=toolbar, submenu=submenu)

        if view_type == 'form' and self._context.get('followupfirst'):
            doc = etree.XML(res['arch'], parser=None, base_url=None)
            first_node = doc.xpath("//page[@name='followup_tab']")
            root = first_node[0].getparent()
            root.insert(0, first_node[0])
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def _get_latest(self):
        for partner in self:
            if partner.company_id == None:
                company = self.env.get('res.users').browse(self._uid).company_id
            else:
                company = self.env.get('res.company').browse(partner.company_id)

            amls = partner.unreconciled_aml_ids
            latest_date = False
            latest_level = False
            latest_days = False
            latest_level_without_lit = False
            latest_days_without_lit = False
            for aml in amls:
                if (aml.company_id == company) and (aml.followup_line_id != False) and (not latest_days or latest_days < aml.followup_line_id.delay):
                    latest_days = aml.followup_line_id.delay
                    latest_level = aml.followup_line_id.id
                if (aml.company_id == company) and (not latest_date or latest_date < aml.followup_date):
                    latest_date = aml.followup_date
                if (aml.company_id == company) and (aml.blocked == False) and (aml.followup_line_id != False and
                            (not latest_days_without_lit or latest_days_without_lit < aml.followup_line_id.delay)):
                    latest_days_without_lit =  aml.followup_line_id.delay
                    latest_level_without_lit = aml.followup_line_id.id
            partner.latest_followup_date = latest_date
            partner.latest_followup_level_id = latest_level
            partner.latest_followup_level_id_without_lit = latest_level_without_lit

    @api.multi
    def do_partner_manual_action(self):
        #partner_ids -> res.partner
        for partner in self:
            #Check action: check if the action was not empty, if not add
            action_text= ""
            if partner.payment_next_action:
                action_text = (partner.payment_next_action or '') + "\n" + (partner.latest_followup_level_id_without_lit.manual_action_note or '')
            else:
                action_text = partner.latest_followup_level_id_without_lit.manual_action_note or ''

            #Check date: only change when it did not exist already
            action_date = partner.payment_next_action_date or fields.Date.context_today(self)

            # Check responsible: if partner has not got a responsible already, take from follow-up
            responsible_id = False
            if partner.payment_responsible_id:
                responsible_id = partner.payment_responsible_id.id
            else:
                p = partner.latest_followup_level_id_without_lit.manual_action_responsible_id
                responsible_id = p and p.id or False
            partner.write({
                'payment_next_action_date': action_date,
                'payment_next_action': action_text,
                'payment_responsible_id': responsible_id
            })

    @api.multi
    def do_partner_print(self, data):
        #wizard_partner_ids are ids from special view, not from res.partner
        if not self._ids:
            return {}
        data['partner_ids'] = self._ids
        datas = {
            'ids': self._ids,
            'model': 'account_followup.followup',
            'form': data
        }
        return self.env['report'].get_action([], 'account_followup.report_followup', data=datas)

    @api.multi
    def do_partner_mail(self):
        ctx = self.env.context.copy() if self.env.context else {}
        ctx['followup'] = True
        #partner_ids are res.partner ids
        # If not defined by latest follow-up level, it will be the default template if it can find it
        mtp = self.env.get('mail.template')
        unknown_mails = 0
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                level = partner.latest_followup_level_id_without_lit
                for partner_to_email in partners_to_email:
                    if level and level.send_email and level.email_template_id and level.email_template_id.id:
                        mtp.with_context(ctx).browse(level.email_template_id.id).send_mail(partner_to_email.id, context=ctx)
                    else:
                        mail_template_id = self.env.get('ir.model.data').get_object_reference('account_followup', 'email_template_account_followup_default')
                        mtp.with_context(ctx).browse(mail_template_id[1]).send_mail(partner_to_email.id)
                if partner not in partners_to_email:
                    self.browse(partner.id).message_post(body=_('Overdue email sent to %s' % ', '.join(['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email])))
            else:
                unknown_mails = unknown_mails + 1
                action_text = _("Email not sent because of email address of partner not filled in")
                if partner.payment_next_action_date:
                    payment_action_date = min(fields.Date.context_today(self), partner.payment_next_action_date)
                else:
                    payment_action_date = fields.Date.context_today(self)
                if partner.payment_next_action:
                    payment_next_action = partner.payment_next_action + " \n " + action_text
                else:
                    payment_next_action = action_text
                self.browse([partner.id]).write({
                    'payment_next_action_date': payment_action_date,
                    'payment_next_action': payment_next_action
                })
        return unknown_mails

    @api.multi
    def get_followup_table_html(self):
        assert len(self._ids) == 1

        for record in self:
            partner = record.commercial_partner_id

            followup_table = ''
            if partner.unreconciled_aml_ids:
                company = self.env.get('res.users').browse(self._uid).company_id
                current_date = fields.Date.context_today(self)
                rml_parse = account_followup_print.report_rappel(self._cr, self._uid, 'followup_rml_parser')
                final_res = rml_parse._lines_get_with_partner(partner, company.id)

                for currency_dict in final_res:
                    currency = currency_dict.get('line', [{'currency_id': company.currency_id}])[0]['currency_id']
                    followup_table += '''
                    <table border="2" width=100%%>
                    <tr>
                        <td>''' + _("Invoice Date") + '''</td>
                        <td>''' + _("Description") + '''</td>
                        <td>''' + _("Reference") + '''</td>
                        <td>''' + _("Due Date") + '''</td>
                        <td>''' + _("Amount") + " (%s)" % (currency.symbol) + '''</td>
                        <td>''' + _("Lit.") + '''</td>
                    </tr>
                    '''
                    total = 0
                    for aml in currency_dict['line']:
                        block = aml['blocked'] and 'X' or ' '
                        total += aml['balance']
                        strbegin = "<TD>"
                        strend = "</TD>"
                        date = aml['date_maturity'] or aml['date']
                        if date <= current_date and aml['balance'] > 0:
                            strbegin = "<TD><B>"
                            strend = "</B></TD>"
                        followup_table +="<TR>" + strbegin + str(aml['date']) + strend + strbegin + aml['name'] + strend + strbegin + (aml['ref'] or '') + strend + strbegin + str(date) + strend + strbegin + str(aml['balance']) + strend + strbegin + block + strend + "</TR>"

                    total = reduce(lambda x, y: x+y['balance'], currency_dict['line'], 0.00)

                    total = rml_parse.formatLang(total, dp='Account', currency_obj=currency)
                    followup_table += '''<tr> </tr>
                                    </table>
                                    <center>''' + _("Amount due") + ''' : %s </center>''' % (total)
            return followup_table

    @api.multi
    def write(self, vals):
        if vals.get("payment_responsible_id", False):
            for part in self:
                if part.payment_responsible_id <> vals["payment_responsible_id"]:
                    #Find partner_id of user put as responsible
                    responsible_partner_id = self.env.get("res.users").browse(vals['payment_responsible_id']).partner_id.id
                    self.env.get("mail.thread").message_post(0,
                                      body = _("You became responsible to do the next action for the payment follow-up of") + " <b><a href='#id=" + str(part.id) + "&view_type=form&model=res.partner'> " + part.name + " </a></b>",
                                      type = 'comment',
                                      subtype = "mail.mt_comment",
                                      model = 'res.partner', res_id = part.id,
                                      partner_ids = [responsible_partner_id])
        return super(res_partner, self).write(vals)

    @api.multi
    def action_done(self):
        return self.write({
            'payment_next_action_date': False,
            'payment_next_action':'',
            'payment_responsible_id': False,
        })

    @api.multi
    def do_button_print(self):
        assert(len(self._ids) == 1)
        company_id = self.env.get('res.users').browse(self._uid).company_id.id
        #search if the partner has accounting entries to print. If not, it may not be present in the
        #psql view the report is based on, so we need to stop the user here.
        if not self.env.get('account.move.line').search([
            ('partner_id', '=', self._ids[0]),
            # ('account_id.type', '=', 'receivable'),
            ('full_reconcile_id', '=', False),
            ('reconciled', '=', False),
            ('company_id', '=', company_id),
            '|', ('date_maturity', '=', False), ('date_maturity', '<=', fields.Date.context_today(self)),
        ]):
            raise Warning(_('Error!'),_("The partner does not have any accounting entries to print in the overdue report for the current company."))
        self.message_post(body=_('Printed overdue payments report'))
        #build the id of this partner in the psql view. Could be replaced by a search with [('company_id', '=', company_id),('partner_id', '=', ids[0])]
        wizard_partner_ids = [self._ids[0] * 10000 + company_id]
        followup_ids = self.env.get('account_followup.followup').search([('company_id', '=', company_id)])
        if not followup_ids:
            raise Warning(_('Error!'),_("There is no followup plan defined for the current company."))
        data = {
            'date': fields.date.today(),
            'followup_id': followup_ids._ids[0],
        }
        #call the print overdue report on this partner
        return self.browse(wizard_partner_ids).do_partner_print(data)

    @api.multi
    def _get_amounts_and_date(self):
        company = self.env.get('res.users').browse(self._uid).company_id
        current_date = fields.Date.context_today(self)
        for partner in self:
            worst_due_date = False
            amount_due = amount_overdue = 0.0
            for aml in partner.unreconciled_aml_ids:
                if (aml.company_id == company):
                    date_maturity = aml.date_maturity or aml.date
                    if not worst_due_date or date_maturity < worst_due_date:
                        worst_due_date = date_maturity
                    amount_due += aml.result
                    if (date_maturity <= current_date):
                        amount_overdue += aml.result
            partner.payment_amount_due = amount_due
            partner.payment_amount_overdue = amount_overdue
            partner.payment_earliest_due_date = worst_due_date

    @api.model
    def _get_followup_overdue_query(self, args, overdue_only=False):
        company_id = self.env.get('res.users').browse(self._uid).company_id.id
        having_where_clause = ' AND '.join(map(lambda x: '(SUM(bal2) %s %%s)' % (x[1]), args))
        having_values = [x[2] for x in args]
        query = self.env.get('account.move.line')._query_get()
        overdue_only_str = overdue_only and 'AND date_maturity <= NOW()' or ''
        return ('''SELECT pid AS partner_id, SUM(bal2) FROM
                    (SELECT CASE WHEN bal IS NOT NULL THEN bal
                    ELSE 0.0 END AS bal2, p.id as pid FROM
                    (SELECT (debit-credit) AS bal, partner_id
                    FROM account_move_line l
                    WHERE account_id IN
                            (SELECT id FROM account_account
                            WHERE full_reconcile_id IS NULL
                    ''' + overdue_only_str + '''
                    AND company_id = %s
                    AND ''' + query + ''') AS l
                    RIGHT JOIN res_partner p
                    ON p.id = partner_id ) AS pl
                    GROUP BY pid HAVING ''' + having_where_clause, [company_id] + having_values)

    # def _get_partners(self, cr, uid, ids, context=None):
    #     #this function search for the partners linked to all account.move.line 'ids' that have been changed
    #     partners = set()
    #     for aml in self.browse(cr, uid, ids, context=context):
    #         if aml.partner_id:
    #             partners.add(aml.partner_id.id)
    #     return list(partners)

    payment_responsible_id = fields.Many2one('res.users', ondelete='set null', string='Follow-up Responsible',
                                            help="Optionally you can assign a user to this field, which will make him responsible for the action.",
                                            track_visibility="onchange", copy=False)
    payment_note = fields.Text('Next Action', copy=False,
                                help="This is the next action to be taken.  It will automatically be set when the partner gets a follow-up level that requires a manual action. ",
                                track_visibility="onchange")
    payment_next_action = fields.Text('Next Action', copy=False,
                                    help="This is the next action to be taken.  It will automatically be set when the partner gets a follow-up level that requires a manual action. ",
                                    track_visibility="onchange")
    payment_next_action_date = fields.Date('Next Action Date', copy=False,
                                    help="This is when the manual follow-up is needed. "
                                         "The date will be set to the current date when the partner "
                                         "gets a follow-up level that requires a manual action. "
                                         "Can be practical to set manually e.g. to see if he keeps "
                                         "his promises.")
    unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id', domain=[('reconciled', '=', False), ('account_id.user_type_id.type', '=', 'receivable')])
    latest_followup_date = fields.Date('Latest Follow-up Date', store=False, compute='_get_latest')
    latest_followup_level_id = fields.Many2one('account_followup.followup.line', 'Latest Follow-up Level', help='The maximum follow-up level', compute='_get_latest')
    latest_followup_level_id_without_lit = fields.Many2one('account_followup.followup.line', 'Latest Follow-up Level without litigation', help='The maximum follow-up level without taking into account the account move lines with litigation', compute='_get_latest')
    payment_amount_due = fields.Float('Amount Due', compute='_get_amounts_and_date')
    payment_amount_overdue = fields.Float('Amount Overdue', compute='_get_amounts_and_date')
    payment_earliest_due_date = fields.Date('Worst Due Date', compute='_get_amounts_and_date')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
