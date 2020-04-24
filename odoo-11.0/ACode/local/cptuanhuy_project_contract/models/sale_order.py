# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order_inherit(models.Model):
    _inherit = 'sale.order'

    # @api.model
    # def default_mrp_routing_id(self):
    #     routing_id = self.env.ref('cptuanhuy_manufacturing.mrp_routing_tuanhuy')
    #     if routing_id:
    #         self.default_mrp_routing_id = routing_id[0].id

    @api.model
    def _get_so_type_id(self):
        so_type_id = self.env.ref('cptuanhuy_project_contract.sale_order_type_thuong_mai')
        if so_type_id:
            return so_type_id.id

    contract_id = fields.Many2one('account.analytic.account',string="Hợp đồng")
    sale_project_id = fields.Many2one('project.project',string="Dự án")
    sale_from_project = fields.Boolean(default=False)
    # mrp_routing_id = fields.Many2one('mrp.routing', string='Quy trình sản xuất')
    # location_dest_id = fields.Many2one('stock.location', string='Kho thành phẩm', domain=[('usage', '=', 'internal')])
    project_manager_id = fields.Many2one('res.users', string="Quản lý dự án",related='contract_id.project_manager_id')
    user_email = fields.Char(string="Email",related='contract_id.user_email')
    user_phone = fields.Char(string="Điện thoại",related='contract_id.user_phone')
    so_type_id = fields.Many2one('sale.order.type',string="Loại đơn hàng",default=_get_so_type_id,required=1)
    check_so_type_sx = fields.Boolean(compute='_get_check_so_type_sx')
    contract_attachment_count = fields.Integer(compute='get_contract_attachment_count')

    # @api.onchange('so_type_id')
    # def onchange_so_type_id(self):
    #     if self.so_type_id:
    #         for line in self.order_line:
    #             line.analytic_tag_ids = self.so_type_id.account_analytic_tag_ids

    @api.multi
    def get_contract_attachment_count(self):
        for record in self:
            if record.contract_id:
                record.contract_attachment_count = len(self.env['ir.attachment'].search([('res_id','=',record.contract_id.id or False),('res_model','=','account.analytic.account')]))

    @api.multi
    def action_show_contract_attachment(self):
        action = self.env.ref("base.action_attachment").read([])[0]
        action['domain'] = [('res_id','=',self.contract_id.id or False),('res_model','=','account.analytic.account')]
        return action

    @api.multi
    @api.onchange('so_type_id')
    def _get_check_so_type_sx(self):
        for record in self:
            if record.so_type_id.type == 'sanxuat':
                record.check_so_type_sx = True
            else:
                record.check_so_type_sx = False

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            self.sale_project_id = self.contract_id.project_id
            self.project_id = self.contract_id
            self.partner_id = self.contract_id.partner_id
            self.sale_project_id = self.contract_id.project_id
            self.project_manager_id = self.contract_id.project_manager_id

    @api.onchange('sale_project_id')
    def onchange_sale_project_id(self):
        if self.sale_project_id:
            self.partner_id = self.sale_project_id.partner_sub_id


    @api.model
    def default_get(self, fields):
        res = super(sale_order_inherit, self).default_get(fields)
        res['sale_from_project'] = self._context.get('sale_from_project', False)
        res['contract_id'] = self._context.get('contract_id', False)
        res['partner_id'] = self._context.get('partner_id', False)
        return res

class sale_order_line_inherit(models.Model):
    _inherit = 'sale.order.line'

    # @api.model
    # def default_get(self, fields):
    #     res = super(sale_order_line_inherit, self).default_get(fields)
    #     if 'analytic_tag_ids' in self._context:
    #         so_type_id = self.env['sale.order.type'].browse(self._context.get('analytic_tag_ids'))
    #         res['analytic_tag_ids'] = [(6,0,so_type_id.account_analytic_tag_ids.ids)]
    #     return res
