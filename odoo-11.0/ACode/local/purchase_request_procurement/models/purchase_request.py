# -*- coding: utf-8 -*-
from openerp import _, api, models
from openerp.exceptions import Warning as UserError

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.multi
    def unlink(self):
        procurement_obj = self.env['procurement.order']
        for req in self:
            proc_ids = procurement_obj.search([('request_id', '=', req.id)])
            if proc_ids:
                raise UserError(_('You cannot delete purchase request that is referenced by a procurement order!'))
        return super(PurchaseRequest, self).unlink()

PurchaseRequest()