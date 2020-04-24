odoo.define('tts_sale_gross_proifit.tree', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

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
            this._super.apply(this, arguments);
            self.$buttons.find('.o_sale_gross_proifit_buttons_print_excel').remove();
            if (self.model == 'account.invoice.line') {

                self.button_export = $(QWeb.render('sale_gross_proifit_buttons_export', {}));
                self.button_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_sale_gross_proifit_excel',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.button_export)
            }
            if (self.model == 'account.invoice') {
                console.log('hide origin')
                setTimeout(function () {
                    if ($('.sky_select_origin_field') &&  $('.sky_select_origin_field')[0]) {
                        $('.sky_select_origin_field')[0][0].value = 'origin'
                        $('.sky_select_origin_field')[0][0].text = 'Source Document'
                        }
                }, 1200);

                if (self.ViewManager.action.xml_id == 'account.action_invoice_tree2') {
                    if ($('.o_vendor_bill_export_overview').length == 0) {
                        self.account_vendor_bill_export_overview = $(QWeb.render('account_vendor_bill_export_overview', {}));
                        self.account_vendor_bill_export_overview.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/print_vendor_bill_export_overview',
                                dataType: 'json',
                                data: {
                                    domain: JSON.stringify(domain),
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.account_vendor_bill_export_overview)
                    }

                    if ($('.o_vendor_bill_export_detail').length == 0) {
                        self.account_vendor_bill_export_detail = $(QWeb.render('account_vendor_bill_export_detail', {}));
                        self.account_vendor_bill_export_detail.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/print_vendor_bill_export_detail',
                                dataType: 'json',
                                data: {
                                    domain: JSON.stringify(domain),
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.account_vendor_bill_export_detail)
                    }

                }
                else {
                    if ($('.o_invoice_export_overview').length == 0) {
                        self.button_export_overview = $(QWeb.render('account_invoice_export_overview', {}));
                        self.button_export_overview.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/print_invoice_export_overview',
                                dataType: 'json',
                                data: {
                                    domain: JSON.stringify(domain),
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.button_export_overview)
                    }

                    if ($('.o_invoice_export_detail').length == 0) {
                        self.button_export_detail = $(QWeb.render('account_invoice_export_detail', {}));
                        self.button_export_detail.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/print_invoice_export_detail',
                                dataType: 'json',
                                data: {
                                    domain: JSON.stringify(domain),
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.button_export_detail)
                    }
                }
            }

        },
    });
});