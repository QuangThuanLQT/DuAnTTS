odoo.define('tts_partner_search_by_range.tree', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    var NewListView = require('search_by_date_range.tree');
    ListView.include({

        init: function (parent, action) {
            this.actionManager = parent;
            this.controller_url = action.context.url;
            this.report_model = action.context.model;
            // in case of a financial report, an id is defined in the action declaration
            this.report_id = action.context.id ? parseInt(action.context.id, 10) : undefined;
            this.given_context = {};
            if (action.context.context) {
                this.given_context = action.context.context;
            }
            this.given_context.from_report_id = action.context.from_report_id;
            this.given_context.from_report_model = action.context.from_report_model;
            this.given_context.force_account = action.context.force_account;
            this.given_context.active_id = action.context.active_id;
            this.odoo_context = action.context;
            return this._super.apply(this, arguments);
        },

        render_buttons: function ($node) {
            var self = this;
            $('.cl_search_by_range').addClass('hidden')
            this._super.apply(this, arguments);
            var l10n = _t.database.parameters;
            if (self.model == 'res.partner') {
                self.button_export = $(QWeb.render('partner_export_button', {}));
                self.button_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_partner_excel',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_partner_buttons_print_excel').length == 0) {
                    self.$buttons.append(self.button_export);
                }

            }

        },
    })
});