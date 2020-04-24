# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    mrp_production_id = fields.Many2one('mrp.production')
    sale_id           = fields.Many2one('sale.order')
    purchase_id       = fields.Many2one('purchase.order')

    @api.model
    def create(self, values):
        result = super(account_move_line, self).create(values)

        if result.invoice_id and result.invoice_id.id:
            if result.invoice_id.type == 'out_invoice':
                for sale_order in result.invoice_id.mapped('invoice_line_ids').mapped('sale_line_ids').mapped('order_id'):
                    result.sale_id             = sale_order
                    result.analytic_account_id = sale_order.contract_id
                    result.analytic_tag_ids    = sale_order.so_type_id.account_analytic_tag_ids

        else:
            if result.move_id.name and 'BILL' in result.move_id.name:
                voucher_id = self.env['account.voucher'].search([
                    ('number', '=', result.move_id.name)
                ])
                if voucher_id and len(voucher_id.ids) == 1:
                    for line in voucher_id.line_ids:
                        line_name = line.name or '/'
                        if line.sale_id and line_name == result.name and abs(line.price_unit) == abs(result.credit + result.debit):
                            result.sale_id             = line.sale_id
                            result.analytic_account_id = line.sale_id.contract_id
                            result.analytic_tag_ids    = line.sale_id.so_type_id.cost_account_analytic_tag_ids
                            result.purchase_id         = line.purchase_id
            elif result.move_id.ref:
                picking_id = self.env['stock.picking'].search([
                    ('name', '=', result.move_id.ref)
                ])
                if picking_id and len(picking_id.ids) == 1:
                    if picking_id.sale_id:
                        result.sale_id             = picking_id.sale_id
                        result.analytic_account_id = picking_id.sale_id.contract_id
                        result.analytic_tag_ids    = picking_id.sale_id.so_type_id.cost_account_analytic_tag_ids
                    elif picking_id.sale_select_id:
                        result.sale_id             = picking_id.sale_select_id
                        result.partner_id          = picking_id.sale_select_id.partner_id
                        result.analytic_account_id = picking_id.sale_select_id.contract_id
                        result.analytic_tag_ids    = picking_id.sale_select_id.so_type_id.cost_account_analytic_tag_ids

        if self.env.context.get('force_set_analytic_tag_by_picking_type',False):
            result.write({'analytic_tag_ids' : [(6,0,self.env.context.get('force_set_analytic_tag_by_picking_type',False))]})
        return result

    @api.depends('move_id', 'debit', 'credit')
    def Z(self):
        for record in self:
            list = record.get_account_1121()
            for account_code in list:
                if '1121' in account_code:
                    record.account_doi_ung_1121 = True
                else:
                    record.account_doi_ung_1121 = False

    def update_account_doi_ung_1121(self):
        list_id = []
        for record in self.env['account.move'].search([('journal_id.type', 'in', ['sale', 'purchase', 'bank'])]):
            for aml in record.line_ids.filtered(lambda r: '1121' not in r.account_id.code):
                list = []
                if aml.debit > aml.credit:
                    for line in record.line_ids:
                        if line.credit > 0 and line.account_id.code not in list:
                            list.append(line.account_id.code)
                elif aml.debit < aml.credit:
                    for line in record.line_ids:
                        if line.debit > 0 and line.account_id.code not in list:
                            list.append(line.account_id.code)
                else:
                    for line in record.line_ids.filtered(lambda l: l.account_id.code != line.account_id.code):
                        if line.account_id.code not in list:
                            list.append(line.account_id.code)

                for account_code in list:
                    if '1121' in account_code:
                        if aml.id not in list_id:
                            list_id.append(aml.id)
        sql = """UPDATE account_move_line SET account_doi_ung_1121 = TRUE WHERE id in (%s);""" % (
                ', '.join(str(e) for e in list_id))
        self.env.cr.execute(sql)
        return True