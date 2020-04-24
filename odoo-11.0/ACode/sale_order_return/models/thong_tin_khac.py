# -*- coding: utf-8 -*-

from odoo import models, fields, api


class thong_tin_khac(models.Model):
    _inherit = 'sale.order.return'

    warehouse_id = fields.Many2one('stock.warehouse', string='Kho')
    incoterm = fields.Many2one('stock.incoterms', string='Incoterms',
                           help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    picking_policy = fields.Selection([
        ('direct', 'Cung cấp từng sản phẩm khi có sẵn'),
        ('one', 'Cung cấp tất cả các sản phẩm cùng một lúc')],
        string='Chính sách vận chuyển', required=True, default='direct')

    fiscal_position_id = fields.Char(string='Vị trí tài chính')

    tag_ids = fields.Char(string='Thẻ')
    team_id = fields.Many2one('crm.team', string='Đội ngũ bán hàng')
    client_order_ref = fields.Char(string='Tham khảo khách hàng')

    origin = fields.Char(string='Tài liệu nguồn')
    campaign_id = fields.Many2one('utm.campaign', string='Chiến dịch')
    medium_id = fields.Many2one('utm.medium', string='Trung bình')
    source_id = fields.Many2one('utm.source', string='Nguồn',
                                help="This is the link source, e.g. Search Engine, another domain,or name of email list")
    opportunity_id = fields.Char(string='Cơ hội')



