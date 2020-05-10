# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo
import StringIO
from PIL import Image

class product_template_ihr(models.Model):
    _inherit = 'product.template'

    availability_number = fields.Float(string='Avilability Number')
    color_number = fields.Char(compute='get_color_number')
    range_size = fields.Char(compute='get_color_number')
    website_sale_price = fields.Char(compute='get_website_sale_price')

    image_90x90 = fields.Binary('Image', compute='get_image_90x90', store=True)
    image_300x300 = fields.Binary('Image', compute='get_image_300x300', store=True)

    @api.depends('image')
    def get_image_90x90(self):
        for rec in self:
            image_90x90 = odoo.tools.image_resize_image(rec.image, size=(90, 90))
            rec.image_90x90 = image_90x90

    @api.depends('image')
    def get_image_300x300(self):
        for rec in self:
            image_300x300 = odoo.tools.image_resize_image(rec.image, size=(600, 600))
            rec.image_300x300 = image_300x300

    @api.multi
    def get_website_sale_price(self):
        for rec in self:
            if rec.product_variant_ids:
                product_variant_ids = rec.product_variant_ids.sorted('lst_price', reverse=False)
                if product_variant_ids:
                    if product_variant_ids[0].lst_price == product_variant_ids[len(product_variant_ids)-1].lst_price:
                        rec.website_sale_price = "%s đ" % ('{:,}'.format(int(product_variant_ids[0].lst_price)))
                    else:
                        rec.website_sale_price = "%s đ - %s đ" % ('{:,}'.format(int(product_variant_ids[0].lst_price)), '{:,}'.format(int(product_variant_ids[len(product_variant_ids)-1].lst_price)))
            else:
                rec.website_sale_price = "%s đ" % (int(rec.website_public_price))

    @api.multi
    def get_color_number(self):
        for rec in self:
            attribute_mau_ids = rec.attribute_line_ids.filtered(lambda l: l.attribute_id.name == 'Màu')
            if attribute_mau_ids:
                rec.color_number = "Có %s màu" % (len(attribute_mau_ids.mapped('value_ids')))
            attribute_size_ids = rec.attribute_line_ids.filtered(lambda l: l.attribute_id.name == 'Size')
            if attribute_size_ids:
                value_ids = attribute_size_ids.mapped('value_ids')
                if len(value_ids) == 1:
                    rec.range_size = "%s" % (value_ids.name)
                else:
                    value_size = {
                        '1': 'S',
                        '2': 'M',
                        '3': 'L',
                        '4': 'XL',
                    }
                    if value_ids[0].name in ['S','M','L','XL'] and len(value_ids) <= 4:
                        rec.range_size = "%s - %s" % (value_size.get('1'),value_size.get(str(len(value_ids))))
                    else:
                        rec.range_size = "%s - %s" % (value_ids[0].name,value_ids[(len(value_ids)-1)].name)

    @api.multi
    def write(self, val):
        res = super(product_template_ihr, self).write(val)
        if 'availability_number' in val or 'availability' in val:
            data = {}
            if val.get('availability_number', False):
                data['availability_number'] = val.get('availability_number')
            if val.get('availability', False):
                data['availability'] = val.get('availability')
            for record in self:
                record.product_variant_ids.write(data)
        return res


class product_product_inhr(models.Model):
    _inherit = 'product.product'

    availability = fields.Selection([
        ('empty', 'Hiển thị tồn kho trên trang web và tạm ngừng bán hàng nếu không đủ kho'),
        ('in_stock', 'Hiển thị tồn kho dưới ngưỡng và tạm ngừng bán hàng nếu không đủ kho'),
        ('warning', 'Không hiện thị tồn kho'),
    ], "Availability", default='empty', help="Adds an availability status on the web product page.")

    availability_number = fields.Float(string='Avilability Number')

    image_90x90 = fields.Binary('Image', compute='get_image_90x90', store=True)
    image_300x300 = fields.Binary('Image', compute='get_image_300x300', store=True)

    @api.depends('image')
    def get_image_90x90(self):
        for rec in self:
            image_90x90 = odoo.tools.image_resize_image(rec.image, size=(90, 90))
            rec.image_90x90 = image_90x90

    @api.depends('image')
    def get_image_300x300(self):
        for rec in self:
            image_300x300 = odoo.tools.image_resize_image(rec.image, size=(600, 600))
            rec.image_300x300 = image_300x300

class ProductImage_ihr(models.Model):
    _inherit = 'product.image'

    image_90x90 = fields.Binary('Image',compute='get_image_90x90', store=True)
    image_300x300 = fields.Binary('Image', compute='get_image_300x300', store=True)

    @api.depends('image')
    def get_image_90x90(self):
        for rec in self:
            image_90x90 = odoo.tools.image_resize_image(rec.image, size=(90, 90))
            rec.image_90x90 = image_90x90

    @api.depends('image')
    def get_image_300x300(self):
        for rec in self:
            image_300x300 = odoo.tools.image_resize_image(rec.image, size=(600, 600))
            rec.image_300x300 = image_300x300


