import functools
import itertools

import psycopg2
import pytz

from odoo import api, fields, models, _
from odoo.tools import ustr


class IrFieldsConverter(models.AbstractModel):
    _inherit = 'ir.fields.converter'

    @api.model
    def db_id_for(self, model, field, subfield, value):
        """ Finds a database id for the reference ``value`` in the referencing
        subfield ``subfield`` of the provided field of the provided model.

        :param model: model to which the field belongs
        :param field: relational field for which references are provided
        :param subfield: a relational subfield allowing building of refs to
                         existing records: ``None`` for a name_get/name_search,
                         ``id`` for an external id and ``.id`` for a database
                         id
        :param value: value of the reference to match to an actual record
        :param context: OpenERP request context
        :return: a pair of the matched database identifier (if any), the
                 translated user-readable name for the field and the list of
                 warnings
        :rtype: (ID|None, unicode, list)
        """
        id = None
        warnings = []
        action = {'type': 'ir.actions.act_window', 'target': 'new',
                  'view_mode': 'tree,form', 'view_type': 'form',
                  'views': [(False, 'tree'), (False, 'form')],
                  'help': _(u"See all possible values")}
        if subfield is None:
            action['res_model'] = field.comodel_name
        elif subfield in ('id', '.id'):
            action['res_model'] = 'ir.model.data'
            action['domain'] = [('model', '=', field.comodel_name)]

        RelatedModel = self.env[field.comodel_name]
        if subfield == '.id':
            field_type = _(u"database id")
            try:
                tentative_id = int(value)
            except ValueError:
                tentative_id = value
            try:
                if RelatedModel.search([('id', '=', tentative_id)]):
                    id = tentative_id
            except psycopg2.DataError:
                # type error
                raise self._format_import_error(
                    ValueError,
                    _(u"Invalid database id '%s' for the field '%%(field)s'"),
                    value,
                    {'moreinfo': action})
        elif subfield == 'id':
            field_type = _(u"external id")
            if '.' in value:
                xmlid = value
            else:
                xmlid = "%s.%s" % (self._context.get('_import_current_module', ''), value)
            try:
                id = self.env.ref(xmlid).id
            except ValueError:
                pass  # leave id is None
        elif subfield is None:
            field_type = _(u"name")
            ids = RelatedModel.name_search(name=value, operator='=')
            if field.name == 'ma_doi_tuong_co' or field.name == 'ma_doi_tuong_no' and model._name == 'tts_journal_entry.nhatkychung':
                if not ids:
                    data = RelatedModel.default_get(RelatedModel._fields)
                    data['name'] = value
                    partner_id = RelatedModel.create(data)
                    ids = RelatedModel.name_search(name=value, operator='=')
                    True
            if ids:
                if len(ids) > 1:
                    warnings.append(ImportWarning(
                        _(u"Found multiple matches for field '%%(field)s' (%d matches)")
                        % (len(ids))))
                id, _name = ids[0]
        else:
            raise self._format_import_error(
                Exception,
                _(u"Unknown sub-field '%s'"),
                subfield
            )

        if id is None:
            raise self._format_import_error(
                ValueError,
                _(u"No matching record found for %(field_type)s '%(value)s' in field '%%(field)s'"),
                {'field_type': field_type, 'value': value},
                {'moreinfo': action})
        return id, field_type, warnings