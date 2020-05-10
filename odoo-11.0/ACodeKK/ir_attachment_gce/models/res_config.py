# -*- coding: utf-8 -*-
import hashlib

from odoo import models, fields, exceptions, _


class GCESettings(models.TransientModel):
    _name = 'gce.config.settings'
    _inherit = 'res.config.settings'

    gce_bucket = fields.Char(string='GCE bucket name', help="i.e. 'vieterp'")

    def get_default_all(self, fields):
        gce_bucket = self.env["ir.config_parameter"].get_param("gce.bucket", default='')

        return dict(
            gce_bucket=gce_bucket,
        )

    # s3_bucket
    def set_gce_bucket(self):
        self.env['ir.config_parameter'].set_param("gce.bucket",
                                                  self.gce_bucket or '',
                                                  groups=['base.group_system'])

    def upload_existing(self):
        domain = [('type', '!=', 'url'), ('id', '!=', 0)]
        attachments = self.env['ir.attachment'].search(domain)
        attachments = attachments._filter_protected_attachments()

        if attachments:
            bucket_name = self.env['ir.attachment']._get_gce_settings('gce.bucket', 'GCE_BUCKET')
            bucket      = self.env['ir.attachment']._get_gce_resource()

            if not bucket:
                raise exceptions.MissingError(_("Some of the GCE credentials are missing.\n Don't forget to click the ``[Apply]`` button after any changes you've made"))

            for attachment in attachments:
                value     = attachment.datas
                bin_data = value and value.decode('base64') or ''
                fname    = hashlib.sha1(bin_data).hexdigest()

                blob = bucket.blob(fname)
                blob.upload_from_string(bin_data, attachment.mimetype)
                blob.make_public()

                file_name = hashlib.sha1(bin_data).hexdigest()
                vals = {
                    'file_size': len(bin_data),
                    'checksum': attachment._compute_checksum(bin_data),
                    'index_content': attachment._index(bin_data, attachment.datas_fname, attachment.mimetype),
                    'store_fname': file_name,
                    'db_datas': False,
                    'type': 'url',
                    'url': attachment._get_gce_object_url(bucket_name, fname),
                }
                attachment.write(vals)
                self.env.cr.commit()