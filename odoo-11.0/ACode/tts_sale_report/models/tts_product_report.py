# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class tts_product_report(models.Model):
    _name = "tts.product.report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Tham chiếu đơn hàng', readonly=True)
    date = fields.Datetime('Ngày đặt hàng', readonly=True)
    product_id = fields.Many2one('product.product', 'Sản phẩm', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Đơn vị đo lường', readonly=True)
    product_uom_qty = fields.Float('# of Qty', readonly=True)
    qty_delivered = fields.Float('SL đã giao', readonly=True)
    qty_to_invoice = fields.Float('SL chờ xuất hoá đơn', readonly=True)
    qty_invoiced = fields.Float('SL đã xuất hoá đơn', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Đối tác', readonly=True)
    company_id = fields.Many2one('res.company', 'Công ty', readonly=True)
    user_id = fields.Many2one('res.users', 'Nhân viên kinh doanh', readonly=True)
    price_total = fields.Float('Tổng', readonly=True)
    price_subtotal = fields.Float('Giá trị trước thuế', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Mẫu sản phẩm', readonly=True)
    categ_id = fields.Many2one('product.category', 'Danh mục sản phẩm', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Bảng giá', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Tài khoản phân tích', readonly=True)
    team_id = fields.Many2one('crm.team', 'Đội ngũ bán hàng', readonly=True, oldname='section_id')
    country_id = fields.Many2one('res.country', 'Quốc gia đối tác', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Đối tượng thương mại', readonly=True)
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('sent', 'Báo giá đã gửi'),
        ('sale', 'Đơn đặt hàng'),
        ('done', 'Bán hàng xong'),
        ('cancel', 'Đã huỷ'),
    ], string='Tình trạng', readonly=True)
    weight = fields.Float('Trọng lượng thô', readonly=True)
    volume = fields.Float('Âm lượng', readonly=True)

    # qty_product_sale = fields.Float('Số lượng sản phẩm khách hàng đã mua', readonly=True)
    # total_amount = fields.Float('Doanh thu', readonly=True)
    # qty_product_return = fields.Float('Số lượng sản phẩm khách hàng trả', readonly=True)
    # amount_return = fields.Float('Giá trị trả', readonly=True)
    # net_amount = fields.Float('Danh thu thuần', readonly=True)


def _select(self):
    select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
               
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
    return select_str


def _from(self):
    from_str = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                    left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    left join currency_rate cr on (cr.currency_id = pp.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
        """
    return from_str


def _group_by(self):
    group_by_str = """
            WHERE s.state = 'sale'
            GROUP BY l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.name,
                    s.date_order,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                   
                    s.team_id,
                    p.product_tmpl_id,
                    partner.country_id,
                
                    partner.commercial_partner_id
        """
    return group_by_str


@api.model_cr
def init(self):
    # self._table = sale_report
    tools.drop_view_if_exists(self.env.cr, self._table)
    self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))
