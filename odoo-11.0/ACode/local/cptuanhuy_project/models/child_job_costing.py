# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class child_job_costing(models.Model):
    _name = "child.job.costing"

    job_type_id = fields.Many2one('job.type',string="Hạng mục")
    child_job_costing_id = fields.Many2one('job.costing',string="Báo giá con",required=1)
    parent_job_costing_id = fields.Many2one('job.costing',string="Báo giá cha")
    quantity = fields.Integer(string="Số lượng",default=1)
    price = fields.Float(string="Chi phí / Đơn vị")
    labor_cost = fields.Float(string="Đơn giá nhân công")
    move_cost = fields.Float(string="Máy Thi Công Vận Chuyển")
    manager_cost = fields.Float(string="Quản Lý Giám Sát TC")
    verage_cost = fields.Float(string="Chi phí dự kiến", compute='_get_verage_cost')
    sub_total = fields.Float(string="Tổng phụ")
    total_discount = fields.Float(string="Giảm giá",related='child_job_costing_id.total_discount')

    @api.multi
    def _get_verage_cost(self):
        for record in self:
            if record.child_job_costing_id:
                sum_verage_cost = 0
                for line in self.child_job_costing_id.job_cost_line_ids:
                    sum_verage_cost += line.verage_cost * line.product_qty
                record.verage_cost = sum_verage_cost

    def get_amount_child_jc(self,child_job_costing_id,quantity):
        sum_cost_price = sum_labor_cost = sum_move_cost = sum_manager_cost = 0
        child_cost_price = child_labor_cost = child_move_cost = child_manager_cost = 0
        for line in self.child_job_costing_id.job_cost_line_ids:
            sum_cost_price += line.cost_price * line.product_qty * quantity
            sum_labor_cost += line.labor_cost * line.product_qty * quantity
            sum_move_cost += line.move_cost * line.product_qty * quantity
            sum_manager_cost += line.manager_cost * line.product_qty * quantity
        for child_jc in child_job_costing_id.child_job_costing_ids:
            child_cost_price, child_labor_cost, child_move_cost, child_manager_cost = child_jc.get_amount_child_jc(child_jc.child_job_costing_id,child_jc.quantity)
        sum_cost_price += child_cost_price
        sum_labor_cost += child_labor_cost
        sum_move_cost += child_move_cost
        sum_manager_cost += child_manager_cost
        return sum_cost_price, sum_labor_cost, sum_move_cost, sum_manager_cost


    @api.onchange('child_job_costing_id','quantity')
    def onchange_child_job_costing(self):
        if self.child_job_costing_id:
            sum_cost_price, sum_labor_cost, sum_move_cost, sum_manager_cost = self.get_amount_child_jc(self.child_job_costing_id,1)
            self.price = sum_cost_price
            self.labor_cost = sum_labor_cost
            self.move_cost = sum_move_cost
            self.manager_cost = sum_manager_cost
            self.sub_total = (sum_cost_price + sum_labor_cost + sum_move_cost + sum_manager_cost - self.total_discount) * self.quantity

