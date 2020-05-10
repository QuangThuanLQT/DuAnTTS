# -*- coding: utf-8 -*-

from odoo import models, fields, api

class phan_bo(models.Model):
    _name = 'phan.bo'

    start_date = fields.Date(string="Ngày bắt đầu")
    end_date = fields.Date(string="Ngày kết thúc")
    account_id = fields.Many2one('account.account',string="Tài khoản",required=1)

    def check_mrp_production_id(self,production_id):
        if production_id.account_move_ids:
            aml = production_id.account_move_ids.filtered(lambda l: l.account_doiung == self.account_id.code)
            return aml or False

    @api.multi
    def action_phan_bo(self):
        account_ids = self.account_id.ids
        if self.account_id.code:
            parent_code = self.account_id.code
            account_id = self.env['account.account'].search([('id','!=',self.account_id.id)]).filtered(lambda a: a.code[:4] == parent_code)
            if account_id:
                account_ids += account_id.ids
        domain_aml = [('account_id','in',account_ids)]
        domain_mrp = [('state','=','done')]
        if self.start_date:
            domain_aml.append(('date', '>=', self.start_date))
            domain_mrp.append(('date_planned_start', '>=', self.start_date))
        if self.end_date:
            domain_aml.append(('date', '<=', self.end_date))
            domain_mrp.append(('date_planned_start', '<=', self.end_date))
        aml_ids = self.env['account.move.line'].search(domain_aml)
        sum_aml = sum(aml_ids.mapped('debit'))
        if sum_aml != 0:
            mrp_production_ids = self.env['mrp.production'].search(domain_mrp)
            sum_material_cost = sum(mrp_production_ids.mapped('material_cost'))
            account_154 = self.env.ref('l10n_vn.1_chart154').id
            aml_list = []
            if mrp_production_ids:
                for mrp_production_id in mrp_production_ids:
                    aml = self.check_mrp_production_id(mrp_production_id)
                    if aml:
                        move_id = aml.move_id
                        for aml_id in move_id.line_ids:
                            self._cr.execute(
                                """DELETE FROM account_move_line WHERE id=%s""" % (aml_id.id))
                        self._cr.execute(
                            """DELETE FROM account_move WHERE id=%s""" % (move_id.id))
                        break
                sum_amount_aml = 0
                for mrp_production_id in mrp_production_ids:
                    ty_le = mrp_production_id.material_cost / sum_material_cost
                    ty_le = round(ty_le,5)
                    amount_aml = round(sum_aml * ty_le,0)
                    if mrp_production_id == mrp_production_ids[len(mrp_production_ids)-1]:
                        amount_aml = sum_aml - sum_amount_aml
                    sum_amount_aml += amount_aml
                    aml_list.append((0,0,{
                        'debit' : amount_aml,
                        'date' : mrp_production_id.date_planned_start,
                        'account_id' : account_154,
                        'mrp_production_id' : mrp_production_id.id,
                        'name' : mrp_production_id.name,
                    }))
                aml_list.append((0, 0, {
                    'credit': sum_aml,
                    'date': fields.Date.context_today(self),
                    'account_id': self.account_id.id,
                    'name': '/',
                }))

            if aml_list:
                journal_id = self.env.ref('stable_hr_timesheet_invoice.expense_journal')
                obj = self.env['account.move']
                data = obj.sudo().default_get(obj._fields)
                data.update({
                    'journal_id': journal_id.id,
                    'line_ids': aml_list,
                })
                account_move_id = obj.create(data)
                account_move_id.post()

            # for mrp_production_id in mrp_production_ids:
            #     new_cost = mrp_production_id.material_cost + sum(mrp_production_id.account_move_ids.mapped('debit'))
            #     for move in mrp_production_id.move_finished_ids:
            #         move.price_unit = new_cost / move.product_uom_qty
            #         move.quant_ids.write({
            #             'inventory_value' : new_cost / move.product_uom_qty,
            #         })
            #         aml_ids = self.env['account.move.line'].search([('name','=',mrp_production_id.name),('product_code','=',move.product_id.default_code)])
            #         for aml in aml_ids:
            #             if aml.debit > 0:
            #                 self._cr.execute("""UPDATE account_move_line SET debit=%s WHERE id=%s""" % (new_cost,aml.id))
            #             elif aml.credit > 0:
            #                 self._cr.execute(
            #                     """UPDATE account_move_line SET credit=%s WHERE id=%s""" % (new_cost, aml.id))
            #
            #         picking_ids = move.quant_ids.mapped('history_ids').mapped('picking_id')
            #         for picking_id in picking_ids:
            #             picking_id.do_reset_stock_picking()
            #         break

            for mrp_production_id in mrp_production_ids:
                new_cost = mrp_production_id.material_cost + sum(mrp_production_id.account_move_ids.mapped('debit'))
                for move in mrp_production_id.move_finished_ids:
                    total_qty = sum(mrp_production_id.move_finished_ids.mapped('product_uom_qty'))
                    move.price_unit = new_cost / total_qty
                    move.quant_ids.write({
                        'cost' : new_cost / move.product_uom_qty,
                    })
                    for quant_id in move.quant_ids:
                        for move_id  in quant_id.history_ids:
                            if move_id.picking_id:
                                picking_aml_ids = self.env['account.move.line'].search([('ref', '=', move_id.picking_id.name), (
                                'product_code', '=', move.product_id.default_code)])
                                for aml_id in picking_aml_ids:
                                    if aml_id.debit > 0:
                                        self._cr.execute("""UPDATE account_move_line SET debit=%s WHERE id=%s""" % (
                                        new_cost / move.product_uom_qty * move_id.product_uom_qty, aml_id.id))
                                    elif aml_id.credit > 0:
                                        self._cr.execute(
                                            """UPDATE account_move_line SET credit=%s WHERE id=%s""" % (
                                            new_cost / move.product_uom_qty * move_id.product_uom_qty, aml_id.id))
                    aml_ids = self.env['account.move.line'].search([('name','=',mrp_production_id.name),('product_code','=',move.product_id.default_code)])
                    for aml in aml_ids:
                        if aml.debit > 0:
                            self._cr.execute("""UPDATE account_move_line SET debit=%s WHERE id=%s""" % (new_cost,aml.id))
                        elif aml.credit > 0:
                            self._cr.execute(
                                """UPDATE account_move_line SET credit=%s WHERE id=%s""" % (new_cost, aml.id))


                    # picking_ids = move.quant_ids.mapped('history_ids').mapped('picking_id')
                    # for picking_id in picking_ids:
                    #     picking_id.do_reset_stock_picking()
                    break



