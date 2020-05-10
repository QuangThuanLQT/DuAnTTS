# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class product_template_ihr(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_attribute_value_ids(self, product):
        """ list of selectable attributes of a product

        :return: list of product variant description
           (variant id, [visible attribute ids], variant price, variant sale price)
        """
        # product attributes with at least two choices
        quantity = product._context.get('quantity') or 1
        product = product.with_context(quantity=quantity)

        visible_attrs_ids = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id').ids
        attribute_value_ids = []
        for variant in product.product_variant_ids:
            price = variant.website_public_price / quantity
            visible_attribute_ids = [v.id for v in variant.attribute_value_ids if v.attribute_id.id in visible_attrs_ids]
            availability = 1
            if variant.availability == 'in_stock':
                availability = 2
            elif variant.availability == 'warning':
                availability = 3
            attribute_value_ids.append([variant.id, visible_attribute_ids, variant.lst_price, price, variant.sp_co_the_ban,availability,variant.availability_number])
        return attribute_value_ids

    @api.multi
    def get_check_product_interest(self):
        for rec in self:
            user_id = self.env['res.users'].browse(self._uid)
            product_interest_ids = self.env['product.interest'].search(
                [('product_id.product_tmpl_id', '=', rec.id), ('partner_id', '=', user_id.partner_id.id)])
            if len(product_interest_ids):
                return True
            else:
                return False

