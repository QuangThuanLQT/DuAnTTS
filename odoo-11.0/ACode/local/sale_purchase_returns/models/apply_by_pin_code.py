# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class cancel_function_reason(models.TransientModel):
    _name = 'apply.by.pin.code'

    ma_bin = fields.Char(required=True,string="Mã Pin")

    @api.multi
    def apply(self):
        if 'model' in self._context and 'record_id' in self._context:
            model = self._context.get('model',False)
            record_id = self._context.get('record_id', False)
            user_ids = self.env.ref('account_unc.group_tong_giam_doc').users
            if self.ma_bin in  user_ids.mapped('ma_bin'):
                if model == 'sale.order':
                    sale_id = self.env['sale.order'].browse(record_id)
                    sale_id.button_action_return()
            else:
                raise UserError(_("Mã pin sai."))