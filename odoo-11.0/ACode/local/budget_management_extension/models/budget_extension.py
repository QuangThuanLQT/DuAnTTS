# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from datetime import datetime
from odoo.exceptions import UserError

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    product_budget_lines = fields.One2many('product.budget.lines', 'account_id', string='Product Budget Lines')

class product_budget_lines(models.Model):
    _name = 'product.budget.lines'

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = ""
            if record.account_id and record.crossovered_budget_id:
                name = record.account_id.name + '/' + record.crossovered_budget_id.name
            res.append((record.id, name))
        return res

    @api.depends('product_spent_lines.amount', 'planned_amount')
    def _amount_all(self):
        for order in self:
            amount_spent = percentage = 0.0
            for line in order.product_spent_lines:
                amount_spent += line.amount
            if order.planned_amount > 0.0:
                percentage = float(amount_spent*100.00)/order.planned_amount
            order.update({
                'amount_spent': amount_spent,
                'balance_left': order.planned_amount-amount_spent,
                'percentage': percentage,
                'percentage_left': 100.00-percentage,
            })

    account_id = fields.Many2one("account.analytic.account", string="Account")
    crossovered_budget_id = fields.Many2one("crossovered.budget", string="Budget")
    name = fields.Char("Budget")
    group_product_id = fields.Many2one("group.products", string="Group of Products")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    planned_amount = fields.Float("Planned Amount")
    amount_spent = fields.Float(compute='_amount_all', string="Amount Spent", store=True, readonly=True,)
    balance_left = fields.Float(compute='_amount_all', string="Balance Left", store=True, readonly=True,)
    percentage = fields.Float(compute='_amount_all', string="Percentage Used", store=True, readonly=True,)
    percentage_left = fields.Float(compute='_amount_all', string="Percentage Left", store=True, readonly=True,)
    product_spent_lines = fields.One2many('product.spent.lines', 'group_id', string='Product Budget Lines')

class product_spent_lines(models.Model):
    _name = 'product.spent.lines'

    name = fields.Char("Origin")
    group_id = fields.Many2one("product.budget.lines", string="Product Group")
    group_product_id = fields.Many2one("group.products", string="Group of Products")
    product_id = fields.Many2one("product.product", string="Product")
    responsible_id = fields.Many2one("hr.employee", string="Responsible (person who expensed)")
    supplier_id = fields.Many2one("res.partner", string="Supplier")
    amount = fields.Float("Amount Spent")
    percent_spent = fields.Float("Percent Spent")
    type = fields.Selection([
        ('Supplier Invoice', 'Supplier Invoice'),
        ('Expense', 'Expense')
        ], string='Source Type', copy=False, default='Expense')
    date_expense = fields.Date("Spent Date")

class group_products(models.Model):
    _name = 'group.products'

    name = fields.Char("Name")
    product_ids = fields.Many2many("product.product", string="Group of Products")
    code = fields.Char("Code")

# class AccountInvoice(models.Model):
#     _inherit = "account.invoice"
# 
#     @api.multi
#     def write(self, vals):
#         res = super(AccountInvoice, self).write(vals)
#         if self.type == 'in_invoice' and vals.has_key('state') and vals['state'] == "open":
#             search = self.env['product.budget.lines'].search([('start_date', '<=', self.date_invoice), ('end_date', '>=', self.date_invoice)])
#             if search:
#                 for prod_group in search:
#                     for line in self.invoice_line_ids:
#                         if line.account_analytic_id and line.account_analytic_id.id == prod_group.account_id.id and line.product_id and line.product_id.id in prod_group.group_product_id.product_ids.ids:
#                             price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                             taxes = line.invoice_line_tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
#                             amount = taxes['total_included']
#                             percent_spent = 0.0
#                             if prod_group.planned_amount > 0.0:
#                                 percent_spent = amount*100.0/prod_group.planned_amount
#                             self.env['product.spent.lines'].create({
#                                 'product_id': line.product_id.id,
#                                 'group_id': prod_group.id,
#                                 'name': line.invoice_id.number,
#                                 'amount': amount,
#                                 'supplier_id': line.invoice_id.partner_id.id,
#                                 'type': "Supplier Invoice",
#                                 'group_product_id': prod_group.group_product_id.id,
#                                 'date_expense': self.date_invoice,
#                                 'percent_spent': percent_spent
#                                 })
#         return res

class HrExpense(models.Model):
    _inherit = "hr.expense"

    @api.multi
    def write(self, vals):
        res = super(HrExpense, self).write(vals)
        if vals.has_key('state') and vals['state'] == "accepted":
            search = self.env['product.budget.lines'].search([('start_date', '<=', self.date), ('end_date', '>=', self.date)])
            if search:
                for prod_group in search:
                    if self.analytic_account_id and self.analytic_account_id.id == prod_group.account_id.id and self.product_id and self.product_id.id in prod_group.group_product_id.product_ids.ids:
                        percent_spent = 0.0
                        if prod_group.planned_amount > 0.0:
                            percent_spent = self.total_amount*100.0/prod_group.planned_amount
                        self.env['product.spent.lines'].create({
                            'product_id': self.product_id.id,
                            'group_id': prod_group.id,
                            'name': self.name,
                            'amount': self.total_amount,
                            'responsible_id': self.employee_id.id,
                            'type': "Expense",
                            'group_product_id': prod_group.group_product_id.id,
                            'date_expense': self.date,
                            'percent_spent': percent_spent
                            })
        return res

class PurchaseOrder(models.Model):
    _inherit='purchase.order'
    
    """
        At a time to confirm PO, we need to set Spent Amount in Product Budget Lines.
        Till now, it based on invoice line but we need to set Spent amount on base of 
        Purchase Order.
    """
    @api.multi
    def button_confirm(self):
        for po in self:
            for po_line in po.order_line:
                #Checking for if Project Budget for specific product had exceed or not.  
                total_budget = 0
                if po_line.account_analytic_id:
                    for budget_line in po_line.account_analytic_id.product_budget_lines:
                        group_product = budget_line.group_product_id
                        prod_list = map(int,group_product.product_ids)
                        if po_line.product_id.id in prod_list:
                            total_budget += budget_line.balance_left
                    if total_budget < po_line.price_subtotal:
                        raise UserError(
                            _('Your Purchase is exceeding budget set in : %s') %
                            (po_line.account_analytic_id.name,))
                        
            res = super(PurchaseOrder, self).button_confirm()
            #Make new lines : product spent lines    
            start_date = po.date_order
            if start_date:
                start_date = datetime.strptime(start_date,'%Y-%m-%d %H:%M:%S')
                start_date = start_date.date()
                start_date = datetime.strftime(start_date,'%Y-%m-%d')
                budget_lines = self.env['product.budget.lines'].search([('start_date', '<=', start_date), ('end_date', '>=', start_date)])
                if budget_lines:
                    for budget_line in budget_lines:
                        for line in po.order_line:
                            if line.account_analytic_id and line.account_analytic_id.id == budget_line.account_id.id and line.product_id and line.product_id.id in budget_line.group_product_id.product_ids.ids:
#                                 price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                                price = line.price_unit
                                taxes = line.taxes_id.compute_all(price, line.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                                amount = taxes['total_included']
                                percent_spent = 0.0
                                if budget_line.planned_amount > 0.0:
                                    percent_spent = amount*100.0/budget_line.planned_amount
                                self.env['product.spent.lines'].create({
                                    'product_id': line.product_id.id,
                                    'group_id': budget_line.id,
                                    'name': line.order_id.name,
                                    'amount': amount,
                                    'supplier_id': line.order_id.partner_id.id,
                                    'type': "Supplier Invoice",
                                    'group_product_id': budget_line.group_product_id.id,
                                    'date_expense': start_date,
                                    'percent_spent': percent_spent
                                })
        return res
