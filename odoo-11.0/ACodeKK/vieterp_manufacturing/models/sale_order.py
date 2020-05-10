# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil import relativedelta

class sale_order(models.Model):
    _inherit = 'sale.order'

    bom_count = fields.Float(compute='_compute_bom_count', string='BOM Count', store=True)
    mo_count  = fields.Float(compute='_compute_mo_count', string='MO Count', store=True)
    bom_ids   = fields.One2many('mrp.bom', 'so_id', 'BOMs')
    mo_ids    = fields.One2many('mrp.production', 'so_id', 'Productions')

    @api.depends('bom_ids')
    def _compute_bom_count(self):
        for record in self:
            record.bom_count = len(record.bom_ids)

    @api.depends('mo_ids')
    def _compute_mo_count(self):
        for record in self:
            record.mo_count = len(record.mo_ids)

    @api.multi
    def action_create_mo(self):
        production_obj = self.env['mrp.production']

        self.action_create_bom()

        for record in self:
            for line in record.order_line:
                mo = production_obj.search([
                    ('so_line_id','=',line.id),
                    ('product_id','=',line.product_id.id)
                ], limit=1)
                if mo:
                    continue

                bom_obj = self.env['mrp.bom']
                bom     = bom_obj.search([
                    ('so_id','=',record.id),
                    ('product_id','=',line.product_id.id)
                ], limit=1)
                if not bom or not bom.id:
                    raise UserError(_('Please create BOM before create MO!'))

                # company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
                newdate = datetime.strptime(record.date_order.split(' ')[0], '%Y-%m-%d') #  - relativedelta(days=line.product_id.produce_delay or 0)
                # newdate = newdate - relativedelta(days=company.manufacturing_lead)
                produce = production_obj.create({
                    'origin': record.name,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'product_uom_id': line.product_uom and line.product_uom.id or False,
                    'so_id': record.id,
                    'bom_id': bom and bom.id or False,
                    'so_line_id': line.id,
                    # 'product_uos_qty': line.product_uos and line.product_uos_qty or False,
                    # 'product_uos': line.product_uos and line.product_uos.id or False,
                    # 'location_src_id': production_obj._src_id_default(cr, uid, []),
                    # 'location_dest_id': production_obj._dest_id_default(cr, uid, []),
                    'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                })
                # produce.button_plan()
                # bom_result = production_obj.action_compute([produce_id], [])
                # wf_service.trg_validate(uid, 'mrp.production', produce_id, 'button_confirm', cr)
        return self.action_view_mo()

    @api.multi
    def action_view_mo(self):
        mos = []
        for record in self:
            mos = self.env['mrp.production'].search([('so_id', '=', record.id)])
        if not mos:
            raise UserError(_('There is no manufacturing order!'))

        view = self.env.ref('vieterp_manufacturing.sale_open_mo')
        result = view.read()[0]
        result['context'] = {'group_by': None, 'default_so_id': self.ids[0], 'search_default_so_id': self.ids[0]}
        return result