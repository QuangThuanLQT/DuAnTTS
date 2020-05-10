# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, SUPERUSER_ID, tools

class mail_thread_inherit(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        res = super(mail_thread_inherit, self).message_post(body=body, subject=subject, message_type=message_type,
                                                            subtype=subtype, parent_id=parent_id, attachments=attachments,
                                                            content_subtype=content_subtype, **kwargs)

        model = self._name
        if model == 'project.task':
            res.needaction_partner_ids = [(6,0,self.user_id.partner_id.ids + self.project_id.user_id.partner_id.ids)]
        return res
