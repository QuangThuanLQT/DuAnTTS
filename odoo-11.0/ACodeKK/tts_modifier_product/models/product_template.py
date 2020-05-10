# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
import itertools
import psycopg2
from odoo.exceptions import ValidationError, except_orm

class product_template_ihr(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(readonly=True)
    product_pricelist_line = fields.One2many('product.pricelist.line', 'line_id', track_visibility='onchange')
    product_stock_move_open = fields.One2many('stock.move', 'product_id', compute='get_product_stock_move_open')

    def _get_cost_root(self):
        for record in self:
            record.cost_root = 0

    @api.multi
    def get_product_stock_move_open(self):
        for record in self:
            stock_location = self.env.ref('stock.stock_location_stock').id
            stock_location_customers = self.env.ref('stock.stock_location_customers').id
            stock_location_scrapped = self.env.ref('stock.stock_location_scrapped').id
            location_inventory = self.env.ref('stock.location_inventory').id
            stock_location_suppliers = self.env.ref('stock.stock_location_suppliers').id
            not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])
            location_dest_list = [stock_location, stock_location_customers, stock_location_scrapped, location_inventory,
                                  stock_location_suppliers] + not_sellable.ids
            moves = self.env['stock.move'].search([('state', '=', 'done'),('product_id', 'in', record.product_variant_ids.ids),('location_dest_id', 'in', location_dest_list)])

            record.product_stock_move_open = moves

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.default_code = template.product_variant_ids.default_code
        for template in (self - unique_variants):
            if template.product_variant_ids:
                default_code = template.product_variant_ids.sorted(key='default_code', reverse=False)[0].default_code
                if default_code:
                    default_code = default_code.replace('SPV','SP')
                template.default_code = default_code
            else:
                template.default_code = ''

    @api.multi
    def create_variant_ids(self):
        Product = self.env["product.product"]
        for tmpl_id in self.with_context(active_test=False):
            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            variant_alone = tmpl_id.attribute_line_ids.filtered(
                lambda line: line.attribute_id.create_variant and len(line.value_ids) == 1).mapped('value_ids')
            for value_id in variant_alone:
                updated_products = tmpl_id.product_variant_ids.filtered(
                    lambda product: value_id.attribute_id not in product.mapped('attribute_value_ids.attribute_id'))
                updated_products.write({'attribute_value_ids': [(4, value_id.id)]})

            # list of values combination
            existing_variants = [set(variant.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant).ids)
                                 for variant in tmpl_id.product_variant_ids]
            variant_matrix = itertools.product(*(line.value_ids for line in tmpl_id.attribute_line_ids if
                                                 line.value_ids and line.value_ids[0].attribute_id.create_variant))
            variant_matrix = map(
                lambda record_list: reduce(lambda x, y: x + y, record_list, self.env['product.attribute.value']),
                variant_matrix)
            to_create_variants = filter(lambda rec_set: set(rec_set.ids) not in existing_variants, variant_matrix)

            # check product
            variants_to_activate = self.env['product.product']
            variants_to_unlink = self.env['product.product']
            for product_id in tmpl_id.product_variant_ids:
                if not product_id.active and product_id.attribute_value_ids.filtered(
                        lambda r: r.attribute_id.create_variant) in variant_matrix:
                    variants_to_activate |= product_id
                elif product_id.attribute_value_ids.filtered(
                        lambda r: r.attribute_id.create_variant) not in variant_matrix:
                    variants_to_unlink |= product_id
            if variants_to_activate:
                variants_to_activate.write({'active': True})

            # create new product
            for variant_ids in to_create_variants:
                new_variant = Product.with_context(variants_to_unlink = variants_to_unlink.ids).create({
                    'product_tmpl_id': tmpl_id.id,
                    'attribute_value_ids': [(6, 0, variant_ids.ids)]
                })

            # unlink or inactive product
            for variant in variants_to_unlink:
                try:
                    with self._cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                        variant.unlink()
                # We catch all kind of exception to be sure that the operation doesn't fail.
                except (psycopg2.Error, except_orm):
                    variant.write({'active': False})
                    pass
        return True

    @api.model
    def create(self, val):
        product_id = self.env['product.product'].search([('default_code', '!=', False),'|',('active', '=', False),('active', '=', True)], limit=1, order='default_code DESC')
        if not product_id:
            number_next = 1
        else:
            number_next = int(product_id.default_code.split('SPV')[1]) + 1
        default_code = 'SP' + '{0:06}'.format(number_next)
        res = super(product_template_ihr, self).create(val)
        res.default_code = default_code
        # val['default_code'] = default_code
        # res = super(product_template_ihr, self).create(val)
        return res

    @api.multi
    def write(self, val):
        res = super(product_template_ihr, self.with_context(write_template = True)).write(val)
        return res

    @api.multi
    def multi_action_unpublish(self):
        ids = self.env.context.get('active_ids', [])
        product_ids = self.browse(ids)
        product_ids.write({
            'website_published' : False,
        })

    @api.multi
    def multi_action_publish(self):
        ids = self.env.context.get('active_ids', [])
        product_ids = self.browse(ids)
        product_ids.write({
            'website_published' : True,
        })

    def update_default_code(self):
        product_id = self.env['product.template'].search([('default_code', 'like', 'SPV')])
        for template in product_id:
            default_code = template.sorted(key='default_code', reverse=False)[0].default_code
            if default_code:
                default_code = default_code.replace('SPV', 'SP')
            template.default_code = default_code

class product_pricelist_line(models.Model):
    _name = 'product.pricelist.line'

    line_id = fields.Many2one('product.template')
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    quantity_min = fields.Float(string="Quantity Min")
    giam_gia = fields.Float(string="Giảm giá")
