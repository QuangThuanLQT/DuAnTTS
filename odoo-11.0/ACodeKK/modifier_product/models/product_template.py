# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class product_product_inherit(models.Model):
#     _inherit = "product.product"
#
#     @api.model
#     def create(self, values):
#         res = super(product_template, self).create(values)
#         barcode = self.env['ir.sequence'].next_by_code('product.template.barcode') or '/'
#         values['barcode'] = barcode
#         return res

class product_template(models.Model):
    _inherit = 'product.template'

    is_manual_barcode = fields.Boolean('Nhập tay', compute='_compute_manual_barcode', store=True)
    brand_name_select = fields.Many2one('brand.name', string='Thương hiệu')
    brand_name = fields.Char('Mẫu mã')
    source_select = fields.Many2one('source.name', string='Xuất xứ')
    source = fields.Char('Nguồn gốc')
    purchase_code = fields.Char('Mã mua hàng')
    list_price = fields.Float(track_visibility='onchange')

    @api.model
    def create(self, values):
        res = super(product_template, self).create(values)
        barcode = self.env['ir.sequence'].next_by_code('product.template.barcode') or '/'
        res.barcode_ids = res.barcode_ids.new({
            'name': barcode,
        })
        res.product_variant_id.write({
            'barcode': barcode,
        })
        return res

    @api.multi
    def fill_multi_barcode(self):
        for record in self:
            if not record.barcode:
                barcode = self.env['ir.sequence'].next_by_code('product.template.barcode') or '/'
                record.product_variant_id.write({
                    'barcode': barcode,
                })
                self.env.cr.commit()
        return True

    @api.depends('barcode')
    def _compute_manual_barcode(self):
        for record in self:
            manually = True
            if record.barcode:
                if record.barcode.isdigit():
                    if 10000 <= int(record.barcode) <= 99999:
                        manually = False
            else:
                manually = False
            record.is_manual_barcode = manually

    @api.onchange('brand_name_select')
    @api.depends('brand_name_select')
    def onchange_brand_name_select(self):
        self.brand_name = self.brand_name_select.name

    @api.onchange('source_select')
    def onchange_source_select(self):
        self.source = self.source_select.name


class brand_name(models.Model):
    _name = "brand.name"

    name = fields.Char('Thương hiệu')
    tiep_dau_ngu = fields.Char('Tiếp đầu ngữ')

    def action_merge_brand_name(self):
        ids = self.env.context.get('active_ids', [])
        brand_name_ids = self.browse(ids)
        if len(brand_name_ids) > 1:
            action = self.env.ref('modifier_product.merge_brand_name_action').read()[0]
            action['context'] = {'brand_name_id': brand_name_ids[0].id,
                                 'brand_name_ids': (brand_name_ids - brand_name_ids[0]).ids}
            return action

    @api.model
    def update_brand_name(self):
        product_template_ids = self.env['product.template'].search([])
        for product_template_id in product_template_ids:
            if product_template_id.brand_name:
                brand_id = self.env['brand.name'].search([('name', '=', product_template_id.brand_name)])
                if not brand_id:
                    brand_id = self.env['brand.name'].create({'name': product_template_id.brand_name})
                product_template_id.brand_name_select = brand_id


class merge_brand_name(models.TransientModel):
    _name = "merge.brand.name"

    brand_name_id = fields.Many2one('brand.name', string="Thương hiệu đích")
    brand_name_ids = fields.Many2many('brand.name', string="Thương hiệu gộp")

    @api.model
    def default_get(self, fields):
        vals = super(merge_brand_name, self).default_get(fields)
        if 'brand_name_id' in self._context and 'brand_name_ids' in self._context:
            vals['brand_name_id'] = self._context.get('brand_name_id', False)
            vals['brand_name_ids'] = [(6, 0, self._context.get('brand_name_ids', False))]
        return vals

    @api.multi
    def action_merge_brand_name(self):
        list_model_remove = ['merge.brand.name']
        brand_field_ids = self.env['ir.model.fields'].search(
            [('model_id.model', 'not in', list_model_remove), ('ttype', '=', 'many2one'),
             ('relation', '=', 'brand.name'), ('store', '=', True)])

        for brand_name_from in self.brand_name_ids:
            for brand_field_id in brand_field_ids:
                model = brand_field_id.model_id.model
                brand_relate_ids = self.env[model].search([(brand_field_id.name, '=', brand_name_from.id)])
                if model == 'product.template':
                    for brand_relate_id in brand_relate_ids:
                        brand_relate_id.brand_name_select = self.brand_name_id
                        brand_relate_id.brand_name = self.brand_name_id.name
                        sale_order_ids = self.env['sale.order.line'].search(
                            [('product_id', '=', brand_relate_id.product_variant_id.id)])
                        for line in sale_order_ids:
                            self._cr.execute("""UPDATE sale_order_line SET brand_name='%s' WHERE id=%s""" % (
                            self.brand_name_id.name, line.id))
                        purchase_order_ids = self.env['purchase.order.line'].search(
                            [('product_id', '=', brand_relate_id.product_variant_id.id)])
                        for line in purchase_order_ids:
                            self._cr.execute("""UPDATE purchase_order_line SET brand_name='%s' WHERE id=%s""" % (
                            self.brand_name_id.name, line.id))
                else:
                    for brand_relate_id in brand_relate_ids:
                        try:
                            self._cr.execute("""UPDATE %s SET %s=%s WHERE id=%s""" % (
                                model.replace(".", "_"), brand_field_id.name, self.brand_name_id.id,
                                brand_relate_id.id))
                        except:
                            pass

        self.brand_name_ids.unlink()


class source_name(models.Model):
    _name = "source.name"

    name = fields.Char('Xuất xứ')

    @api.model
    def update_source_name(self):
        # product_template_ids = self.env['product.template'].search([])
        # for product_template_id in product_template_ids:
        #     if product_template_id.source:
        #         source_id = self.env['source.name'].search([('name','=',product_template_id.source)])
        #         if not source_id:
        #             source_id = self.env['source.name'].create({'name':product_template_id.source})
        #         product_template_id.source_select = source_id

        invoice_ids = self.env['account.invoice'].search([('state', 'not in', ['draft', 'paid', 'cancel'])])
        for invoice_id in invoice_ids:
            move_line_ids = invoice_id.move_id.mapped('line_ids').filtered(
                lambda mvl: mvl.account_id.code in ['131', '331'])
            for move_line in move_line_ids:
                if not move_line.amount_residual:
                    print
                    "INV: (%s,%s) - MVL: %s" % (invoice_id.id, invoice_id.number, move_line.id)
                    if move_line.debit and not move_line.credit:
                        self._cr.execute("""UPDATE account_move_line SET amount_residual=%s
                                                                                                    WHERE id=%s""" % (
                            move_line.debit, move_line.id))
                    if not move_line.debit and move_line.credit:
                        self._cr.execute("""UPDATE account_move_line SET amount_residual=%s
                                                                            WHERE id=%s""" % (
                            -move_line.credit, move_line.id))
