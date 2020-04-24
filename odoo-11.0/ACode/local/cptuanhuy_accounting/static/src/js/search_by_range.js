odoo.define('cptuanhuy_accounting.tree', function (require) {
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
            console.log('cptuanhuy');
            if (self.actionManager.action && self.actionManager.action.xml_id && self.actionManager.action.xml_id == 'cptuanhuy_accounting.account_move_pnl_report_action'){
               if ($('.cl_show_credit_debit').length > 0) {
                         $('.cl_show_credit_debit').hide();

                    } else {
                        setTimeout(function () {
                             $('.cl_show_credit_debit').hide();
                        }, 1000);
                    }
                $('.cl_show_credit_debit').hide();
            }

            if (self.model == 'account.asset.asset' ) {

                self.asset_export_excel = $(QWeb.render('account_asset_export_excel', {}));
                self.asset_export_excel.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/account_asset_export_excel',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_asset_export_excel').length == 0) {
                    self.$buttons.append(self.asset_export_excel);
                }
            }
        },

        check_amkho: function () {
            var self = this;
            var domain = [], value, value_tmp;

            var end_date
            var field
            var start_date
            if (self.$search_button) {
                start_date = self.$search_button.find('.sky_start_date').val();
                end_date = self.$search_button.find('.sky_end_date').val();
                field = self.$search_button.find('.sky_select_field').val();
            }

            new Model('stock.move').call('get_stock_am_kho', [field, start_date, end_date]).then(function (stock_move_id_list) {
                $('.list_check_am_kho').val(JSON.stringify(stock_move_id_list));
                domain.push(['id', 'in', stock_move_id_list]);
                var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                self.dataset.domain = compound_domain.eval();
                return self.old_search(compound_domain, self.last_context, self.last_group_by);
            });
        },

        // load_list: function (data) {
        //     this._super(data);
        //     if (this.$buttons) {
        //         this.$buttons.find('.o_account-print-xlsx').off().click(this.proxy('action_print_excel'));
        //         console.log('Save & Close button method call...');
        //     }
        // },
        tgl_search: function () {
            var self = this;
            var domain = []
            if ($('.list_check_am_kho') && $('.list_check_am_kho').val() && $('.list_check_am_kho').val().length > 3) {
                var stock_move_id_list = JSON.parse($('.list_check_am_kho').val())
                domain.push(['id', 'in', stock_move_id_list]);
                var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                self.dataset.domain = compound_domain.eval();
                return self.old_search(compound_domain, self.last_context, self.last_group_by);
            }
            this._super.apply(this, arguments);
            if (self.model == 'account.move.line') {
                console.log('22');
                var domain_list = self.dataset.domain
                var partner_str, start_date, end_date;
                if (self.$search_customer) {
                    partner_str = self.$search_customer.find('.sky_customer_name').val()
                }
                if (self.$search_button) {
                    start_date = self.$search_button.find('.sky_start_date').val();
                    end_date = self.$search_button.find('.sky_end_date').val();
                }
                new Model("account.move.line").call("get_debit_credit_before", [domain_list, start_date, partner_str]).then(function (result) {
                    if ($('.sky_debit_number_ps').length != 0 && Array.isArray(result)){
                        $('.sky_debit_number').val(result[0]);
                        $('.sky_credit_number').val(result[1]);
                    }
                    // else {
                    //     setTimeout(function () {
                    //         $('.sky_debit_number').val(result[0]);
                    //         $('.sky_credit_number').val(result[1]);
                    //     }, 1000);
                    // }
                });

                new Model("account.move.line").call("get_debit_credit_current", [domain_list, start_date, end_date, partner_str]).then(function (result) {
                    if ($('.sky_debit_number_ps').length != 0 && Array.isArray(result)) {
                        $('.sky_debit_number_ps').val(result[0]);
                        $('.sky_credit_number_ps').val(result[1]);
                        $('.sky_debit_number_last').val(result[2]);
                        $('.sky_credit_number_last').val(result[3]);
                    }
                    // else {
                    //     setTimeout(function () {
                    //         $('.sky_debit_number_ps').val(result[0]);
                    //         $('.sky_credit_number_ps').val(result[1]);
                    //         $('.sky_debit_number_last').val(result[2]);
                    //         $('.sky_credit_number_last').val(result[3]);
                    //     }, 1000);
                    // }

                });
            }
            if (self.model == 'cong.no.phaithu') {
                var domain_list = self.dataset.domain
                var partner_str, start_date, end_date;
                if (self.$search_customer) {
                    partner_str = self.$search_customer.find('.sky_customer_name').val()
                }
                if (self.$search_button) {
                    start_date = self.$search_button.find('.sky_start_date').val();
                    end_date = self.$search_button.find('.sky_end_date').val();
                }
                new Model("account.move.line").call("get_debit_credit_before_131", [start_date, partner_str]).then(function (result) {
                    $('.sky_debit_number').val(result[0]);
                    $('.sky_credit_number').val(result[1]);
                    return true;
                });
                new Model("account.move.line").call("get_debit_credit_current_131", [domain_list, start_date, end_date, partner_str]).then(function (result) {
                    if ($('.sky_debit_number_ps').length != 0 && Array.isArray(result)) {
                        $('.sky_debit_number_ps').val(result[0]);
                        $('.sky_credit_number_ps').val(result[1]);
                        $('.sky_debit_number_last').val(result[2]);
                        $('.sky_credit_number_last').val(result[3]);
                    } else {
                        setTimeout(function () {
                            $('.sky_debit_number_ps').val(result[0]);
                            $('.sky_credit_number_ps').val(result[1]);
                            $('.sky_debit_number_last').val(result[2]);
                            $('.sky_credit_number_last').val(result[3]);
                        }, 1000);
                    }
                });
            }
            if (self.model == 'cong.no.phaitra') {
                var domain_list = self.dataset.domain
                var partner_str, start_date, end_date;
                if (self.$search_customer) {
                    partner_str = self.$search_customer.find('.sky_customer_name').val()
                }
                if (self.$search_button) {
                    start_date = self.$search_button.find('.sky_start_date').val();
                    end_date = self.$search_button.find('.sky_end_date').val();
                }
                new Model("account.move.line").call("get_debit_credit_before_331", [start_date, partner_str]).then(function (result) {
                    $('.sky_debit_number').val(result[0]);
                    $('.sky_credit_number').val(result[1]);
                    return true;
                });
                new Model("account.move.line").call("get_debit_credit_current_331", [domain_list, start_date, end_date, partner_str]).then(function (result) {
                    if ($('.sky_debit_number_ps').length != 0 && Array.isArray(result)) {
                        $('.sky_debit_number_ps').val(result[0]);
                        $('.sky_credit_number_ps').val(result[1]);
                        $('.sky_debit_number_last').val(result[2]);
                        $('.sky_credit_number_last').val(result[3]);
                    } else {
                        setTimeout(function () {
                            $('.sky_debit_number_ps').val(result[0]);
                            $('.sky_credit_number_ps').val(result[1]);
                            $('.sky_debit_number_last').val(result[2]);
                            $('.sky_credit_number_last').val(result[3]);
                        }, 1000);
                    }
                });
            }
            if ($('.list_check_am_kho') && $('.list_check_am_kho').val() && $('.list_check_am_kho').val().length > 3) {
                var stock_move_id_list = JSON.parse($('.list_check_am_kho').val())
                domain.push(['id', 'in', stock_move_id_list]);
                var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                self.dataset.domain = compound_domain.eval();
                return self.old_search(compound_domain, self.last_context, self.last_group_by);
            }
        },
        action_print_excel: function () {
            console.log('click');
        }
    })
});