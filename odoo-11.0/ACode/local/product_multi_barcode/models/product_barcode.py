# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
# from odoo.addons.product import product as addon_product

_logger = logging.getLogger(__name__)

class ProductBarcode(models.Model):
    _name = 'product.barcode'
    _description = "List of Barcode for a product."

    name = fields.Char('Barcode')
    product_id = fields.Many2one('product.template', 'Product', required=True)
    sequence = fields.Integer('Sequence')

    _order = 'sequence'

    def _check_barcode_key(self):
        res = True
        if self.env['product.barcode'].search([('id', '!=', self.id), ('name', '=', self.name)]) or self.env['product.product'].search([('product_tmpl_id', '!=', self.product_id.id), ('barcode', '=', self.name)]):
            res = False
        return res

    _constraints = [(_check_barcode_key, 'Barcode đã được sử dụng.', ['name'])]

    @api.model
    def create(self, vals):
        """Create ean13 with a sequence higher than all
        other products when it is not specified"""
        if not vals.get('sequence') and vals.get('product_id'):
            barcodes = self.search([
                ('product_id', '=', vals['product_id'])
            ])
            vals['sequence'] = 1
            if barcodes:
                vals['sequence'] = max([barcode.sequence for barcode in barcodes]) + 1
        return super(ProductBarcode, self).create(vals)

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'barcodes.barcode_events_mixin']

    def on_barcode_scanned(self, barcode):
        a = 1
        if barcode not in self.barcode_ids.mapped('name'):
            self.barcode_ids += self.barcode_ids.new({
                'name' : barcode,
            })

    @api.model_cr_context
    def _auto_init(self):
        cr = self._cr

        sql = ("SELECT data_type "
               "FROM information_schema.columns "
               "WHERE table_name = 'product_template' "
               "AND column_name = 'barcode' ")

        cr.execute(sql)
        column = cr.fetchone()
        if column and column[0] == 'character varying':
            # module was not installed, the column will be replaced by
            _logger.info('migrating the Barcode')
            cr.execute("INSERT INTO "
                       "product_barcode (name, product_id, sequence) "
                       "SELECT p.barcode, p.id, 1 "
                       "FROM product_template p WHERE "
                       "p.barcode IS NOT NULL ")
            # drop the field otherwise the function field will
            # not be computed
            cr.execute("ALTER TABLE product_template "
                       "DROP barcode")

        return super(ProductTemplate, self)._auto_init()

    # @api.multi
    # @api.depends('barcode_ids')
    # def _get_main_barcode(self):
    #     values = {}
    #     for product in self:
    #         barcode = False
    #         if product.barcode_ids:
    #             # get the first ean13 as main ean13
    #             barcode = product.barcode_ids[0].id
    #         product.barcode = barcode
    #     return values
#
#     # def _get_barcode(self, cr, uid, ids, context=None):
#     #     res = set()
#     #     obj = self.pool.get('product.barcode')
#     #     for barcode in obj.browse(cr, uid, ids, context=context):
#     #         res.add(barcode.product_id.id)
#     #     return list(res)
#     #
#     # def _write_barcode(self, cr, uid, product_id, _name, value, _arg, context=None):
#     #     product = self.browse(cr, uid, product_id, context=context)
#     #     if value and value not in [barcode.name for barcode in product.barcode_ids]:
#     #         self.pool.get('product.barcode').create(cr, uid, {
#     #             'name': value,
#     #             'product_id': product.id
#     #         }, context=context)
#     #     return True
#
    @api.depends('barcode_ids')
    @api.multi
    def _get_barcode_text(self):
        for record in self:
            barcode_texts = []
            for barcode in record.barcode_ids:
                barcode_texts.append(barcode.name)
            record.barcode_text = ','.join(barcode_texts)

    barcode_text = fields.Char('Barcodes', compute='_get_barcode_text', store=True)
    barcode_ids  = fields.One2many('product.barcode', 'product_id', 'Barcode')
    # barcode     = fields.Char('Barcode', compute='_get_main_barcode', store=False)
#
#     # disable constraint
#     # def _check_barcode_key(self, cr, uid, ids):
#     #     "Inherit the method to disable the EAN13 check"
#     #     return True
#     #
#     # _constraints = [(_check_barcode_key, 'Error: Invalid barcode code', ['barcode'])]
#     #
#     # def search(self, cr, uid, args, offset=0, limit=None,
#     #            order=None, context=None, count=False):
#     #     """overwrite the search method in order to search
#     #     on all ean13 codes of a product when we search an ean13"""
#     #
#     #     if filter(lambda x: x[0] == 'barcode', args):
#     #         # get the operator of the search
#     #         barcode_operator = filter(lambda x: x[0] == 'barcode', args)[0][1]
#     #         # get the value of the search
#     #         barcode_value = filter(lambda x: x[0] == 'barcode', args)[0][2]
#     #         # search the ean13
#     #         barcode_ids = self.pool.get('product.barcode').search(
#     #             cr, uid, [('name', barcode_operator, barcode_value)])
#     #
#     #         # get the other arguments of the search
#     #         args = filter(lambda x: x[0] != 'barcode', args)
#     #         # add the new criterion
#     #         args += [('barcode_ids', 'in', barcode_ids)]
#     #     return super(ProductProduct, self).search(
#     #         cr, uid, args, offset, limit, order, context=context, count=count)
