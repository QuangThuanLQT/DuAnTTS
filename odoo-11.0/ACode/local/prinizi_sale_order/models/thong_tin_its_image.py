# -*- coding: utf-8 -*-

from odoo import models, fields, api


class thong_tin_its(models.Model):
    _name = 'thong.tin.its'

    product_from_id = fields.Many2one('product.product', string='Product Print')
    product_id = fields.Many2one('product.print', string='Product Print')
    size = fields.Char(string='Size')
    lung_tren = fields.Char(string='Lưng trên')
    lung_giua = fields.Char(string='Lưng giữa')
    lung_duoi = fields.Char(string='Lưng dưới')
    in_hinh = fields.Boolean(string='In hình')
    sale_id = fields.Many2one('sale.order')

    @api.onchange('product_from_id')
    def onchange_product_from_id(self):
        product_id = self.product_from_id
        attribute_mau = product_id.attribute_value_ids.filtered(lambda p: p.attribute_id.name == 'Màu')
        if attribute_mau:
            attribute_mau = attribute_mau[0]
            product_print_id = self.env['product.print'].search(
                [('product_id', '=', product_id.product_tmpl_id.id),
                 ('attribute_value_id', '=', attribute_mau.id)], limit=1)
            if product_print_id:
                self.product_id = product_print_id
                self.size = product_id.attribute_value_ids.filtered(
                    lambda p: p.attribute_id.name == 'Size').name or ''

    @api.model
    def create(self, val):
        res = super(thong_tin_its, self).create(val)
        config_thong_tin_its = self.env['config.thong.tin.its'].search(
            [('product_id', '=', res.product_id.id), ('sale_id', '=', res.sale_id.id)])
        if not config_thong_tin_its:
            self.env['config.thong.tin.its'].create({
                'product_id': res.product_id.id,
                'font_chu_so': res.product_id.font_chu_so.id,
                'lung_ao_chat_lieu_its': res.product_id.lung_ao_chat_lieu_its.id,
                'lung_ao_mau_its': res.product_id.lung_ao_mau_its.id,
                'mat_truoc_ao_chat_lieu_its': res.product_id.mat_truoc_ao_chat_lieu_its.id,
                'mat_truoc_ao_mau_its': res.product_id.mat_truoc_ao_mau_its.id,
                'ong_quan_chat_lieu_its': res.product_id.ong_quan_chat_lieu_its.id,
                'ong_quan_mau_its': res.product_id.ong_quan_mau_its.id,
                'tay_ao_chat_lieu_its': res.product_id.tay_ao_chat_lieu_its.id,
                'tay_ao_mau_its': res.product_id.tay_ao_mau_its.id,
                'sale_id': res.sale_id.id,
            })
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            thong_tin_its_ids = self.env['thong.tin.its'].search(
                [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id)])
            if len(thong_tin_its_ids) == 1:
                config_thong_tin_its = self.env['config.thong.tin.its'].search(
                    [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id)])
                if config_thong_tin_its:
                    config_thong_tin_its.unlink()
        res = super(thong_tin_its, self).unlink()
        return res

    @api.multi
    def update_size_ttits(self):
        for line in self.search([('size', '=', False)]):
            if line.product_from_id:
                size = line.product_from_id.attribute_value_ids.filtered(
                    lambda p: p.attribute_id.name == 'Size').name or ''
                line.size = size


class thong_tin_them_its(models.Model):
    _name = 'thong.tin.them.its'

    def dien_tich_in(self):
        dien_tich_in = self.env.ref('prinizi_sales_config_print_attribute.dien_tich_in')
        return [('attribute', '=', dien_tich_in.id)]

    product_ids = fields.Many2many('product.print')
    product_id = fields.Many2one('product.print', string='Product Print')
    vi_tri_in = fields.Many2one('vi.tri.in', tring='Vị trí in', required=1)
    kich_thuot_in = fields.Char('Kích thước in', required=1)
    noi_dung_in = fields.Char('Nội dung in', required=1)
    sale_id = fields.Many2one('sale.order')
    dien_tich_in = fields.Many2one('prinizi.product.attribute.value', string='Diện tích in', domain=dien_tich_in,
                                   required=1)


class thong_tin_in_hinh(models.Model):
    _name = 'thong.tin.in.hinh'

    def chat_lieu_in_hinh(self):
        chat_lieu_in_hinh = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_hinh')
        return [('attribute', '=', chat_lieu_in_hinh.id)]

    def dien_tich_in(self):
        dien_tich_in = self.env.ref('prinizi_sales_config_print_attribute.dien_tich_in')
        return [('attribute', '=', dien_tich_in.id)]

    product_id = fields.Many2one('product.print', string='Product Print')
    vi_tri_in = fields.Many2one('vi.tri.in', tring='Vị trí in hình', required=1)
    vi_tri_in_sub = fields.Char(compute='get_vi_tri_in_sub', store=True)
    chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_hinh,
                                        string='Chất liệu in hình')
    kich_thuot_in = fields.Char('Kích thước in hình', required=1)
    ten_hinh = fields.Char('Tên hình', required=1)
    sale_id = fields.Many2one('sale.order')
    dien_tich_in = fields.Many2one('prinizi.product.attribute.value', string='Diện tích in', domain=dien_tich_in,
                                   required=1)

    @api.depends('vi_tri_in')
    def get_vi_tri_in_sub(self):
        for rec in self:
            if rec.vi_tri_in:
                if rec.vi_tri_in.code in ('lung_ao_tren', 'lung_ao_giua', 'lung_ao_duoi'):
                    rec.vi_tri_in_sub = 'lung_ao_in_hinh'
                elif rec.vi_tri_in.code in ('mat_truoc_ao_nguc_phai', 'mat_truoc_ao_nguc_trai', 'mat_truoc_ao_bung'):
                    rec.vi_tri_in_sub = 'mat_truoc_ao_in_hinh'
                elif rec.vi_tri_in.code in ('ong_quan_trai', 'ong_quan_phai'):
                    rec.vi_tri_in_sub = 'ong_quan_in_hinh'
                elif rec.vi_tri_in.code in ('tay_ao_trai', 'tay_ao_phai'):
                    rec.vi_tri_in_sub = 'ong_tay_ao_in_hinh'

    @api.onchange('vi_tri_in')
    def onchange_vi_tri_in(self):
        for rec in self:
            if rec.vi_tri_in:
                if rec.vi_tri_in.code in ('lung_ao_tren', 'lung_ao_giua', 'lung_ao_duoi'):
                    rec.chat_lieu_in_hinh = rec.product_id.lung_ao_chat_lieu_in_hinh
                elif rec.vi_tri_in.code in ('mat_truoc_ao_nguc_phai', 'mat_truoc_ao_nguc_trai', 'mat_truoc_ao_bung'):
                    rec.chat_lieu_in_hinh = rec.product_id.mat_truoc_ao_chat_lieu_in_hinh
                elif rec.vi_tri_in.code in ('ong_quan_trai', 'ong_quan_phai'):
                    rec.chat_lieu_in_hinh = rec.product_id.ong_quan_chat_lieu_in_hinh
                elif rec.vi_tri_in.code in ('tay_ao_trai', 'tay_ao_phai'):
                    rec.chat_lieu_in_hinh = rec.product_id.tay_ao_chat_lieu_in_hinh


class config_thong_tin_its(models.Model):
    _name = 'config.thong.tin.its'

    def font_chu_so(self):
        font_chu_so = self.env.ref('prinizi_sales_config_print_attribute.font_chu_so')
        return [('attribute', '=', font_chu_so.id)]

    product_id = fields.Many2one('product.print', string='Product Print')
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_id')
    attribute_value_id = fields.Many2one('product.attribute.value', related='product_id.attribute_value_id')
    sale_id = fields.Many2one('sale.order')
    font_chu_so = fields.Many2one('prinizi.product.attribute.value', domain=font_chu_so, string='Font chữ/số mặc định')

    def chat_lieu_in_ten_so(self):
        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        return [('attribute', '=', chat_lieu_in_ten_so.id)]

    def mau_in_ten_so(self):
        mau_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.mau_in_ten_so')
        return [('attribute', '=', mau_in_ten_so.id)]

    lung_ao_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                            string='Chất liệu in lưng áo')
    lung_ao_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so, string='Màu in lưng áo')
    lung_ao = fields.Char(string='Lưng áo', compute='_get_cau_hinh_tt_its', store=True)

    mat_truoc_ao_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                                 string='Chất liệu in mặt trước áo')
    mat_truoc_ao_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so,
                                           string='Màu in mặt trước áo')
    mat_truoc_ao = fields.Char(string='Mặt trước áo', compute='_get_cau_hinh_tt_its', store=True)

    tay_ao_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                           string='Chất liệu in tay áo')
    tay_ao_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so,
                                     string='Màu in tay áo')
    tay_ao = fields.Char(string='Tay áo', compute='_get_cau_hinh_tt_its', store=True)

    ong_quan_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                             string='Chất liệu in ống quần')
    ong_quan_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so,
                                       string='Màu in ống quần')
    ong_quan = fields.Char(string='Ống quần', compute='_get_cau_hinh_tt_its', store=True)

    @api.depends('mat_truoc_ao_chat_lieu_its', 'mat_truoc_ao_mau_its', 'lung_ao_chat_lieu_its', 'lung_ao_mau_its',
                 'tay_ao_chat_lieu_its', 'tay_ao_mau_its', 'ong_quan_chat_lieu_its', 'ong_quan_mau_its')
    def _get_cau_hinh_tt_its(self):
        for rec in self:
            lung_ao = []
            if rec.lung_ao_chat_lieu_its:
                lung_ao.append(rec.lung_ao_chat_lieu_its.name)
            if rec.lung_ao_mau_its:
                lung_ao.append(rec.lung_ao_mau_its.name)
            rec.lung_ao = ', '.join(lung_ao)

            mat_truoc_ao = []
            if rec.mat_truoc_ao_chat_lieu_its:
                mat_truoc_ao.append(rec.mat_truoc_ao_chat_lieu_its.name)
            if rec.mat_truoc_ao_mau_its:
                mat_truoc_ao.append(rec.mat_truoc_ao_mau_its.name)
            rec.mat_truoc_ao = ', '.join(mat_truoc_ao)

            tay_ao = []
            if rec.tay_ao_chat_lieu_its:
                tay_ao.append(rec.tay_ao_chat_lieu_its.name)
            if rec.tay_ao_mau_its:
                tay_ao.append(rec.tay_ao_mau_its.name)
            rec.tay_ao = ', '.join(tay_ao)

            ong_quan = []
            if rec.ong_quan_chat_lieu_its:
                ong_quan.append(rec.ong_quan_chat_lieu_its.name)
            if rec.ong_quan_mau_its:
                ong_quan.append(rec.ong_quan_mau_its.name)
            rec.ong_quan = ', '.join(ong_quan)


# class ProductImage(models.Model):
#     _name = 'product.image'
#
#     name = fields.Char('Name')
#     image = fields.Binary('Image', attachment=True)
#     product_tmpl_id = fields.Many2one('product.template', 'Related Product', copy=True)

class ProductImage(models.Model):
    _inherit = 'sale.order'

    image_print = fields.Many2many('ir.attachment', string="Image")
    note_image = fields.Text()
    # image = fields.Binary(string="Image")
