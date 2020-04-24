# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    brand_name = fields.Char('Thương Hiệu', readonly=True)
    group_id   = fields.Many2one('product.group', 'Nhóm', readonly=True)
    group_kh1_id = fields.Many2one('partner.group.hk1', string="Nhóm Khách Hàng 1")
    group_kh2_id = fields.Many2one('partner.group.hk2', string="Nhóm Khách Hàng 2")

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    CASE
                      WHEN s.sale_order_return = true 
                        THEN SUM(l.product_uom_qty / u.factor * u2.factor * -1)
                        ELSE SUM(l.product_uom_qty / u.factor * u2.factor)
                    END as product_uom_qty,
                    CASE
                      WHEN s.sale_order_return = true 
                        THEN SUM(l.qty_delivered / u.factor * u2.factor * -1)
                        ELSE SUM(l.qty_delivered / u.factor * u2.factor)
                    END as qty_delivered,
                    CASE
                      WHEN s.sale_order_return = true 
                        THEN SUM(l.qty_invoiced / u.factor * u2.factor * -1)
                        ELSE SUM(l.qty_invoiced / u.factor * u2.factor)
                    END as qty_invoiced,
                    CASE
                      WHEN s.sale_order_return = true 
                        THEN SUM(l.qty_to_invoice / u.factor * u2.factor * -1)
                        ELSE SUM(l.qty_to_invoice / u.factor * u2.factor)
                    END as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    CASE
                      WHEN s.sale_order_return = true 
                        THEN SUM(l.price_subtotal / COALESCE(cr.rate, 1.0) * -1)
                        ELSE SUM(l.price_subtotal / COALESCE(cr.rate, 1.0))
                    END as price_subtotal,
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
                    s.project_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume,
                    t.brand_name as brand_name,
                    t.group_id as group_id,
                    partner.group_kh1_id as group_kh1_id,
                    partner.group_kh2_id as group_kh2_id
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        group_by_str = '%s %s' % (group_by_str, ', t.brand_name, t.group_id, s.sale_order_return, partner.group_kh1_id, partner.group_kh2_id ')
        return group_by_str