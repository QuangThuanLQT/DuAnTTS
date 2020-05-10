# -*- coding: utf-8 -*-
from odoo import http
from odoo import api, models
from odoo import SUPERUSER_ID
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def binary_content(cls, xmlid=None, model='ir.attachment', id=None, field='datas', unique=False, filename=None,
                       filename_field='datas_fname', download=False, mimetype=None,
                       default_mimetype='application/octet-stream', env=None):
        env = env or request.env
        if request.env['res.users'].has_group('website.group_website_publisher'):
            env = env(user=SUPERUSER_ID)
        return super(Http, cls).binary_content(xmlid=xmlid, model=model, id=id, field=field, unique=unique,
                                               filename=filename, filename_field=filename_field, download=download,
                                               mimetype=mimetype, default_mimetype=default_mimetype, env=env)

