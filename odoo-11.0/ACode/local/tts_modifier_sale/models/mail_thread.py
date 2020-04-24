from odoo import _, api, exceptions, fields, models, tools


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.multi
    def message_post_with_view(self, views_or_xmlid, **kwargs):
        values = kwargs.get('values', None) or dict()
        if self._name in ['stock.picking', 'account.invoice'] and 'origin' in values:
            return True
        res = super(MailThread, self).message_post_with_view(views_or_xmlid, **kwargs)
        return res
