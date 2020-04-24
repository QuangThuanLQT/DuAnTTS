# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class do_transfer_warning(models.TransientModel):
    _name = 'do.transfer.warning'

    reason = fields.Char(required=False,string="Lý do tiếp tục")
    picking_id = fields.Many2one('stock.picking')

    @api.model
    def default_get(self, fields):
        res = super(do_transfer_warning, self).default_get(fields)
        res['picking_id'] = self._context.get('picking_id',False)
        res['reason'] = self._context.get('origin_in', False)
        return res

    def do_transfer_again(self):
        if self.picking_id:
            self.picking_id.with_context(not_check_date=True).do_new_transfer()