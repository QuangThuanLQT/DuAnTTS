odoo.define('tuanhuy_account_reports_search_by_date_range.tree', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager');
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
            this._super.apply(this, arguments);

            if (this.$buttons) {
                this.$buttons.find('.o_account-print-xls').click(this.proxy('action_print_excel'));
            }
            console.log('run 2');

            if (self.model == 'stock.move' && self.ViewManager.action.xml_id == 'tuanhuy_stock.stock_picking_line_action') {
                self.$check_amkho = $(QWeb.render('SkyERP.Checkamkho', {}))
                $('.cl_search_by_range').on('click', '.button_check_am_kho', function () {
                    self.check_amkho();
                });
                if ($('.cl_search_by_range').length > 0) {
                    self.$check_amkho.appendTo($('.cl_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$check_amkho.appendTo($('.cl_search_by_range'));
                        $('.cl_search_by_range').on('click', '.button_check_am_kho', function () {
                            self.check_amkho();
                        });
                    }, 1000);
                }
            }

            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                console.log('aml_inherit');
                if (value.string && value.string.length > 1 && value.name === "debit") {
                    sky_fields.push([value.name, value.string]);
                }
            });
            var code = ['151', '152', '153', '154', '155', '156', '157', '158', '211' ];
            if (sky_fields.length > 0 && self.model == 'account.move.line') {
                var check = false;
                var start_date;
                var domain = self.dataset.domain;
                for (var list in domain) {
                    for (var value in domain[list]) {
                        if (domain[list][value] == 'account_id.code' || domain[list][value] == 'account_doi_ung_1121') {
                            check = true
                        }
                        else if (domain[list][value] == 'account_id'){
                            debugger;
                            check = true;
                        }
                    }
                }
                if (check == true) {
                    self.$before_debit_number = $(QWeb.render('SkyERP.BeforeDebitNumber', {'sky_fields': sky_fields}))

                    // self.$search_number_vourcher.find('.sky_number_vourcher').on('change', function() {
                    //     self.tgl_search();
                    // });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$before_debit_number.appendTo($('.cl_show_credit_debit'));

                    } else {
                        setTimeout(function () {
                            self.$before_debit_number.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }
                }

            }


            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1 && value.name === "debit") {
                    sky_fields.push([value.name, value.string]);
                }
            });

            if (sky_fields.length > 0 && self.model == 'account.move.line') {
                console.log('aml_inherit_1');
                var check = false;
                var show_print_detail = false;
                var start_date;
                var domain = self.dataset.domain;

                for (var list in domain) {
                    for (var value in domain[list]) {
                        if (domain[list][value] == 'account_id.code' || domain[list][value] == 'account_doi_ung_1121') {
                            check = true
                            var i = parseInt(value) + 2;
                            if (domain[list][i] == '131' || domain[list][i] == '331' || domain[list][i] in code) {
                                show_print_detail = true
                            }
                        }
                        else if (domain[list][value] == 'account_id'){
                            debugger;
                            check = true;
                            show_print_detail = true;
                        }
                    }
                }
                if (check == true) {
                    console.log('sky_fields', sky_fields);
                    self.$ps_debit_credit = $(QWeb.render('SkyERP.PSDebitCredit', {'sky_fields': sky_fields}));
                    self.$last_debit_credit = $(QWeb.render('SkyERP.LastDebitCredit', {'sky_fields': sky_fields}));
                    if (show_print_detail == false) {
                        self.$button_print = $(QWeb.render('SkyERP.buttons_print', {'sky_fields': sky_fields}));
                        self.$button_print.click(function () {
                            var domain_list = self.dataset.domain;
                            var account_code = 'False';
                            var partner_str = false;
                            var start_date = false;
                            var end_date = false;
                            var account_id = false;
                            for (var list in domain_list) {
                                for (var value in domain_list[list]) {
                                    if (domain_list[list][value] == 'account_id.code' || domain_list[list][value] == 'account_doi_ung_1121') {
                                        var i = parseInt(value) + 2
                                        account_code = domain_list[list][i]
                                        if (domain[list][value] == 'account_doi_ung_1121') {
                                            account_code = '1121'
                                        }
                                    }
                                    else if (domain_list[list][value] == 'account_id') {
                                        var i = parseInt(value) + 2
                                        account_id = domain_list[list][i]
                                    }
                                }
                            }
                            if (self.$search_customer) {
                                partner_str = self.$search_customer.find('.sky_customer_name').val()
                            }
                            if (self.$search_button) {
                                start_date = self.$search_button.find('.sky_start_date').val();
                                end_date = self.$search_button.find('.sky_end_date').val();
                            }

                            framework.blockUI();
                            var nodk = $('.sky_debit_number').val() || 0;
                            var codk = $('.sky_credit_number').val() || 0;
                            var psno = $('.sky_debit_number_ps').val() || 0;
                            var psco = $('.sky_credit_number_ps').val() || 0;
                            var nock = $('.sky_debit_number_last').val() || 0;
                            var cock = $('.sky_credit_number_last').val() || 0;
                            new Model('account.move.line').call('get_account_xlsx',[domain_list, nodk, codk, psno, psco, nock, cock, self.dataset.context]).then(function (result) {
                                session.get_file({
                                    url: result,
                                    dataType: 'json',
                                    data: {
                                    },
                                    complete: framework.unblockUI,
                                    error: crash_manager.rpc_error.bind(crash_manager),
                                });
                                });
                            // session.get_file({
                            //     url: '/print_account_report_excel',
                            //     dataType: 'json',
                            //     data: {
                            //         code: account_code,
                            //         account_id: account_id,
                            //         partner_str: partner_str,
                            //         start_date: start_date,
                            //         end_date: end_date
                            //     },
                            //     complete: framework.unblockUI,
                            //     error: crash_manager.rpc_error.bind(crash_manager),
                            // });
                        });
                    } else {
                        self.$button_print_detail = $(QWeb.render('SkyERP.Account_131', {'sky_fields': sky_fields}));
                        self.$button_print_detail.click(function () {
                            var domain_list = self.dataset.domain;
                            var account_code = 'False';
                            var partner_str = false;
                            var start_date = false;
                            var end_date = false;
                            var account_id = false;
                            for (var list in domain_list) {
                                for (var value in domain_list[list]) {
                                    if (domain_list[list][value] == 'account_id.code') {
                                        var i = parseInt(value) + 2;
                                        account_code = domain_list[list][i]
                                    }
                                    else if (domain_list[list][value] == 'account_id') {
                                        var i = parseInt(value) + 2;
                                        account_id = domain_list[list][i];
                                        debugger;
                                        var nodk = $('.sky_debit_number').val() || 0;
                                        var codk = $('.sky_credit_number').val() || 0;
                                        var psno = $('.sky_debit_number_ps').val() || 0;
                                        var psco = $('.sky_credit_number_ps').val() || 0;
                                        var nock = $('.sky_debit_number_last').val() || 0;
                                        var cock = $('.sky_credit_number_last').val() || 0;
                                        new Model('account.move.line').call('print_phat_sinh_excel',[domain_list, nodk, codk, psno, psco, nock, cock]).then(function (result) {
                                            session.get_file({
                                                url: result,
                                                dataType: 'json',
                                                data: {
                                                },
                                                complete: framework.unblockUI,
                                                error: crash_manager.rpc_error.bind(crash_manager),
                                            });
                                            })

                                    }
                                }
                            }
                            if (!account_id) {
                                if (self.$search_customer) {
                                partner_str = self.$search_customer.find('.sky_customer_name').val()
                                }
                                if (self.$search_button) {
                                    start_date = self.$search_button.find('.sky_start_date').val();
                                    end_date = self.$search_button.find('.sky_end_date').val();
                                }

                                framework.blockUI();
                                session.get_file({
                                    url: '/print_account_detail_excel',
                                    dataType: 'json',
                                    data: {
                                        code: account_code,
                                        account_id: account_id,
                                        partner_str: partner_str,
                                        start_date: start_date,
                                        end_date: end_date
                                    },
                                    complete: framework.unblockUI,
                                    error: crash_manager.rpc_error.bind(crash_manager),
                                });
                            }

                        });
                    }

                    self.tgl_search();

                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$ps_debit_credit.appendTo($('.cl_show_credit_debit'));
                        self.$last_debit_credit.appendTo($('.cl_show_credit_debit'));
                        if (show_print_detail == false) {
                            self.$button_print.appendTo($('.cl_show_credit_debit'));
                        } else {
                            self.$button_print_detail.appendTo($('.cl_show_credit_debit'));
                        }


                    } else {
                        setTimeout(function () {
                            self.$ps_debit_credit.appendTo($('.cl_show_credit_debit'));
                            self.$last_debit_credit.appendTo($('.cl_show_credit_debit'));
                            if (show_print_detail == false) {
                                self.$button_print.appendTo($('.cl_show_credit_debit'));
                            } else {
                                self.$button_print_detail.appendTo($('.cl_show_credit_debit'));
                            }
                        }, 1000);
                    }
                }
            }


            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1 && value.name === "debit") {
                    sky_fields.push([value.name, value.string]);
                }
            });
            if (sky_fields.length > 0 && self.model == 'cong.no.phaithu') {
                console.log('aml_inherit_1');
                var check = true;
                if (check == true) {
                    console.log('sky_fields', sky_fields);
                    self.$before_debit_number = $(QWeb.render('SkyERP.BeforeDebitNumber', {'sky_fields': sky_fields}));
                    self.$ps_debit_credit = $(QWeb.render('SkyERP.PSDebitCredit', {'sky_fields': sky_fields}));
                    self.$last_debit_credit = $(QWeb.render('SkyERP.LastDebitCredit', {'sky_fields': sky_fields}));
                    self.$last_debit_credit = $(QWeb.render('SkyERP.LastDebitCredit', {'sky_fields': sky_fields}));
                    self.$button_print_131 = $(QWeb.render('SkyERP.Account_131', {'sky_fields': sky_fields}));
                    self.$button_print_131.click(function () {
                        var domain_list = self.dataset.domain;
                        var account_code = '131';
                        var partner_str = false;
                        var start_date = false;
                        var end_date = false;
                        if (self.$search_customer) {
                            partner_str = self.$search_customer.find('.sky_customer_name').val()
                        }
                        if (self.$search_button) {
                            start_date = self.$search_button.find('.sky_start_date').val();
                            end_date = self.$search_button.find('.sky_end_date').val();
                        }

                        framework.blockUI();
                        if (partner_str) {
                            session.get_file({
                                url: '/print_account_detail_excel',
                                dataType: 'json',
                                data: {
                                    code: account_code,
                                    partner_str: partner_str,
                                    start_date: start_date,
                                    end_date: end_date
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        }
                        else {
                            session.get_file({
                                url: '/print_account_tong_hop_excel',
                                dataType: 'json',
                                data: {
                                    code: account_code,
                                    start_date: start_date,
                                    end_date: end_date
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        }

                    });

                    // self.$search_number_vourcher.find('.sky_number_vourcher').on('change', function() {
                    self.tgl_search();
                    // });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$before_debit_number.appendTo($('.cl_show_credit_debit'));
                        self.$ps_debit_credit.appendTo($('.cl_show_credit_debit'));
                        self.$last_debit_credit.appendTo($('.cl_show_credit_debit'));
                        self.$button_print_131.appendTo($('.cl_show_credit_debit'));
                    } else {
                        setTimeout(function () {
                            self.$before_debit_number.appendTo($('.cl_show_credit_debit'));
                            self.$ps_debit_credit.appendTo($('.cl_show_credit_debit'));
                            self.$last_debit_credit.appendTo($('.cl_show_credit_debit'));
                            self.$button_print_131.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }
                }

            }

            sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.string && value.string.length > 1 && value.name === "debit") {
                    sky_fields.push([value.name, value.string]);
                }
            });
            if (sky_fields.length > 0 && self.model == 'cong.no.phaitra') {
                console.log('aml_inherit_1');
                var check = true;
                if (check == true) {
                    console.log('sky_fields', sky_fields);
                    self.$before_debit_number = $(QWeb.render('SkyERP.BeforeDebitNumber', {'sky_fields': sky_fields}))
                    self.$ps_debit_credit = $(QWeb.render('SkyERP.PSDebitCredit', {'sky_fields': sky_fields}))
                    self.$last_debit_credit = $(QWeb.render('SkyERP.LastDebitCredit', {'sky_fields': sky_fields}))
                    self.$button_print_331 = $(QWeb.render('SkyERP.Account_331', {'sky_fields': sky_fields}));
                    self.$button_print_331.click(function () {
                        var domain_list = self.dataset.domain;
                        var account_code = '331';
                        var partner_str = false;
                        var start_date = false;
                        var end_date = false;
                        if (self.$search_customer) {
                            partner_str = self.$search_customer.find('.sky_customer_name').val()
                        }
                        if (self.$search_button) {
                            start_date = self.$search_button.find('.sky_start_date').val();
                            end_date = self.$search_button.find('.sky_end_date').val();
                        }

                        framework.blockUI();
                        if (partner_str) {
                            session.get_file({
                                url: '/print_account_detail_excel',
                                dataType: 'json',
                                data: {
                                    code: account_code,
                                    partner_str: partner_str,
                                    start_date: start_date,
                                    end_date: end_date
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        }

                        else {
                            session.get_file({
                                url: '/print_account_tong_hop_excel',
                                dataType: 'json',
                                data: {
                                    code: account_code,
                                    start_date: start_date,
                                    end_date: end_date
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        }
                    });
                    // self.$search_number_vourcher.find('.sky_number_vourcher').on('change', function() {
                    self.tgl_search();
                    // });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$before_debit_number.appendTo($('.cl_show_credit_debit'));
                        self.$ps_debit_credit.appendTo($('.cl_show_credit_debit'));
                        self.$last_debit_credit.appendTo($('.cl_show_credit_debit'));
                        self.$button_print_331.appendTo($('.cl_show_credit_debit'));
                    } else {
                        setTimeout(function () {
                            self.$before_debit_number.appendTo($('.cl_show_credit_debit'));
                            self.$ps_debit_credit.appendTo($('.cl_show_credit_debit'));
                            self.$last_debit_credit.appendTo($('.cl_show_credit_debit'));
                            self.$button_print_331.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }
                }

            }

            if (sky_fields.length > 0 && self.model == 'account.move.line') {
                console.log('profit_loss1');
                debugger;
                var check = true;
                if (check == true && ["sale.order", "product.product", "product.template"].includes(self.odoo_context.active_model)) {;
                    self.profit_loss = $(QWeb.render('SkyERP.ProfitLossPercent', {'sky_fields': sky_fields}));
                    self.$button_print = $(QWeb.render('SkyERP.buttons_print', {'sky_fields': sky_fields}));
                    self.$button_print.click(function () {
                        var domain_list = self.dataset.domain;
                        var start_date = false;
                        var end_date = false;
                        if (self.$search_button) {
                            start_date = self.$search_button.find('.sky_start_date').val();
                            end_date = self.$search_button.find('.sky_end_date').val();
                        }
                        framework.blockUI();
                        self.dataset.read_ids(self.dataset.ids).done(function(records) {
                            debugger;
                        new Model('account.move.line').call('print_pnl_excel',[domain_list]).then(function (result) {
                            debugger;
                        session.get_file({
                            url: result,
                            dataType: 'json',
                            data: {
                            },
                            complete: framework.unblockUI,
                            error: crash_manager.rpc_error.bind(crash_manager),
                        });
                        });
                        });
                    });
                    self.tgl_search();
                    if ($('.cl_search_by_range').length > 0) {

                        self.profit_loss.appendTo($('.cl_search_by_range'));
                        self.$button_print.appendTo($('.cl_search_by_range'));
                    } else {
                        setTimeout(function () {
                            self.profit_loss.appendTo($('.cl_search_by_range'));
                            self.$button_print.appendTo($('.cl_search_by_range'));
                        }, 1000);
                    }
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
                new Model("account.move.line").call("get_debit_credit_before", [domain_list, start_date, partner_str, self.dataset.context]).then(function (result) {
                    if ($('.sky_debit_number_ps').length != 0 && Array.isArray(result)){
                        $('.sky_debit_number').val(result[0]);
                        $('.sky_credit_number').val(result[1]);
                    }
                    else if (Array.isArray(result)) {
                        setTimeout(function () {
                            $('.sky_debit_number').val(result[0]);
                            $('.sky_credit_number').val(result[1]);
                        }, 1000);
                    }
                });

                new Model("account.move.line").call("get_debit_credit_current", [domain_list, start_date, end_date, partner_str, self.dataset.context]).then(function (result) {
                    if ($('.sky_debit_number_ps').length != 0 && Array.isArray(result)) {
                        $('.sky_debit_number_ps').val(result[0]);
                        $('.sky_credit_number_ps').val(result[1]);
                        $('.sky_debit_number_last').val(result[2]);
                        $('.sky_credit_number_last').val(result[3]);
                    }
                    else if (Array.isArray(result)){
                        setTimeout(function () {
                            $('.sky_debit_number_ps').val(result[0]);
                            $('.sky_credit_number_ps').val(result[1]);
                            $('.sky_debit_number_last').val(result[2]);
                            $('.sky_credit_number_last').val(result[3]);
                        }, 1000);
                    }

                });
                if (self.odoo_context.active_model == 'sale.order'){
                    new Model("account.move.line").call("compute_profit_percent", [domain_list, start_date, end_date, partner_str, self.odoo_context]).then(function (result) {
                    if ($('.sky_profit_loss').length != 0 && result != undefined) {
                        $('.sky_profit_loss').val(result.toFixed(2) + ' %');
                    }
                    else {
                        $('.sky_profit_loss').val('');
                    }

                });
                }

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
    });
});