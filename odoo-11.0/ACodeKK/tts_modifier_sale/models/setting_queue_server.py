# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import gearman
from odoo.exceptions import ValidationError


class setting_queue_server(models.Model):
    _name = 'setting.queue.server'

    @api.model
    def _compute_default_prefix(self):
        return self.env.cr.dbname

    name = fields.Char(string='Model')
    queue_server = fields.Char(string='Queue Server')
    active = fields.Boolean(default=False)
    prefix = fields.Char(required=1, string='Prefix', default=_compute_default_prefix)

    @api.multi
    def check_connect(self):
        try:
            queue_server = self.queue_server
            gm_client = gearman.GearmanClient([queue_server])
            job_name = "%s_check_connect" %(self.prefix)
            job_request = gm_client.submit_job(job_name.encode('ascii', 'ignore'), "arbitrary binary data")
            if job_request.complete:
                self.active = True
            else:
                raise ValidationError('Connect failed!')
        except:
            raise ValidationError('Connect failed!')