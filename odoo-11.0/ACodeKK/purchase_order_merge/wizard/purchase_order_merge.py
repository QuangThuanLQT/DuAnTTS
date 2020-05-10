# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _

class purchase_order_merge(models.TransientModel):
    _name = "purchase.order.merge"
    _description = "Purchase Order Merge"

    purchase_order = fields.Many2one(
       'purchase.order', 'Merge into', required=True, readonly=True)
    mergeable = fields.Many2many(
        comodel_name='purchase.order',
        related='purchase_order.merge_with')
    to_merge = fields.Many2many(
        'purchase.order', 'rel_purchase_to_merge', 'purchase', 'to_merge_id',
        'Orders to merge')

    @api.multi
    def merge_order_lines(self):
        self.purchase_order.write({
            'order_line': [
                (4, line.id)
                for line in self.to_merge.mapped('order_line')
            ]})

    @api.multi
    def _picking_can_merge(self, picking):
        return (picking.state not in ('done', 'cancel') and
                picking.location_dest_id.usage == 'customer')

    @api.multi
    def _get_picking_map_key(self, picking):
        return (picking.picking_type_id, picking.location_id,
                picking.location_dest_id, picking.partner_id)

    @api.multi
    def merge_pickings(self):
        """ Assign all pickings to the target purchase order and merge any
        pending pickings """
        orders = self.purchase_order + self.to_merge
        group = self.env['procurement.group']
        if self.purchase_order.picking_ids[0].group_id:
            group = self.purchase_order.picking_ids[0].group_id
        else:
            for order in self.to_merge:
                if order.picking_ids:
                    if order.picking_ids[0].group_id:
                        group = order.picking_ids[0].group_id
                        break
            else:
                return 
            self.purchase_order.write({'procurement_group_id': group.id})
        other_groups = orders[0].picking_ids.mapped('group_id')
        self.env['stock.picking'].search(
            [('group_id', 'in', other_groups.ids)]).write(
                {'group_id': group.id})
        self.env['stock.move'].search(
            [('group_id', 'in', other_groups.ids)]).write(
                {'group_id': group.id})
        self.env['procurement.order'].search(
            [('group_id', 'in', other_groups.ids)]).write(
                {'group_id': group.id})
        pick_map = {}
        for picking in self.to_merge.mapped('picking_ids'):
            if self._picking_can_merge(picking):
                key = self._get_picking_map_key(picking)
                if key not in pick_map:
                    pick_map[key] = self.env['stock.picking']
                pick_map[key] += picking
            else:
                picking.write({'origin': group.name, 'group_id':group.id})
        for pickings in pick_map.values():
            target = pickings[0]
            if len(pickings) > 1:
                pickings -= target
                pickings.mapped('move_lines').write({'picking_id': target.id})
		pickings.mapped('pack_operation_product_ids').write({'picking_id': target.id})
                pickings.unlink()
            target.write({'origin': group.name, 'group_id':group.id})
        return True

    @api.multi
    def open_purchase(self):
        self.ensure_one()
        return {
            'name': _('Merged purchase order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.purchase_order.id,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
        }


    @api.multi
    def merge(self):
        self.ensure_one()
        orders = self.purchase_order + self.to_merge
        create_picking = False
        reset_wait_invoice = False
        if not all(order.state in ('sent', 'draft') for order in orders):
            drafts = orders.filtered(
                lambda o: o.state in ('sent', 'draft'))
            confirmed = orders - drafts
            for draft in drafts:
                draft.button_confirm()
            self.merge_pickings()

        self.merge_order_lines()
        self.to_merge.write({'state': 'cancel'})
        for order in self.to_merge:
            order.message_post(_('Merged into %s') % self.purchase_order.name)
        self.purchase_order.message_post(
            _('Order(s) %s merged into this one') % ','.join(
                self.to_merge.mapped('name')))
        return self.open_purchase()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
