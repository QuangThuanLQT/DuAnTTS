# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class scrap_ihr(models.Model):
    _inherit = 'stock.scrap'

    reason = fields.Text(string='Reason to Scrap', required=True)
    confirm_date = fields.Datetime(string='Confirm Date')
    confirm_person = fields.Many2one('res.users', string='Confirm Person')

    @api.multi
    def do_scrap(self):
        if self._context.get('skip_stock_move', False) == True:
            pass
        else:
            qty_available = self.get_qty_location(self.location_id)
            if self.scrap_qty > qty_available:
                raise ValidationError(_('Số lượng xuất huỷ vượt mức cho phép!.'))
            res = super(scrap_ihr, self).do_scrap()
            self.confirm_date = datetime.now()
            self.confirm_person = self._uid
            return res

    @api.multi
    def action_confirm_scrap(self):
        return self.do_scrap()

    def get_qty_location(self, location_id):
        if location_id.not_sellable == True:
            qty_available = self.with_context(location=self.location_id.id, location_id=self.location_id.id).product_id.qty_available
        else:
            qty_available = self.product_id.sp_co_the_ban
        return qty_available
