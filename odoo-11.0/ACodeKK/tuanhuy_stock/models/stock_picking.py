# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare


class ReturnPicking(models.Model):
    _inherit = 'stock.picking'
    _order = "id desc, date desc, priority desc"

    need_to_confirm      = fields.Boolean(default=False, string='Xác nhận lại')
    time_to_confirm      = fields.Datetime()
    check_return_picking = fields.Boolean(default=False)
    check_color_picking  = fields.Char(compute='_check_color_picking')
    date_base_order      = fields.Date(string='Ngày theo đơn hàng', compute='_get_date_order')

    @api.model
    def _cron_check_duplicate_quants(self):
        so_return_ids = self.env['sale.order'].search([('sale_order_return','=',True),('sale_order_return_ids','!=',False)])
        for so_return in so_return_ids:
            picking_return = so_return.picking_ids.filtered(lambda p: p.state == 'done')
            picking_so = so_return.mapped('sale_order_return_ids').mapped('picking_ids').filtered(lambda p: p.state == 'done')
            if len(picking_return) == 1:
                for picking_return_mvl in picking_return.move_lines:
                    for picking_so_mvl in picking_so.mapped('move_lines'):
                        if picking_return_mvl.product_id == picking_so_mvl.product_id and picking_return_mvl.product_uom_qty == picking_so_mvl.product_uom_qty:
                            if float_compare(sum(picking_return_mvl.quant_ids.mapped('inventory_value')), sum(picking_so_mvl.quant_ids.mapped('inventory_value')),0) != 0:
                                print "----- SO: %s - %s - sp: %s" %(so_return.id, so_return.name, picking_return_mvl.name)
                        # if picking_return_mvl.product_id == picking_so_mvl.product_id and picking_return_mvl.product_uom_qty != picking_so_mvl.product_uom_qty:
                        #     picking_return_amount = sum(picking_return_mvl.quant_ids.mapped('inventory_value')) / sum(picking_return_mvl.quant_ids.mapped('qty'))
                        #     picking_so_amount = sum(picking_so_mvl.quant_ids.mapped('inventory_value')) / sum(picking_so_mvl.quant_ids.mapped('qty'))
                        #     if float_compare(picking_return_amount,picking_so_amount,0) != 0:
                        #         print "----- SO: %s - %s - sp: %s" % (so_return.id, so_return.name, picking_return_mvl.name)

        # picking_ids = self.env['stock.picking'].search([])
        # for picking in picking_ids:
        #     date = datetime.strptime(picking.min_date,DEFAULT_SERVER_DATETIME_FORMAT).month
        #     if picking.state != 'done' and date == 11:
        #         print "--------picking :%s - %s"%(picking.id,picking.name)

        # so_ids = self.env['sale.order'].search([('state','not in',['draft','cancel'])])
        # po_ids = self.env['purchase.order'].search([])
        # name_so_po = so_ids.mapped('name')
        # for name in name_so_po:
        #     st_id = self.env['stock.picking'].search([('origin', '=', name)])
        #     # if len(st_id) > 1:
        #     #     print "-------name :%s"%(name)
        #     if len(st_id) == 1 and st_id.state == 'done':
        #         am_id = self.env['account.move'].search([('ref','=',st_id.name)])
        #         if len(am_id) < len(st_id.move_lines):
        #             print "-------name :%s - st :%s - am :%s" % (name,st_id.name,am_id.mapped('id'))

        # for so in so_ids:
        #     st_id = self.env['stock.picking'].search([('origin', '=', so.name)])
        #     if not st_id:
        #         print "-------name :%s - id :%s" % (so.name,so.id)
        #     else:
        #         if len(st_id) == 1:
        #             if st_id.state != 'done':
        #                 print "-------name :%s - id :%s" % (so.name, so.id)
        #             if so.date_order != st_id.min_date:
        #                 print "+++++++++++name :%s - id :%s" % (so.name,so.id)

        # for so in so_ids:
        #     st_id = self.env['stock.picking'].search([('origin', '=', so.name)])
        #     if len(st_id) == 1 and st_id.state == 'done':
        #         for line in st_id.move_lines:
        #             if not line.quant_ids:
        #                 print "-------name :%s - id :%s - sp :%s" % (so.name, so.id,line.product_id.name)
        print "Done"

        # picking_ids = self.env['stock.picking'].search([('state', '=', 'done')])
        # picking_error = []
        # for picking_id in picking_ids:
        #     check = False
        #     # if 'PO' in picking_id.origin:
        #     for line in picking_id.move_lines:
        #         if line.product_uom_qty != sum(line.quant_ids.mapped('qty')):
        #             print "+ Picking: %s : sp: %s" % (picking_id.id, line.product_id.default_code)
        #             check = True
        #                 # picking_error.append(picking_id.id)
        #                 # break
        #     if check:
        #         print "=================="

        # self.env['stock.picking'].with_context(active_ids=picking_error).multi_do_reset_stock_picking()
        # self.env['stock.picking'].with_context(active_ids=picking_error).multi_action_confirm_picking()
        # self.env['stock.picking'].with_context(active_ids=picking_error).multi_action_assign()
        #
        # picking_reset_ids = self.env['stock.picking'].search([('state','not in',['done','draft'])]).ids
        # self.env['stock.picking'].with_context(active_ids=picking_reset_ids).multi_action_assign()

    @api.multi
    def _get_date_order(self):
        for record in self:
            if record.sale_id:
                record.date_base_order = record.sale_id.date_order
            if record.purchase_id:
                record.date_base_order = record.purchase_id.date_order

    @api.multi
    def action_assign(self):
        if 'create_from_so' in self._context:
            return True
        res = super(ReturnPicking, self).action_assign()
        return res

    @api.multi
    def multi_do_reset_stock_picking(self):
        ids = self.env.context.get('active_ids', [])
        stock_picking_ids = self.browse(ids)
        for stock_picking_id in stock_picking_ids:
            stock_picking_id.do_reset_stock_picking()

    @api.multi
    def multi_action_confirm_picking(self):
        ids = self.env.context.get('active_ids', [])
        stock_picking_ids = self.browse(ids).sorted('min_date', reverse=False)
        wh_stock = self.env.ref('stock.stock_location_stock')
        for stock_picking_id in stock_picking_ids:
            if stock_picking_id.location_dest_id == wh_stock and stock_picking_id.state == 'draft':
                stock_picking_id.action_confirm()
        for stock_picking_id in stock_picking_ids:
            if stock_picking_id.location_dest_id != wh_stock and stock_picking_id.state == 'draft':
                stock_picking_id.action_confirm()

    @api.multi
    def do_reset_stock_picking(self):
        for picking in self:
            if picking.state == 'done':
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
                    picking_need_reset = []
                    quant_need_remove  = []

                    # TODO: Reset stock quant
                    for stock_quant in stock_move.quant_ids:
                        reseted_move_ids = []

                        # unreserve picking that related to current quant
                        if stock_quant.reservation_id and stock_quant.reservation_id.id:
                            stock_quant.reservation_id.picking_id.do_unreserve()

                        current_location_id = stock_quant.location_id
                        reset_move          = self.env['stock.move'].search([
                            ('location_dest_id', '=', current_location_id.id),
                            ('id', 'in', stock_quant.history_ids.ids),
                            ('id', 'not in', reseted_move_ids),
                        ], order='date DESC', limit=1)
                        if not reset_move or not reset_move.id:
                            raise UserError('Invalid stock quant: %s' %(stock_quant.id))

                        while reset_move.id != stock_move.id:
                            reseted_move_ids.append(reset_move.id)
                            if reset_move.picking_id.id not in picking_need_reset:
                                picking_need_reset.append(reset_move.picking_id.id)

                            current_location_id = reset_move.location_id
                            reset_move          = self.env['stock.move'].search([
                                ('location_dest_id', '=', current_location_id.id),
                                ('id', 'in', stock_quant.history_ids.ids),
                                ('id', 'not in', reseted_move_ids),
                            ], order='date DESC', limit=1)
                            if not reset_move or not reset_move.id:
                                raise UserError('Invalid stock quant: %s' % (stock_quant.id))

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

                query = "UPDATE stock_move SET state='assigned' WHERE picking_id = %s" % (picking.id,)
                self.env.cr.execute(query)

                query = "UPDATE stock_picking SET state='assigned' WHERE id = %s" % (picking.id,)
                self.env.cr.execute(query)
                picking.state = 'assigned'

            elif picking.state == 'waiting':
                if len(picking.move_lines.ids) > 0:
                    # STEP1: Count waiting moves
                    waiting_move = 0
                    for stock_move in picking.move_lines:
                        if stock_move.state == 'waiting':
                            waiting_move += 1

                    # Reset to confirmed
                    if waiting_move == len(picking.move_lines.ids):
                        for stock_move in picking.move_lines:
                            if stock_move.state == 'waiting':
                                stock_move.write({
                                    'state': 'confirmed',
                                    'procure_method': 'make_to_stock',
                                })
                        picking.state = 'confirmed'

                        move_origins = self.env['stock.move'].search([
                            ('move_dest_id', 'in', picking.move_lines.ids)
                        ])
                        if len(move_origins.ids) > 0:
                            move_origins.write({
                                'move_dest_id': False,
                            })

                # STEP3: Auto assign picking after reset
                # picking.action_assign()

        return True

    @api.model
    def cron_update_picking_to_assign(self):
        pickings = self.search([
            ('need_to_reset', '=', True)
        ])
        for picking in pickings:
            if picking.state == 'done':
                picking.do_reset_stock_picking()

            picking.need_to_reset = False

        return True

    @api.model
    def cron_update_picking_to_confirm(self):
        pickings = self.search([
            ('need_to_confirm', '=', True)
        ])
        for to_confirm in pickings:
            if to_confirm.state == 'draft':
                to_confirm.action_confirm()
                to_confirm.action_assign()

            if to_confirm.state == 'confirmed':
                to_confirm.action_assign()

            if to_confirm.state == 'partially_available':
                to_confirm.action_assign()

            if to_confirm.state == 'assigned':
                to_confirm.do_new_transfer()

            if to_confirm.state == 'done':
                to_confirm.need_to_confirm = False
                self.env.cr.commit()
            else:
                pass
                # raise UserError('Can not assign picking %s' %(to_confirm.name))

        return True

    @api.multi
    def do_cancel_stock_picking(self):
        self.do_reset_stock_picking()

        for picking in self:

            for stock_move in picking.move_lines:
                # Step 3: Cancel stock move status
                stock_move.state = 'cancel'
                stock_move.update_account_move_after()

            # Step 4: Cancel stock picking
            picking.state = 'cancel'

            self.env.cr.execute("DELETE FROM stock_move WHERE picking_id = %s" % (picking.id))
            self.env.cr.execute("DELETE FROM stock_pack_operation WHERE picking_id = %s" % (picking.id))
            self.env.cr.execute("DELETE FROM stock_picking WHERE id = %s" % (picking.id))

        return True

    @api.multi
    def multi_action_assign(self):
        ids = self.env.context.get('active_ids', [])
        pickings = self.browse(ids).filtered(lambda r: r.state in ('confirmed', 'partially_available','assigned'))

        if pickings and len(pickings) > 0:
            # Step1: Reset all stock picking
            pickings.do_unreserve()

            for picking in pickings:
                # Step 2: Assign picking one by one
                picking.action_assign()

                # Step3: If picking dont have enough good we assign to other first
                if picking.state == 'partially_available':
                    picking.do_unreserve()
                else:
                    pass

            # Step4: After all assign current confirmed picking
            confirmed_pickings = pickings.filtered(lambda r: r.state in ('confirmed'))
            if confirmed_pickings:
                confirmed_pickings.action_assign()

    @api.multi
    def multi_do_new_transfer(self):
        ids = self.env.context.get('active_ids', [])
        stocklines = self.browse(ids)
        for stock in stocklines:
            if stock.state in ('assigned'):
                stock.do_new_transfer()

    @api.multi
    def remove_picking_done(self):
        for stock_move_line in self.move_lines:
            quant_list = []
            for stock_quant_line in stock_move_line.quant_ids:
                get_stock_move_sql = "SELECT move_id FROM public.stock_quant_move_rel WHERE quant_id = %s" % (stock_quant_line.id)
                self.env.cr.execute(get_stock_move_sql)
                get_stock_move_ids = self.env.cr.fetchall()
                stock_move_list = []
                for line in get_stock_move_ids:
                    if line[0] != stock_move_line.id:
                        stock_move_list.append(line[0])
                stock_move_new_id = self.env['stock.move'].search([('id','in',stock_move_list)],limit=1)
                for quant_line in stock_move_new_id.quant_ids:
                    if quant_line.location_id.id == 15:
                        quant_line.qty += stock_quant_line.qty
                        break
                quant_list.append(str(stock_quant_line.id))

            for quant_id in quant_list:
                delete_stock_quant_sql = "DELETE FROM public.stock_quant WHERE id = %s" % (quant_id)
                self.env.cr.execute(delete_stock_quant_sql)

        delete_stock_move_sql = "DELETE FROM public.stock_move WHERE picking_id = %s" % (self.id)
        self.env.cr.execute(delete_stock_move_sql)

        delete_stock_pack_operation_sql = "DELETE FROM stock_pack_operation WHERE picking_id = %s" % (self.id)
        self.env.cr.execute(delete_stock_pack_operation_sql)

        account_move_ids = self.env['account.move'].search([('ref','=',self.name)])
        if len(account_move_ids) > 1:
            raise UserError('Kiem tra lai')
        elif len(account_move_ids) == 1:
            delete_account_move_line_sql = "DELETE FROM public.account_move_line WHERE move_id = %s" % (account_move_ids.id)
            self.env.cr.execute(delete_account_move_line_sql)
            delete_account_move_sql = "DELETE FROM public.account_move WHERE id = %s" % (account_move_ids.id)
            self.env.cr.execute(delete_account_move_sql)

        # self.unlink()

    @api.multi
    def _check_color_picking(self):
        for record in self:
            if record.group_id and 'SO' in record.group_id.name and record.check_return_picking:
                record.check_color_picking = 'red'
            if record.group_id and 'PO' in record.group_id.name and record.check_return_picking:
                record.check_color_picking = 'blue'
            if record.origin and 'INV' in record.origin and record.check_return_picking:
                record.check_color_picking = 'red'
            if record.origin and 'BILL' in record.origin and record.check_return_picking:
                record.check_color_picking = 'blue'

    @api.multi
    def do_new_transfer(self):
        for pick in self:
            # if pick.state == 'assigned' and pick.picking_type_code == 'outgoing':
            #     check = self.check_stock_picking()
            #     if check:
            #         raise UserError(_('Có 1 Giao Hàng của Sản Phẩm trong tháng trước chưa được Xác nhận'))
            if pick.state == 'cancel':
                raise UserError(_('Phiếu kho đã bị huỷ'))
            if pick.state == 'done':
                raise UserError(_('The pick is already validated'))
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
            # In draft or with no pack operations edited yet, ask if we can just do everything
            if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                # If no lots when needed, raise error
                picking_type = pick.picking_type_id
                if (picking_type.use_create_lots or picking_type.use_existing_lots):
                    for pack in pick.pack_operation_ids:
                        if pack.product_id and pack.product_id.tracking != 'none':
                            raise UserError(
                                _('Some products require lots/serial numbers, so you need to specify those first!'))
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})
                return wiz.process()

            # Check backorder should check for other barcodes
            if pick.check_backorder():
                view = self.env.ref('stock.view_backorder_confirmation')
                wiz = self.env['stock.backorder.confirmation'].create({'pick_id': pick.id})
                # TDE FIXME: same reamrk as above actually
                return {
                    'name': _('Create Backorder?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.backorder.confirmation',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            for operation in pick.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if operation.qty_done > 0:
                    operation.write({'product_qty': operation.qty_done})
                else:
                    pack_operations_delete |= operation
            if pack_operations_delete:
                pack_operations_delete.unlink()
        self.do_transfer()
        return True

    # @api.multi
    # def do_transfer(self):
    #     res = super(ReturnPicking, self).do_transfer()
    #     if 'not_check_date' not in self._context:
    #         for record in self:
    #             wh_stock = self.env.ref('stock.stock_location_stock').id
    #             if record.location_dest_id != wh_stock:
    #                 for mv_line in record.move_lines:
    #                     for quant_id in mv_line.quant_ids:
    #                         min_date_in = False
    #                         origin_in = False
    #                         max_date_out = False
    #                         for line in quant_id.history_ids.sorted('date', reverse=False):
    #                             if line.location_id.id == wh_stock:
    #                                 max_date_out = line.date
    #                             elif not min_date_in:
    #                                 min_date_in = line.date
    #                                 origin_in = line.origin
    #                         if min_date_in:
    #                             datetime.strptime(min_date_in,DEFAULT_SERVER_DATETIME_FORMAT).date()
    #                         if max_date_out:
    #                             datetime.strptime(max_date_out,DEFAULT_SERVER_DATETIME_FORMAT).date()
    #                         if min_date_in > max_date_out:
    #                             origin_in = "Đơn nhập hàng %s sau đơn mua"%(origin_in)
    #                             return {
    #                                 'name': 'Warning',
    #                                 'type': 'ir.actions.act_window',
    #                                 'res_model': 'do.transfer.warning',
    #                                 'view_type': 'form',
    #                                 'view_mode': 'form',
    #                                 'context' : {'picking_id': record.id,'origin_in':origin_in},
    #                                 'target': 'new',
    #                             }
    #
    #     return res

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #
    #     res = super(ReturnPicking, self).fields_view_get(view_id=view_id, view_type=view_type,
    #                                                    toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form' and 'active_id' in self._context:
    #         picking_type = self.env['stock.picking.type'].browse(self._context['active_id'])
    #     return res


    def check_stock_picking(self):
        check = False
        list_product = []
        date = datetime.strftime(datetime.strptime(self.min_date, '%Y-%m-%d %H:%M:%S').date().replace(day=1), '%Y-%m-%d %H:%M:%S')
        for line in self.move_lines:
            if line.product_id.id not in list_product:
                list_product.append(line.product_id.id)
        for product in list_product:
            aml = self.env['stock.move'].search(
                [('product_id', '=', product), ('location_id', '=', self.location_id.id),
                 ('location_dest_id', '=', self.location_dest_id.id), ('state', '=', 'assigned'),('date_expected', '<', date)])
            if aml:
                for picking in aml.mapped('picking_id'):
                    if picking.state == 'assigned':
                        check = True
        return check


    def conver_domain_multi_origin(self, domain, origin_multi):
        count_condition = 0
        list_condition = []
        list_domain = []
        index = False
        check = False
        for do in domain:
            if origin_multi in do:
                if not index:
                    index = domain.index(do)
                do[2] = origin_multi.split()[0]
                count_condition += 1
                list_condition.append([do[0], do[1]])
        for do in reversed(domain):
            if not origin_multi.split()[0] in do:
                if not check:
                    list_domain.append(do)
                    domain.remove(do)
            else:
                check = True
        # if index:
        for i in range(1, len(origin_multi.split())):
            domain.insert(index, unicode('|'))
        # args += domain_or
        for i in range(1, len(origin_multi.split())):
            domain_add = []
            for k in range(1, count_condition):
                domain_add.append(unicode('|'))
            for condition in list_condition:
                cont = condition + [origin_multi.split()[i]]
                domain_add.append(cont)
            domain += domain_add
        domain += list_domain
        return domain

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        origin_multi = False
        for do in domain:
            if 'origin' in do and 'ilike' in do:
                origin_multi = do[2]
        if origin_multi and len(origin_multi.split()) > 1 and all(
                        len(origin) > 12 for origin in origin_multi.split()):
            domain_convert = self.conver_domain_multi_origin(domain, origin_multi)
            domain = domain_convert
        res = super(ReturnPicking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        origin_multi = False
        for do in domain:
            if 'origin' in do and 'ilike' in do:
                origin_multi = do[2]
        if origin_multi and len(origin_multi.split()) > 1 and all(
                        len(origin) > 12 for origin in origin_multi.split()):
            domain_convert = self.conver_domain_multi_origin(domain, origin_multi)
            domain = domain_convert
        res = super(ReturnPicking, self).read_group(domain, fields, groupby, offset=offset,
                                                                                limit=limit, orderby=orderby, lazy=lazy)
        return res



class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def create_picking_return(self):
        res = super(account_invoice, self).create_picking_return()
        res.check_return_picking = True
        return res


class ReturnPicking_return(models.TransientModel):
    _inherit = 'stock.return.picking'

    check_all_return = fields.Boolean('Check\Uncheck All')

    @api.onchange('check_all_return')
    def onchange_check_all_return(self):
        for record in self:
            if record.check_all_return:
                for line in record.product_return_moves:
                    line.to_refund_so = True
            else:
                for line in record.product_return_moves:
                    line.to_refund_so = False

    # @api.multi
    # def _create_returns(self):
    #     for record in self:
    #         if True not in record.product_return_moves.mapped('to_refund_so'):
    #             raise UserError(_('Select at least one product to refund.'))
    #         for line in record.product_return_moves:
    #             if not line.to_refund_so:
    #                 line.unlink()
    #     new_picking, picking_type_id = super(ReturnPicking, self)._create_returns()
    #     picking_id = self.env['stock.picking'].search([('id','=',new_picking)])
    #     if picking_id:
    #         picking_id.check_return_picking = True
    #     return picking_id.id,picking_type_id

class stock_move_inherit(models.Model):
    _inherit = "stock.move"

    check_color_picking = fields.Char(compute="_check_color_picking")

    @api.multi
    def _check_color_picking(self):
        for record in self:
            if record.picking_id and 'WH/OUT' in record.picking_id.name and record.state == 'done':
                record.check_color_picking = 'red'
            if record.picking_id and 'WH/IN' in record.picking_id.name and record.state == 'done':
                record.check_color_picking = 'blue'
