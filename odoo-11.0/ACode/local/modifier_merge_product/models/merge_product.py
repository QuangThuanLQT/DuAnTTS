# -*- coding: utf-8 -*-

from odoo import models, fields, api


class merge_to_product(models.TransientModel):
    _name = 'merge.to.product'

    product_to = fields.Many2one('product.product', string="Product To")
    product_from = fields.Many2one('product.product', string="Product From")

    @api.multi
    def apply_merge(self):
        list_model_remove = ['report.stock.lines.date', 'merge.to.product']
        product_field_ids = self.env['ir.model.fields'].search(
            [('model_id.model', 'not in', list_model_remove), ('ttype', '=', 'many2one'),
             ('relation', '=', 'product.product'), ('store', '=', True)])
        for product_field_id in product_field_ids:
            model = product_field_id.model_id.model
            if model == 'stock.check.report':
                continue
            product_relate_ids = self.env[model].search([(product_field_id.name, '=', self.product_from.id)])
            for product_relate_id in product_relate_ids:
                try:
                    self._cr.execute("""UPDATE %s SET %s=%s WHERE id=%s""" % (
                        model.replace(".", "_"), product_field_id.name, self.product_to.id, product_relate_id.id))
                except:
                    pass

        self.product_from.active = False
        self.product_from.product_tmpl_id.active = False
