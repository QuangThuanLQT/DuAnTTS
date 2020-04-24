# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
import math


class mrp_production_inherit(models.Model):
    _inherit = 'mrp.production'

    so_id       = fields.Many2one('sale.order', compute='_get_so_so_line', store=True, string="Đơn hàng")
    so_line_id  = fields.Many2one('sale.order.line',compute='_get_so_so_line',store=True)
    user_email  = fields.Char(string="Email", related='user_id.partner_id.email')
    user_phone  = fields.Char(string="Điện thoại", related='user_id.partner_id.phone')
    routing_id  = fields.Many2one(
        'mrp.routing', 'Routing',
        readonly=False, store=True,domain=[('operation_ids','!=',False)],
        help="The list of operations (list of work centers) to produce the finished product. The routing "
             "is mainly used to compute work center costs during operations and to plan future loads on "
             "work centers based on production planning.")
    picking_ids = fields.One2many('stock.picking', 'mrp_production', string="Kho")
    priority_id = fields.Many2one('mrp.priority', u'Độ ưu tiên', default=lambda x: x.env.ref('cptuanhuy_mrp.mrp_priority_trung_binh'))

    def update_generate_finished_moves(self):
        if not self.move_finished_ids:
            move = self.env['stock.move'].create({
                'name': self.name,
                'date': self.date_planned_start,
                'date_expected': self.date_planned_start,
                'product_id': self.product_id.id,
                'product_uom': self.product_uom_id.id,
                'product_uom_qty': self.product_qty,
                'location_id': self.product_id.property_stock_production.id,
                'location_dest_id': self.location_dest_id.id,
                'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
                'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
                'company_id': self.company_id.id,
                'production_id': self.id,
                'origin': self.name,
                'group_id': self.procurement_group_id.id,
                'propagate': self.propagate,
                'price_unit' : self.material_cost,
            })
            move.action_confirm()
            self.set_to_draft_mp()
            self.with_context(active_ids=self.ids).action_confirm_production()

            return False
        else:
            return False

    def update_mrp_generate_finished_moves(self):
        if not self.move_finished_ids:
            move = self.env['stock.move'].create({
                'name': self.name,
                'date': self.date_planned_start,
                'date_expected': self.date_planned_start,
                'product_id': self.product_id.id,
                'product_uom': self.product_uom_id.id,
                'product_uom_qty': self.product_qty,
                'location_id': self.product_id.property_stock_production.id,
                'location_dest_id': self.location_dest_id.id,
                'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
                'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
                'company_id': self.company_id.id,
                'production_id': self.id,
                'origin': self.name,
                'group_id': self.procurement_group_id.id,
                'propagate': self.propagate,
                'price_unit': self.material_cost,
            })
            move.action_confirm()

            return False
        else:
            return False

    @api.multi
    def set_to_draft_mp(self):
        for record in self:
            stock_move_ids = record.move_raw_ids + record.move_finished_ids
            stock_move_ids.set_to_draft_stm()
            record.move_raw_ids.unlink()
            move_finished_id_cr = {}

            mrp_workorder_ids = self.env['mrp.workorder'].search([('production_id','=',record.id)])
            for mrp_workorder_id in mrp_workorder_ids:
                mrp_workorder_id.state = 'ready'
            mrp_workorder_ids.unlink()

            for line in record.move_finished_ids:
                if line.product_id == record.product_id and line.product_uom_qty == record.product_qty:
                    move_finished_id_cr = line.copy_data({})[0]
                    move_finished_id_cr.update({
                        'quantity_done' : 0
                    })
                    break
            if move_finished_id_cr:
                record.move_finished_ids.unlink()
                move_finished_ids = record.move_finished_ids.browse([])
                move_finished_ids += record.move_finished_ids.new(move_finished_id_cr)
                record.move_finished_ids = move_finished_ids
            elif record.move_finished_ids:
                move_finished_id_cr = record.move_finished_ids[0].copy_data({})[0]
                move_finished_id_cr.update({
                    'product_uom_qty' : record.product_qty,
                    'product_id': record.product_id.id,
                    'quantity_done': 0,
                })
                record.move_finished_ids.unlink()
                record.move_finished_ids += record.move_finished_ids.new(move_finished_id_cr)
            record.state = 'confirmed'

        return True

    @api.onchange('priority_id')
    def onchange_priority_id(self):
        for record in self:
            for workorder in record.workorder_ids:
                workorder.priority_id = record.priority_id

    @api.multi
    def create_raw_material_picking(self):
        data_line = []
        move_obj = self.env['stock.move']

        for line in self.bom_id.bom_line_ids:
            move_default_data = move_obj.default_get(move_obj._fields)
            manufacture_id = self.env.ref('mrp.route_warehouse0_manufacture')
            if line.product_id and line.product_id and manufacture_id in line.product_id.route_ids:
                continue
            move_default_data.update({
                'product_id'        : line.product_id.id,
                'product_uom'       : line.product_uom_id.id,
                'product_uom_qty'   : self.product_qty * line.product_qty,
                'name'              : line.product_id.name,
                'address_in_id'     : self.so_id and self.so_id.partner_id.id or False,
                'picking_type_id'   : self.env.ref("cptuanhuy_stock.manufacturing_transfer").id or False,
                'location_id'       : self.env.ref("cptuanhuy_stock.manufacturing_transfer").default_location_src_id.id or False,
                'location_dest_id'  : self.env.ref("cptuanhuy_stock.manufacturing_transfer").default_location_dest_id.id or False,
                # 'min_date'          : self.min_date
            })
            data_line.append((0,0,move_default_data))

        context = {
            'default_picking_type_id'   : self.env.ref("cptuanhuy_stock.manufacturing_transfer").id or False,
            'default_mrp_production'    : self.id,
            'default_sale_select_id'    : self.so_id.id or False,
            'default_shipper'           : self.user_id.id or False,
            'default_receiver'          : self.user_id.id or False,
            'default_partner_id'        : self.so_id and self.so_id.partner_id.id or False
        }
        if data_line:
            context.update({'default_move_lines' : data_line})
        return {
            'type'      : 'ir.actions.act_window',
            'name'      : 'Kho Tổng: Dịch chuyển sản xuất',
            'view_type' : 'form',
            'view_mode' : 'form',
            'view_id'   : self.env.ref("stock.view_picking_form").id or False,
            'res_model' : 'stock.picking',
            'context'   : context,
        }


    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        bom_qty = bom_data['qty']

        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in bom.routing_id.operation_ids:
            # create workorder
            cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': not operation.code_before and 'ready' or 'pending',
                'qty_producing': quantity,
                'capacity': operation.workcenter_id.capacity,
                'code' : operation.code,
                'code_before' : ','.join(operation.code_before.mapped('code')),
                'responsible_id' : operation.user_id.id,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder

            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_lot_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = "%s - %s" % (record.name, record.product_id.default_code)
            result.append((record.id, name))
        return result

    @api.onchange('bom_id')
    def md_onchange_bom_id(self):
        if self.bom_id and self.bom_id.routing_id.operation_ids:
            self.routing_id = self.bom_id.routing_id


    @api.multi
    def write(self, values):
        result = super(mrp_production_inherit, self).write(values)
        for record in self:
            if record.routing_id and record.routing_id != record.bom_id.routing_id:
                record.bom_id.routing_id = record.routing_id
        return result

    @api.depends('bom_id')
    def _get_so_so_line(self):
        for record in self:
            if record.bom_id:
                record.so_id = record.bom_id.so_id
                record.so_line_id = record.bom_id.so_line_id

    @api.multi
    def update_picking_workorder(self):
        for record in self:
            if record.state not in ('confirmed','done','cancel'):
                for workorder in record.workorder_ids:
                    picking_id = workorder.stock_picking_delivery_ids.filtered(lambda p: p.picking_workorder_from_mo == True)
                    if picking_id:
                        if picking_id.state != 'done':
                            picking_id.move_lines = [(6, 0, workorder.mrp_bom_line_ids.ids)]
                    else:
                        if workorder.mrp_bom_line_ids:
                            picking_id = self.env['stock.picking'].with_context(stock_picking_delivery=True,
                                                                                production_id=workorder.production_id.id).create(
                                {
                                    'picking_workorder_from_mo': True
                                })
                            picking_id.move_lines = [(6, 0, workorder.mrp_bom_line_ids.ids)]
                            workorder.stock_picking_delivery_ids = [(4, picking_id.id)]

                for workorder in record.workorder_ids:
                    picking_id = workorder.stock_picking_delivery_ids.filtered(
                        lambda p: p.picking_workorder_from_mo == True and not p.move_lines)
                    if picking_id:
                        picking_id.do_cancel_stock_picking()

    @api.multi
    def multi_confirm_production(self):
        for record in self:
            if record.state == 'confirmed':
                record.button_plan()

            if record.state == 'planned':
                for workorder in record.workorder_ids:
                    if workorder.state in ['pending', 'ready']:
                        workorder.button_start()
                    if workorder.state in ['progress']:
                        workorder.record_production()

            if record.state == 'progress':
                # record.button_mark_done()
                record.post_inventory()
                moves_to_cancel = (record.move_raw_ids | record.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel'))
                moves_to_cancel.action_cancel()
                query = "UPDATE mrp_production SET state='done' WHERE id = %s" %(record.id)
                self.env.cr.execute(query)

        return True

    @api.model
    def action_confirm_production(self):
        ids         = self.env.context.get('active_ids', [])
        productions = self.browse(ids)

        for record in productions:
            if record.state == 'confirmed':
                record.button_plan()

            if record.state == 'planned':
                for workorder in record.workorder_ids:
                    if workorder.state in ['pending', 'ready']:
                        workorder.button_start()
                    if workorder.state in ['progress']:
                        workorder.record_production()

            if record.state == 'progress':
                record.button_mark_done()

    @api.multi
    def action_delete_production(self):
        # delete move_raw, account_move, quant
        for move in self.move_raw_ids:
            query_1 = """SELECT move_id FROM account_move_line aml
                                    WHERE aml.product_id = '%s' AND aml.name = '%s'""" % (
                move.product_id.id, self.name)
            self.env.cr.execute(query_1)
            account_move_line_ids = self.env.cr.fetchall()
            if account_move_line_ids:
                self.env.cr.execute("""DELETE FROM public.account_move WHERE id = '%s';""" % account_move_line_ids[0])
                self.env.cr.execute("""DELETE FROM account_move_line aml
                          WHERE aml.product_id = '%s' AND aml.name = '%s'""" % (
                    move.product_id.id, self.name))
            if move.quant_ids:
                delete_stock_quant_sql = "DELETE FROM public.stock_quant WHERE id in (%s)" % (', '.join(str(id.id) for id in move.quant_ids))
                self.env.cr.execute(delete_stock_quant_sql)
        if self.move_raw_ids:
            delete_move_raw_sql = "DELETE FROM public.stock_move WHERE id in (%s)" % (
                ', '.join(str(id.id) for id in self.move_raw_ids))
            self.env.cr.execute(delete_move_raw_sql)

        # delete move_finished, account_move, quant
        for move in self.move_finished_ids:
            query_1 = """SELECT move_id FROM account_move_line aml
                                    WHERE aml.product_id = '%s' AND aml.name = '%s'""" % (
                move.product_id.id, self.name)
            self.env.cr.execute(query_1)
            account_move_line_ids = self.env.cr.fetchall()
            if account_move_line_ids:
                self.env.cr.execute(
                    """DELETE FROM public.account_move WHERE id = '%s';""" % account_move_line_ids[0])
                self.env.cr.execute("""DELETE FROM account_move_line aml
                          WHERE aml.product_id = '%s' AND aml.name = '%s'""" % (
                    move.product_id.id, self.name))
            if move.quant_ids:
                delete_stock_quant_sql = "DELETE FROM public.stock_quant WHERE id in (%s)" % (
                ', '.join(str(id.id) for id in move.quant_ids))
                self.env.cr.execute(delete_stock_quant_sql)
        if self.move_finished_ids:
            delete_finished_raw_sql = "DELETE FROM public.stock_move WHERE id in (%s)" % (
                ', '.join(str(id.id) for id in self.move_finished_ids))
            self.env.cr.execute(delete_finished_raw_sql)

        # delete workorder
        for workorder in self.env['mrp.workorder'].search([('production_id', '=', self.id)]):
            workorder.unlink()
        # delete production
        delete_production_sql = "DELETE FROM public.mrp_production WHERE id = '%s';" % self.id
        self.env.cr.execute(delete_production_sql)

        # self.env.cr.execute("DELETE FROM stock_move WHERE inventory_id = %s" % (self.id))

    def _generate_raw_move(self, bom_line, line_data):
        res = super(mrp_production_inherit, self)._generate_raw_move(bom_line, line_data)
        if bom_line:
            res.stt = bom_line.sequence
        return res

    @api.multi
    def delete_raw_material_tab(self):
        productions = self
        if self.env.context.get('active_ids',False) and self.env.context.get('active_model',False) == 'mrp.production':
            productions = self.env['mrp.production'].browse(self.env.context.get('active_ids',False))

        for record in productions:
            if record.move_raw_ids:
                picking_to_confirm = []
                # Cancel stock move done state from do_reset_stock_picking function
                for stock_move in record.move_raw_ids:
                    if stock_move.state == 'done':

                        picking_need_reset = []
                        quant_need_remove = []

                        # TODO: Reset stock quant
                        for stock_quant in stock_move.quant_ids:
                            reseted_move_ids = []

                            # unreserve picking that related to current quant
                            if stock_quant.reservation_id and stock_quant.reservation_id.id:
                                stock_quant.reservation_id.picking_id.do_unreserve()

                            current_location_id = stock_quant.location_id
                            reset_moves         = self.env['stock.move'].search([
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

                                current_location_id = reset_move.location_id
                                reset_moves         = self.env['stock.move'].search([
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
                                self.env.cr.execute("""UPDATE stock_picking SET need_to_confirm = TRUE WHERE id = %s""" % (picking_id,))

                # Step 3: Reset stock move status to draft
                for stock_move in record.move_raw_ids:
                    stock_move.state = 'draft'

                record.move_raw_ids.unlink()