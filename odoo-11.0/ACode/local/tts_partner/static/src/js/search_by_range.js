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
            console.log('run 2 tts');
            var l10n = _t.database.parameters;
            var datepickers_options = {
                pickTime: false,
                startDate: moment({y: 1900}),
                endDate: moment().add(200, "y"),
                calendarWeeks: true,
                icons: {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down'
                },
                language: moment.locale(),
                format: time.strftime_to_moment_format(l10n.date_format),
            }
            self.$buttons.find('.o_partner_buttons_print_excel').remove();
            if (self.model == 'res.partner') {

                self.button_export = $(QWeb.render('partner_export_button', {}));
                self.button_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_partner_excel',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.button_export)

                self.button_detail_export = $(QWeb.render('partner_export_button_detail', {}));
                self.button_detail_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_detail_partner_excel',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.button_detail_export)


                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "phone") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                if (sky_fields.length > 0) {
                    self.$search_partner_phone = $(QWeb.render('SkyERP.PartnerPhone', {'sky_fields': sky_fields}))
                    self.$search_partner_phone.find('.sky_partner_phone').on('change', function () {
                        self.tgl_search();
                    });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_search_by_range').length > 0) {
                        self.$search_partner_phone.appendTo($('.cl_search_by_range'));
                    } else {
                        setTimeout(function () {
                            self.$search_partner_phone.appendTo($('.cl_search_by_range'));
                            // self.$clear_all.appendTo($('.cl_search_by_range'));
                        }, 500);
                    }
                }

                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "user_id") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                // self.$clear_all = $(QWeb.render('SkyERP.ClearAllPartner', {}))
                $('.cl_search_by_range').on('click', '.button_clear_all', function () {
                    self.clear_tgl_search();
                });
                if (sky_fields.length > 0) {
                    self.$search_partner_user_id = $(QWeb.render('SkyERP.SearchPartnerUser', {'sky_fields': sky_fields}))
                    self.$search_partner_user_id.find('.sky_user_id').on('change', function () {
                        self.tgl_search();
                    });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_search_by_range').length > 0) {
                        self.$search_partner_user_id.appendTo($('.cl_search_by_range'));
                    } else {
                        setTimeout(function () {
                            self.$search_partner_user_id.appendTo($('.cl_search_by_range'));
                            // self.$clear_all.appendTo($('.cl_search_by_range'));
                        }, 500);
                    }
                }



                //     sky_fields = [];
                //     _.each(self.columns, function (value, key, list) {
                //         if (value.store && value.length > 1 || value.name === 'last_invoice_date_sub') {
                //             sky_fields.push([value.name, value.string]);
                //         }
                //     });
                //     if (sky_fields.length > 0) {
                //         self.$search_invoice_date = $(QWeb.render('SkyERP.Search_date', {'sky_fields': sky_fields}))
                //         self.$search_invoice_date.find('.sky_start_date').datetimepicker(datepickers_options);
                //         self.$search_invoice_date.find('.sky_end_date').datetimepicker(datepickers_options);
                //
                //         self.$search_invoice_date.find('.sky_start_date').on('change', function () {
                //             self.tgl_search();
                //         });
                //         self.$search_invoice_date.find('.sky_end_date').on('change', function () {
                //             self.tgl_search();
                //         });
                //         if ($('.cl_show_credit_debit').length > 0) {
                //             self.$search_invoice_date.appendTo($('.cl_show_credit_debit'));
                //         } else {
                //             setTimeout(function () {
                //                 self.$search_invoice_date.appendTo($('.cl_show_credit_debit'));
                //             }, 1000);
                //         }
                //     }
                //     sky_fields = [];
                //     _.each(self.columns, function (value, key, list) {
                //         if (value.store && value.length > 1 || value.name === 'create_date') {
                //             sky_fields.push([value.name, value.string]);
                //         }
                //     });
                //     if (sky_fields.length > 0) {
                //         self.$search_create_date = $(QWeb.render('SkyERP.Search_date', {'sky_fields': sky_fields}))
                //         self.$search_create_date.find('.sky_start_date').datetimepicker(datepickers_options);
                //         self.$search_create_date.find('.sky_end_date').datetimepicker(datepickers_options);
                //
                //         self.$search_create_date.find('.sky_start_date').on('change', function () {
                //             self.tgl_search();
                //         });
                //         self.$search_create_date.find('.sky_end_date').on('change', function () {
                //             self.tgl_search();
                //         });
                //         if ($('.cl_show_credit_debit').length > 0) {
                //             self.$search_create_date.appendTo($('.cl_show_credit_debit'));
                //         } else {
                //             setTimeout(function () {
                //                 self.$search_create_date.appendTo($('.cl_show_credit_debit'));
                //             }, 1000);
                //         }
                //     }

            }

        },

        tgl_search: function () {
            var self = this;
            var domain = [];
            if (self.$search_partner_user_id) {
                var user_id_name = self.$search_partner_user_id.find('.sky_user_id').val()
                if (user_id_name) {
                    domain.push(['user_id', 'like', user_id_name]);
                    var compound_domain = new data.CompoundDomain(self.last_domain || [], domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }

            if (self.$search_partner_phone) {
                var phone = self.$search_partner_phone.find('.sky_partner_phone').val()
                if (phone) {
                    domain.push(['phone', 'ilike', phone]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            this._super.apply(this, arguments);


        },
    })
});