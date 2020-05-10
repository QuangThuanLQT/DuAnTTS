# -*- coding: utf-8 -*-
from odoo import models, fields, api

class product_template(models.Model):
    _inherit = 'product.template'

    labor_cost = fields.Float("Labor Cost")
    account_analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Doanh thu')
    cost_account_analytic_tag_ids = fields.Many2many('account.analytic.tag', 'product_template_analytic_tag_rel',
                                                     'product_id', 'tag_id', string='Chi Phí')


    @api.onchange('route_ids')
    def compute_account_analytic_tag(self):
        manufacture_id = self.env.ref('mrp.route_warehouse0_manufacture')

        cp_sx = self.env.ref('cptuanhuy_project.cost_account_analytic_tag_san_xuat')
        dt_sx = self.env.ref('cptuanhuy_project.account_analytic_tag_san_xuat')
        cp_tm = self.env.ref('cptuanhuy_project.cost_account_analytic_tag_thuong_mai')
        dt_tm = self.env.ref('cptuanhuy_project.account_analytic_tag_thuong_mai')

        if manufacture_id in self.route_ids:
            self.account_analytic_tag_ids = dt_sx
            self.cost_account_analytic_tag_ids = cp_sx
        else:
            self.account_analytic_tag_ids = dt_tm
            self.cost_account_analytic_tag_ids = cp_tm

    @api.multi
    def update_account_analytic_tag_product(self):
        manufacture_id = self.env.ref('mrp.route_warehouse0_manufacture')

        cp_sx = self.env.ref('cptuanhuy_project.cost_account_analytic_tag_san_xuat')
        dt_sx = self.env.ref('cptuanhuy_project.account_analytic_tag_san_xuat')
        cp_tm = self.env.ref('cptuanhuy_project.cost_account_analytic_tag_thuong_mai')
        dt_tm = self.env.ref('cptuanhuy_project.account_analytic_tag_thuong_mai')
        for product in self.search([]):
            if manufacture_id in product.route_ids:
                product.account_analytic_tag_ids = dt_sx
                product.cost_account_analytic_tag_ids = cp_sx
            else:
                product.account_analytic_tag_ids = dt_tm
                product.cost_account_analytic_tag_ids = cp_tm

class product_product(models.Model):
    _inherit = 'product.product'

    labor_cost = fields.Float("Labor Cost",related='product_tmpl_id.labor_cost')

    @api.onchange('labor_cost')
    def change_labor_cost(self):
        if self.product_tmpl_id:
            self.product_tmpl_id.labor_cost = self.labor_cost
