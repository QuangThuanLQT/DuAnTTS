# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class mrp_workorder(models.Model):
    _inherit = "mrp.workorder"

    @api.model
    def _get_wo_state(self):
        result = []
        states = self.env['work.order.state'].sudo().search([])
        for state in states:
            result.append((state.code, state.name))
        return result

    so_id       = fields.Many2one('sale.order', related='production_id.so_id', string='Sale Order', store=True)
    state       = fields.Selection(_get_wo_state, 'Status', readonly=True, track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string="Responsible")

    @api.multi
    def button_waiting_director(self):
        for record in self:
            delay = 0.0
            date_now = time.strftime('%Y-%m-%d %H:%M:%S')

            date_start = datetime.strptime(record.date_start, '%Y-%m-%d %H:%M:%S')
            date_finished = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S')
            delay += (date_finished - date_start).days * 24
            delay += (date_finished - date_start).seconds / float(60 * 60)

            record.write({
                'state': 'waiting_director',
                'date_finished': date_now,
                'delay': delay,
            })

    @api.multi
    def button_refuse(self):
        self.write({
            'state': 'draft',
        })

    @api.multi
    def button_start(self):
        result = super(mrp_workorder, self).button_start()
        # for record in self:
        #     sale_order_id = record.so_id and record.so_id.id or False
        #     if sale_order_id:
        #         record.so_id.write({
        #             'mo_state': record.workcenter_id.mo_state
        #         })
        return result

    @api.multi
    def send_mail(self):
        template = self.env.ref('vieterp_manufacturing.email_template_edi_start_work_order', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        ctx = {}
        ctx.update({
            'default_model': 'mrp.production.workcenter.line',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    # def send_mail_tempalte(self, cr, uid, ids, template_id, context=None):
    #     vals = {
    #         'model': 'mrp.production.workcenter.line',
    #         'res_id': ids[0],
    #         'use_template': template_id,
    #         'composition_mode': 'comment',
    #     }
    #
    #     res = self.pool.get('mail.compose.message').onchange_template_id(cr, uid, None, template_id, 'comment',
    #                                                                      'mrp.production.workcenter.line', ids[0])
    #
    #     if res:
    #         vals['body'] = res['value']['body']
    #         vals['subject'] = res['value']['subject']
    #         vals['subject'] = res['value']['subject']
    #
    #     mail_id = self.pool.get('mail.compose.message').create(cr, uid, vals)
    #     raise osv.except_osv(_('DeBug!'), _(" Email template ID: " + str(vals['use_template'])))
    #
    #     sql = '''
    #             update mail_compose_message set template_id = '%s' where id = %s
    #           ''' % (template_id, int(mail_id))
    #     cr.execute(sql)
    #
    #     return self.pool.get('mail.compose.message').send_mail(cr, uid, [mail_id])
    #     return True