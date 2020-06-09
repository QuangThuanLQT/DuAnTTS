# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char(string="HS Code", help="Standardized code for international shipping and goods declaration")
    group_id = fields.Char(string="Nhóm SP")
    # tt_sp = fields.Selection([('con_hang', 'Còn hàng'), ('het_hang', 'Hết hàng')],
    #                          string="Tình trạng SP")
    # group_id = fields.Many2one('product.group', string="Group Product")

    brand_name_select = fields.Many2one('brand.name', string='Thương hiệu')
    source_select = fields.Many2one('source.name', string='Xuất xứ')
    purchase_code = fields.Char('Mã mua hàng')

    default_code1 = fields.Char(string='Mã SP', readonly=True, required=True, copy=False, default='SP00xx')

    # @api.onchange('product.virtual_available', 'tt_sp')
    # def onchange_tt_sp(self):
    #     for rec in self:
    #         if rec.product.virtual_available == 0:
    #             self.tt_sp = 'het_hang'
    #         else:
    #             self.tt_sp = 'con_hang'

    @api.model
    def create(self, vals):
        if vals.get('default_code1', 'New') == 'New':
            vals['default_code1'] = self.env['ir.sequence'].next_by_code('product.template') or 'New'
        result = super(product_template, self).create(vals)
        return result

    invoice_name = fields.Char(string='Tên Hoá Đơn')

    # categ_id = fields.Many2one(
    #     'product.category', 'Internal Category',
    #     change_default=True, default=_get_default_category_id,
    #     required=True, help="Select category for the current product")

    cost_root = fields.Float(compute='_get_cost_root', string="Cost Medium")

    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Purchase Bills",
        help="On ordered quantities: control bills based on ordered quantities.\n"
             "On received quantities: control bills based on received quantity.", default="receive")

    def _get_cost_root(self):
        for record in self:
            purchase_line_ids = record.env['purchase.order.line'].search(
                [('product_id.product_tmpl_id', '=', record.id), ('order_id.state', '=', 'purchase')])
            amount = 0
            qty = 0
            for line in purchase_line_ids:
                if line.order_id.picking_ids and 'done' in line.order_id.picking_ids.mapped('state'):
                    amount += line.price_discount or line.price_unit
                    qty += 1
            if amount and qty:
                record.cost_root = float(amount / qty)
            else:
                amount = record.standard_price
                qty = 1
                record.cost_root = float(amount / qty)

    # them action cho yeu cau nhap
    @api.multi
    def open_yeu_cau_mua(self):
        action = self.env.ref('sale_order.nhap_hang_list_action_popup').read()[0]
        return action


class product_variants(models.Model):
    _inherit = 'product.product'


class ProductPriceHistory(models.Model):
    """ Keep track of the ``product.template`` standard prices as they are changed. """
    _name = 'product.price.history'
    _rec_name = 'datetime'
    _order = 'datetime desc'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=_get_default_company_id, required=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade', required=True)
    datetime = fields.Datetime('Date', default=fields.Datetime.now)
    cost = fields.Float('Cost', digits=dp.get_precision('Product Price'))
