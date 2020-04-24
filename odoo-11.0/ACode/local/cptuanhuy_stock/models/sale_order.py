from odoo import models, fields, api

class sale_order(models.Model):
    _inherit = 'sale.order'

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     if name:
    #         partner_ids = self.env['res.partner'].search([('name','ilike',name)])
    #         if partner_ids and len(partner_ids.ids):
    #             args += ['|',('partner_id', 'in', partner_ids.ids)]
    #     res = super(sale_order, self.with_context(name_search_so=True)).name_search(name=name, args=args, operator=operator, limit=limit)
    #     return res

    @api.multi
    def name_get(self):
        if self._context.get('name_search_so', False):
            return [(record.id, "%s - %s" % ( record.name or '', record.partner_id.name or '')) for record in self]
        else:
            return super(sale_order, self).name_get()
