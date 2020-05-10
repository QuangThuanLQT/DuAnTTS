# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class sale_order_ihr(models.Model):
    _inherit = 'sale.order'

    sale_order_merge = fields.Boolean(string='Gộp đơn', copy=False)
    sale_order_merge_ids = fields.Many2many('sale.order','sale_order_merge_ref','so_parent_id','so_child_id',string='Sale Orders', copy=False)
    sale_order_parent_id = fields.Many2one('sale.order', copy=False)

    @api.multi
    def action_sale_cancel(self):
        for rec in self:
            if rec.sale_order_merge:
                raise UserError(_('Đơn hàng này là một đơn hàng gộp bạn không thể hủy.'))
            else:
                return super(sale_order_ihr, self).action_sale_cancel()

    @api.depends('sale_order_merge','order_line.price_total', 'delivery_method', 'delivery_scope_id', 'transport_route_id')
    def _delivery_amount(self):
        for order in self:
            if order.sale_order_parent_id:
                order.update({
                    'delivery_amount': 0,
                })
            else:
                super(sale_order_ihr, self)._delivery_amount()

    @api.multi
    def update_so_parent(self):
        for rec in self:
            so_id = self.env['sale.order'].search([('sale_order_merge_ids', '=', rec.id)], limit=1)
            if so_id:
                rec.sale_order_merge = True
                rec.sale_order_parent_id = so_id
            else:
                print "split_sale_order"
                rec.sale_order_merge = False
                rec.sale_order_parent_id = False
            rec.button_dummy()

    @api.onchange('sale_order_merge')
    def onchange_sale_order_merge(self):
        if not self.sale_order_merge:
            self.sale_order_merge_ids = False

    @api.model
    def create(self, val):
        res = super(sale_order_ihr, self).create(val)
        if res.sale_order_merge_ids:
            res.sale_order_merge_ids.update_so_parent()
        return res

    @api.multi
    def write(self, val):
        so_ids = self.env['sale.order']
        if 'sale_order_merge_ids' in val:
            so_ids = self.mapped('sale_order_merge_ids')
        res = super(sale_order_ihr, self).write(val)
        if 'sale_order_merge_ids' in val:
            so_ids += self.mapped('sale_order_merge_ids')
        if so_ids:
            so_ids.update_so_parent()
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        domain_so_merge = self._context.get('domain_so_merge', False)
        if domain_so_merge:
            domain_so_merge = self.env['sale.order'].browse(domain_so_merge)
            domain_partner_so_merge = domain_so_merge.partner_id.id
            domain_name_so_merge = domain_so_merge.name
            domain = [('partner_id', '=', domain_partner_so_merge), ('state', '=', 'sale'),
                                           ('sale_order_merge', '=', False), ('sale_order_parent_id', '=', False), ('sale_order_return', '=', False)]
            if domain_name_so_merge:
                domain.append(('name', '!=', domain_name_so_merge))
            so_ids = self.env['sale.order'].search(domain)
            so_ids = so_ids.filtered(lambda s: s.trang_thai_dh not in  ['done', 'delivery', 'cancel'])
            args.append(('id', 'in', so_ids.ids))

        domain_so_split = self._context.get('domain_so_split', False)
        if domain_so_split:
            domain_so_split = self.env['sale.order'].browse(domain_so_split)
            args.append(('id', 'in', domain_so_split.sale_order_merge_ids.ids))
        res = super(sale_order_ihr, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

    @api.multi
    def action_merge_sale_order(self):
        for rec in self:
            action = self.env.ref('prinizi_merge_sale_order.merge_sale_order_action').read()[0]
            action['context'] = {'default_sale_id':rec.id}
            return action

    @api.multi
    def action_split_sale_order(self):
        for rec in self:
            action = self.env.ref('prinizi_merge_sale_order.split_sale_order_action').read()[0]
            action['context'] = {'default_sale_id':rec.id}
            return action

class merge_sale_order(models.Model):
    _name = 'merge.sale.order'

    sale_id = fields.Many2one('sale.order')
    sale_merge_ids = fields.Many2many('sale.order', required=1, string="Đơn hàng gộp")

    @api.multi
    def action_merge(self):
        for rec in self:
            if not rec.sale_id.sale_order_parent_id:
                sale_merge_ids = rec.sale_merge_ids + rec.sale_id.sale_order_merge_ids
                rec.sale_id.sale_order_merge_ids = sale_merge_ids
                rec.sale_id.sale_order_merge = True

class split_sale_order(models.Model):
    _name = 'split.sale.order'

    sale_id = fields.Many2one('sale.order')
    sale_split_ids = fields.Many2many('sale.order', string="Đơn hàng tách")
    option = fields.Selection([('each', 'Tách từng đơn'),('all', 'Tách tất cả')], default='each')

    @api.multi
    def action_split(self):
        for rec in self:
            if rec.option == 'each':
                sale_split_ids = rec.sale_id.sale_order_merge_ids - rec.sale_split_ids
                print sale_split_ids
                rec.sale_id.sale_order_merge_ids = sale_split_ids
                if not sale_split_ids:
                    rec.sale_id.sale_order_merge = False
            else:
                rec.sale_id.sale_order_merge_ids = False
                rec.sale_id.sale_order_merge = False
