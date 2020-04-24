# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

class stock_picking_inherit(models.Model):
    _inherit = 'stock.picking'

    is_virtual_picking        = fields.Boolean('Is Virtal Picking', default=False)
    mrp_workorder_delivery_id = fields.Many2one('mrp.workorder')
    mrp_workorder_return_id   = fields.Many2one('mrp.workorder')
    mrp_workorder_lost_id     = fields.Many2one('mrp.workorder')
    receiver                  = fields.Many2one('res.users', 'Người nhận' , default=lambda self: self.env.user)
    shipper                   = fields.Many2one('res.users', 'Người giao', default=lambda self: self.env.user)
    picking_workorder_from_mo = fields.Boolean()
    mrp_picking_id = fields.Many2one('stock.picking', string='Dịch chuyển sản xuất')
    project_picking_id = fields.Many2one('stock.picking', string='Dịch chuyển công trình')

    @api.model
    def cron_create_mrp_picking_id(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        ksx_location   = self.env.ref('cptuanhuy_mrp.location_ksx_stock')
        manufacturing_transfer = self.env.ref('cptuanhuy_stock.manufacturing_transfer')

        pickings = self.env['stock.picking'].search([
            ('mrp_picking_id', '=', False),
            ('state', '=', 'done'),
            ('picking_type_id', '=', manufacturing_transfer.id),
            # ('location_id', '=', stock_location.id),
            # ('location_dest_id', '=', ksx_location.id)
        ], limit=30)

        pickings.create_mrp_picking_id()
        return True

    @api.model
    def cron_create_project_picking(self):
        # stock_location = self.env.ref('stock.stock_location_stock')
        # ksx_location = self.env.ref('cptuanhuy_mrp.location_ksx_stock')
        project_transfer = self.env.ref('cptuanhuy_stock.project_transfer')

        pickings = self.env['stock.picking'].search([
            ('project_picking_id', '=', False),
            ('state', '=', 'done'),
            ('picking_type_id', '=', project_transfer.id),
            # ('location_id', '=', stock_location.id),
            # ('location_dest_id', '=', ksx_location.id)
        ], limit=30)

        pickings.create_project_picking_id()
        return True

    @api.multi
    def create_mrp_picking_id(self):
        # Location
        stock_location         = self.env.ref('stock.stock_location_stock')
        ksx_location           = self.env.ref('cptuanhuy_mrp.location_ksx_stock')
        mrp_main_location      = self.env.ref('cptuanhuy_mrp.location_ksx_main_material')
        mrp_general_location   = self.env.ref('cptuanhuy_mrp.location_ksx_general_material')
        production_location    = self.env.ref('stock.location_production')
        customer_location      = self.env.ref('stock.stock_location_customers')

        # MRP Information
        picking_type_mrp_transfer = self.env.ref('cptuanhuy_stock.manufacturing_transfer')
        picking_type_out          = self.env.ref('stock.picking_type_out')
        picking_type_internal     = self.env.ref('stock.picking_type_internal')

        pickings                  = self.env['stock.picking']

        for record in self:
            location_id = record.location_dest_id.id
            if record.picking_type_id.id == picking_type_mrp_transfer.id:
                if record.location_id.id == stock_location.id:
                    if record.location_dest_id.id == ksx_location.id:
                        if record.mrp_production:
                            location_dest_id   = mrp_main_location
                            stock_picking_data = record.copy_data({})[0]
                            stock_picking_data.update({
                                'picking_type_id': picking_type_mrp_transfer.id,
                                'state': 'draft',
                                'is_virtual_picking': True
                            })

                            picking = self.env['stock.picking'].create(stock_picking_data)
                            picking.onchange_picking_type()
                            picking.location_id      = location_id
                            picking.location_dest_id = location_dest_id
                            for line in picking.move_lines:
                                line.location_id      = location_id
                                line.location_dest_id = location_dest_id
                            record.mrp_picking_id = picking
                            pickings += picking
                        else:
                            if record.sale_select_id:
                                stock_picking_data = record.copy_data({})[0]
                                stock_picking_data.update({
                                    'picking_type_id': picking_type_out.id,
                                    'state': 'draft',
                                    'is_virtual_picking': True
                                })
                                picking = self.env['stock.picking'].create(stock_picking_data)
                                picking.onchange_picking_type()
                                picking.location_id = location_id
                                for line in picking.move_lines:
                                    line.location_id = location_id
                                record.mrp_picking_id = picking
                                pickings += picking
                            else:
                                location_dest_id   = mrp_general_location
                                stock_picking_data = record.copy_data({})[0]
                                stock_picking_data.update({
                                    'picking_type_id': picking_type_mrp_transfer.id,
                                    'state': 'draft',
                                    'is_virtual_picking': True
                                })

                                picking = self.env['stock.picking'].create(stock_picking_data)
                                picking.onchange_picking_type()
                                picking.location_id = location_id
                                picking.location_dest_id = location_dest_id
                                for line in picking.move_lines:
                                    line.location_id = location_id
                                    line.location_dest_id = location_dest_id
                                record.mrp_picking_id = picking
                                pickings += picking
                    elif record.location_dest_id.id == customer_location.id:
                        query = "UPDATE stock_picking SET picking_type_id=%s WHERE id = %s" % (picking_type_out.id, record.id,)
                        self.env.cr.execute(query)
                    else:
                        raise UserError('You can not do this transfer.')
                elif record.location_id.id == ksx_location.id:
                    if record.location_dest_id.id in [mrp_main_location.id, mrp_general_location.id]:
                        location_dest_id   = production_location
                        stock_picking_data = record.copy_data({})[0]
                        stock_picking_data.update({
                            'picking_type_id': picking_type_internal.id,
                            'state': 'draft',
                            'is_virtual_picking': True
                        })

                        picking = self.env['stock.picking'].create(stock_picking_data)
                        picking.onchange_picking_type()
                        picking.location_id      = location_id
                        picking.location_dest_id = location_dest_id
                        for line in picking.move_lines:
                            line.location_id      = location_id
                            line.location_dest_id = location_dest_id
                        record.mrp_picking_id = picking
                        pickings += picking
                    else:
                        raise UserError('You can not do this transfer.')
                else:
                    raise UserError('You can not do this transfer.')

        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()
            if picking.state == 'assigned':
                stock_immediate_transfer = self.env['stock.immediate.transfer'].create({'pick_id': picking.id})
                stock_immediate_transfer.process()

    @api.multi
    def create_project_picking_id(self):
        # Location
        stock_location = self.env.ref('stock.stock_location_stock')
        kct_location = self.env.ref('cptuanhuy_stock.location_kct_stock')
        project_main_location = self.env.ref('cptuanhuy_mrp.location_kct_main_material')
        san_xuat_ct_location = self.env.ref('cptuanhuy_mrp.location_san_xuat_ct')
        production_location = self.env.ref('stock.location_production')
        customer_location = self.env.ref('stock.stock_location_customers')

        # MRP Information
        picking_type_project_transfer = self.env.ref('cptuanhuy_stock.project_transfer')
        picking_type_out = self.env.ref('stock.picking_type_out')
        picking_type_internal = self.env.ref('stock.picking_type_internal')

        pickings = self.env['stock.picking']

        for record in self:
            if record.state == 'done' and not record.project_picking_id and record.picking_type_id == picking_type_project_transfer.id:
                location_id = record.location_dest_id.id
                if record.picking_type_id.id == picking_type_project_transfer.id:
                    # Neu dia diem nguon == WH/Stock
                    if record.location_id.id == stock_location.id:
                        # Neu dia diem den la KCT
                        if record.location_dest_id.id == kct_location.id:
                            # if record.project_id or (record.sale_select_id and record.sale_select_id.sale_project_id):
                                location_dest_id = project_main_location
                                stock_picking_data = record.copy_data({})[0]
                                stock_picking_data.update({
                                    'picking_type_id': picking_type_project_transfer.id,
                                    'state': 'draft',
                                    'is_virtual_picking': True,
                                    'project_picking_id': False,
                                })

                                picking = self.env['stock.picking'].create(stock_picking_data)
                                picking.onchange_picking_type()
                                picking.location_id = location_id
                                picking.location_dest_id = location_dest_id
                                for line in picking.move_lines:
                                    line.location_id = location_id
                                    line.location_dest_id = location_dest_id
                                record.project_picking_id = picking
                                pickings += picking
                    if record.location_id.id == kct_location.id and record.location_dest_id.id == project_main_location.id:
                        location_dest_id = san_xuat_ct_location
                        stock_picking_data = record.copy_data({})[0]
                        stock_picking_data.update({
                            'picking_type_id': picking_type_project_transfer.id,
                            'state': 'draft',
                            'is_virtual_picking': True,
                            'project_picking_id': False,
                        })

                        picking = self.env['stock.picking'].create(stock_picking_data)
                        picking.onchange_picking_type()
                        picking.location_id = location_id
                        picking.location_dest_id = location_dest_id
                        for line in picking.move_lines:
                            line.location_id = location_id
                            line.location_dest_id = location_dest_id
                        record.project_picking_id = picking
                        pickings += picking


        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()
            if picking.state == 'assigned':
                stock_immediate_transfer = self.env['stock.immediate.transfer'].create({'pick_id': picking.id})
                stock_immediate_transfer.process()

    @api.model
    def default_get(self, fields):
        res = super(stock_picking_inherit, self).default_get(fields)
        if 'production_id' in self._context:
            production_id           = self.env['mrp.production'].browse(self._context.get('production_id', False))
            picking_type_id         = self.env.ref('cptuanhuy_stock.manufacturing_transfer').id
            stock_location          = production_id.routing_id.location_id.id or self.env.ref('stock.stock_location_stock').id
            location_production     = self.env.ref('stock.location_production').id
            stock_location_scrapped = self.env.ref('stock.stock_location_scrapped').id
            check                   = False
            now                     = datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT)
            res['date']             = now
            res['min_date']         = now
            if 'stock_picking_delivery' in self._context:
                location_id      = stock_location
                location_dest_id = location_production
                check            = True
            if 'stock_picking_return' in self._context:
                location_id      = location_production
                location_dest_id = stock_location
                check            = True
            if 'stock_picking_lost' in self._context:
                location_id      = location_production
                location_dest_id = stock_location_scrapped
                check            = True
            if check:
                res['picking_type_id']  = picking_type_id
                res['location_id']      = location_id
                res['location_dest_id'] = location_dest_id
                res['origin']           = production_id.name
            else:
                res['picking_type_id'] = picking_type_id
                res['origin']          = production_id.name
        return res

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        if 'stock_picking_delivery' not in self._context and 'stock_picking_return' not in self._context and 'stock_picking_lost' not in self._context:
            super(stock_picking_inherit, self).onchange_picking_type()

    @api.multi
    def do_reset_stock_picking(self):
        for picking in self:
            if picking.state == 'done':
                production_to_confirm = []

                # Step 1: Cancel account move
                account_moves = self.env['account.move'].search([
                    ('ref', '=', picking.name)
                ])
                # account_moves.unlink()
                for account_move in account_moves:
                    self.env.cr.execute("DELETE FROM account_move_line WHERE move_id = %s" % (account_move.id))
                    self.env.cr.execute("DELETE FROM account_move WHERE id = %s" % (account_move.id))

                # Step 2: Cancel stock quant
                for stock_move in picking.move_lines:
                    picking_need_reset    = []
                    quant_need_remove     = []

                    # TODO: Reset stock quant
                    for stock_quant in stock_move.quant_ids:
                        reseted_move_ids = []

                        # unreserve picking that related to current quant
                        if stock_quant.reservation_id and stock_quant.reservation_id.id:
                            stock_quant.reservation_id.picking_id.do_unreserve()

                        current_location_id = stock_quant.location_id
                        reset_moves = self.env['stock.move'].search([
                            ('location_dest_id', '=', current_location_id.id),
                            ('id', 'in', stock_quant.history_ids.ids),
                            ('id', 'not in', reseted_move_ids),
                        ], order='date DESC')

                        if len(reset_moves) <= 0:
                            raise UserError('Invalid stock quant: %s' % (stock_quant.id))

                        reset_move = reset_moves.filtered(lambda m: m.location_id.id == current_location_id.id)
                        if len(reset_move) > 0:
                            reset_move = reset_move[0]
                        else:
                            reset_move = reset_moves[0]

                        while reset_move.id != stock_move.id:
                            reseted_move_ids.append(reset_move.id)
                            if reset_move.picking_id.id not in picking_need_reset:
                                picking_need_reset.append(reset_move.picking_id.id)
                            elif reset_move.production_id and reset_move.production_id.id:
                                # Step 1: Reset to draft mrp production
                                production_to_confirm.append(reset_move.production_id)
                                reset_move.production_id.set_to_draft_mp()

                            current_location_id = reset_move.location_id
                            reset_moves = self.env['stock.move'].search([
                                ('location_dest_id', '=', current_location_id.id),
                                ('id', 'in', stock_quant.history_ids.ids),
                                ('id', 'not in', reseted_move_ids),
                            ], order='date DESC')

                            if len(reset_moves) <= 0:
                                raise UserError('Invalid stock quant: %s' % (stock_quant.id))

                            reset_move = reset_moves.filtered(lambda m: m.location_id.id == current_location_id.id)
                            if len(reset_move) > 0:
                                reset_move = reset_move[0]
                            else:
                                reset_move = reset_moves[0]

                        reseted_move_ids.append(stock_move.id)
                        new_histories = self.env['stock.move'].search([
                            ('id', 'in', stock_quant.history_ids.ids),
                            ('id', 'not in', reseted_move_ids),
                        ])
                        if len(new_histories) > 0:
                            quant_data = {
                                'history_ids': [(6, 0, new_histories.ids)],
                                'location_id': stock_move.location_id.id,
                            }
                            stock_quant.write(quant_data)
                        else:
                            quant_need_remove.append(stock_quant)

                    for stock_quant in quant_need_remove:
                        stock_quant.with_context({'force_unlink': True}).unlink()

                    if len(picking_need_reset) > 0:
                        self.browse(picking_need_reset).do_reset_stock_picking()
                        for picking_id in picking_need_reset:
                            self.env.cr.execute(
                                """UPDATE stock_picking SET need_to_confirm = TRUE WHERE id = %s""" % (picking_id,))

                if len(production_to_confirm) > 0:
                    for production in production_to_confirm:
                        if production.state == 'confirmed':
                            production.multi_confirm_production()

                if picking.mapped('mrp_picking_id'):
                    picking.mapped('mrp_picking_id').do_reset_stock_picking()
                    picking.mapped('mrp_picking_id').mapped('pack_operation_product_ids').unlink()
                    picking.mapped('mrp_picking_id').unlink()

                query = "UPDATE stock_move SET state='assigned' WHERE picking_id = %s" % (picking.id,)
                self.env.cr.execute(query)

                query = "UPDATE stock_picking SET state='assigned' WHERE id = %s" % (picking.id,)
                self.env.cr.execute(query)
                picking.state = 'assigned'
            else:
                super(stock_picking_inherit, picking).do_reset_stock_picking()

        return True