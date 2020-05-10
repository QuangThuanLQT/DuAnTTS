# -*- coding: utf-8 -*-

from odoo import models, fields, api

class procurement_order(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        return True

    @api.model
    def create(self, values):
        context = self.env.context.copy() or {}
        context.update({
            'mail_notrack': True,
            'tracking_disable': True
        })
        result = super(procurement_order, self.with_context(context)).create(values)
        return result

    @api.multi
    def write(self, values):
        context = self.env.context.copy() or {}
        context.update({
            'mail_notrack': True,
            'tracking_disable': True
        })
        result = super(procurement_order, self.with_context(context)).write(values)
        return result