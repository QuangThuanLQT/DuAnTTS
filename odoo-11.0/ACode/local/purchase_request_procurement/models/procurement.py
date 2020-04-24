# -*- coding: utf-8 -*-
from openerp import _, api, fields, models

class Procurement(models.Model):
    _inherit = 'procurement.order'

    request_id = fields.Many2one('purchase.request', string='Latest Purchase Request')

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        self.ensure_one()
        default['request_id'] = False
        return super(Procurement, self).copy(default)

    @api.model
    def _prepare_purchase_request_line(self, purchase_request):
        return {
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'date_required': self.date_planned,
            'product_uom_id': self.product_uom.id,
            'product_qty': self.product_qty,
            'request_id': purchase_request.id,
            'procurement_id': self.id
        }

    @api.model
    def _prepare_purchase_request(self):
        return {
            'origin': self.origin,
            'company_id': self.company_id.id,
            'picking_type_id': self.rule_id.picking_type_id.id,
        }

    @api.model
    def _search_existing_purchase_request(self):
        """This method is to be implemented by other modules that can
        provide a criteria to select the appropriate purchase request to be
        extended.
        """
        return False

    @api.multi
    def _run(self):
        request_obj = self.env['purchase.request']
        request_line_obj = self.env['purchase.request.line']
        if self.rule_id and self.rule_id.action == 'buy' and self.product_id.purchase_request:
            # Search for an existing Purchase Request to be considered
            # to be extended.
            pr = self._search_existing_purchase_request()
            if not pr:
                request_data = self._prepare_purchase_request()
                req = request_obj.create(request_data)
                self.message_post(body=_("Purchase Request created"))
                self.request_id = req.id
            request_line_data = self._prepare_purchase_request_line(req)
            request_line_obj.create(request_line_data),
            self.message_post(body=_("Purchase Request extended."))
            return True
        return super(Procurement, self)._run()

Procurement()