# -*- coding: utf-8 -*-
import os
import hashlib
import logging
import requests
import base64

from google.cloud import storage
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    gce_url = fields.Char('GCE URL')

    @api.model
    def _get_gce_settings(self, param_name, os_var_name):
        config_obj = self.env['ir.config_parameter']
        res = config_obj.get_param(param_name)
        if not res:
            res = os.environ.get(os_var_name)
            if res:
                config_obj.set_param(param_name, res)
                _logger.info('parameter {} has been created from env {}'.format(param_name, os_var_name))
        return res

    @api.model
    def _set_gce_settings(self, param_name, param_value):
        config_obj = self.env['ir.config_parameter']
        res = config_obj.set_param(param_name, param_value)
        return res

    @api.model
    def _get_gce_object_url(self, bucket_name, file_name):
        object_url = "http://storage.googleapis.com/{0}/{1}".format(bucket_name, file_name)
        return object_url

    @api.model
    def _get_storage_client(self):
        storage_client = storage.Client.from_service_account_json(
            os.path.dirname(os.path.realpath(__file__ + '/../../../../../../')) + '/config/production/99dd971024f5.json')
        return storage_client

    @api.model
    def _get_gce_resource(self):
        try:
            bucket_name = self._get_gce_settings('gce.bucket', 'vieterp')

            storage_client = self._get_storage_client()
            bucket = storage_client.get_bucket(bucket_name)
        except Exception, e:
            return None
        return bucket

    def _inverse_datas(self):
        bucket = self._get_gce_resource()

        if bucket:
            bucket_name = self._get_gce_settings('gce.bucket', 'vieterp')

            gce_records = self
            gce_records = gce_records.filtered(lambda r: r.res_model == 'ir.ui.view' and r.name.startswith('/web/content/'))

            for attachment in gce_records:
                if not attachment.gce_url:
                    # TODO: Upload protected url to gce
                    value    = attachment.datas
                    bin_data = value and value.decode('base64') or ''
                    fname    = hashlib.sha1(bin_data).hexdigest()

                    blob = bucket.blob(fname)
                    blob.upload_from_string(bin_data, attachment.mimetype)
                    blob.make_public()

                    vals = {
                        'gce_url': attachment._get_gce_object_url(bucket_name, fname),
                    }
                    attachment.write(vals)
                    self.env.cr.commit()

            attachments = self._filter_protected_attachments()
            for attachment in attachments:
                value    = attachment.datas
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
                super(IrAttachment, attachment.sudo()).write(vals)

            super(IrAttachment, self - attachments)._inverse_datas()
        return super(IrAttachment, self)._inverse_datas()

    @api.model
    def _create_bucket(self, bucket_name):
        storage_client = self._get_storage_client()
        bucket = storage_client.create_bucket(bucket_name)

        self.update_attachments()
        return bucket

    @api.model
    def update_attachments(self):
        bucket_name = self._get_gce_settings('gce.bucket', 'vieterp')

        domain      = [('type', '!=', 'url'), ('id', '!=', 0)]
        attachments = self.env['ir.attachment'].search(domain)
        bucket      = self._get_gce_resource()

        if bucket:
            protecteds = attachments.filtered(lambda r: r.res_model == 'ir.ui.view' and r.name.startswith('/web/content/'))
            if protecteds:
                for attachment in protecteds:
                    # TODO: Upload protected url to gce
                    if not attachment.gce_url:
                        value    = attachment.datas
                        bin_data = value and value.decode('base64') or ''
                        fname    = hashlib.sha1(bin_data).hexdigest()

                        blob = bucket.blob(fname)
                        blob.upload_from_string(bin_data, attachment.mimetype)
                        blob.make_public()

                        vals = {
                            'gce_url': attachment._get_gce_object_url(bucket_name, fname),
                        }
                        attachment.write(vals)
                        self.env.cr.commit()

            attachments = attachments - protecteds

            if attachments:
                for attachment in attachments:
                    value    = attachment.datas
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
                    super(IrAttachment, attachment.sudo()).write(vals)
                    self.env.cr.commit()

    @api.depends('store_fname', 'db_datas')
    def _compute_datas(self):
        bin_size = self._context.get('bin_size')
        url_records = self.filtered(lambda r: r.type in ['url', 'binary'] and r.gce_url)
        for attach in url_records:
            if not bin_size:
                r = requests.get(attach.gce_url)
                attach.datas = base64.b64encode(r.content)
            else:
                attach.datas = "1.00 Kb"

        super(IrAttachment, self - url_records)._compute_datas()

    @api.model
    def cron_update_gce(self):
        bucket_name = self._get_gce_settings('gce.bucket', 'vieterp')
        unique_bucket_name = self.env['ir.config_parameter'].get_param('database.uuid')

        if bucket_name != unique_bucket_name:
            bucket_name = unique_bucket_name
            self._set_gce_settings('gce.bucket', bucket_name)
            self.env.cr.commit()

            try:
                bucket = self._get_gce_resource()
                if not bucket:
                    self._create_bucket(bucket_name)
            except Exception as e:
                self._create_bucket(bucket_name)
        else:
            # Only run one time
            query = "UPDATE ir_cron SET active=false WHERE name = '%s'" % ('Marketplace Update GCE',)
            self.env.cr.execute(query)