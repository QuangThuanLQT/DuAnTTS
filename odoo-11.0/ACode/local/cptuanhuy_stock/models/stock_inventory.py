# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    def set_to_confirm_inventory(self):
        for move in self.move_ids:
            query_1 = """SELECT move_id FROM account_move_line aml 
                                    WHERE aml.product_id = '%s' AND aml.date = '%s' AND aml.name like '%s'""" % (
                move.product_id.id, self.accounting_date or self.date, ('%' + self.name))
            self.env.cr.execute(query_1)
            account_move_line_ids = self.env.cr.fetchall()
            if account_move_line_ids:
                self.env.cr.execute("""DELETE FROM public.account_move WHERE id = '%s';""" % account_move_line_ids[0])
                self.env.cr.execute("""DELETE FROM account_move_line aml 
                          WHERE aml.product_id = '%s' AND aml.date = '%s' AND aml.name like '%s'""" % (
                    move.product_id.id, self.accounting_date or self.date, ('%' + self.name)))
        self.state = 'confirm'
        self.env.cr.execute("DELETE FROM stock_move WHERE inventory_id = %s" % (self.id))

    name = fields.Char(
        'Inventory Reference',
        readonly=False, required=True,
        states={'done': [('readonly', True)]})