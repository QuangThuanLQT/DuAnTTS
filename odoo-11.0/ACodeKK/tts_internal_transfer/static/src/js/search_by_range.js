odoo.define('tts_internal_transfer.tree', function (require) {
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
            console.log('run 323 tts');
            if (self.model == 'stock.picking') {
                if (self.actionManager && self.actionManager.action && self.actionManager.action.xml_id == 'tts_internal_transfer.receipt_history_action') {
                    if ($('.o_receipt_history_print_excel').length == 0) {
                        self.receipt_history_buttons_export = $(QWeb.render('receipt_history_buttons_export', {}));
                        self.receipt_history_buttons_export.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/receipt_history_export_data',
                                dataType: 'json',
                                data: {
                                     domain: JSON.stringify(domain)
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.receipt_history_buttons_export)
                    }
                }
                else {
                    if (self.actionManager.action.xml_id != 'prinizi_picking_print_history_list.picking_print_history_action') {
                        self.button_export_picking_receipt = $(QWeb.render('picking_receipt_buttons_export', {}));
                        self.button_export_picking_receipt.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/picking_receipt_export_data',
                                dataType: 'json',
                                data: {
                                    domain: JSON.stringify(domain)
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.button_export_picking_receipt)


                        self.button_export_picking_delivery = $(QWeb.render('picking_delivery_buttons_export', {}));
                        self.button_export_picking_delivery.click(function () {
                            var domain = self.dataset.domain;
                            session.get_file({
                                url: '/picking_delivery_export_data',
                                dataType: 'json',
                                data: {
                                    'action': self.ViewManager.action.xml_id,
                                    domain: JSON.stringify(domain)
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                        });
                        self.$buttons.append(self.button_export_picking_delivery)
                    }

                    self.$clear_all = $(QWeb.render('SkyERP.ClearAll', {}))
                    self.$picking_source_location = $(QWeb.render('TTS.SearchSourceLocation', {}));
                    self.$picking_source_location.find('.tts_source_location_name').on('change', function () {
                        self.tgl_search();
                    });
                    if ($('.cl_show_credit_debit').length > 0) {
                        setTimeout(function () {
                            self.$picking_source_location.appendTo($('.cl_show_credit_debit'));
                        }, 500);
                    } else {
                        setTimeout(function () {
                            self.$picking_source_location.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }
                    new Model("stock.picking").call("get_location_list", []).then(function (categ_ids) {
                        sbr_autocomplete(self.$picking_source_location.find('#input_source_location_name')[0], categ_ids);
                    });


                    self.$picking_dest_location = $(QWeb.render('TTS.SearchDestLocation', {}));
                    self.$picking_dest_location.find('.tts_dest_location_name').on('change', function () {
                        self.tgl_search();
                    });

                    if ($('.cl_show_credit_debit').length > 0) {
                        setTimeout(function () {
                            self.$picking_dest_location.appendTo($('.cl_show_credit_debit'));
                        }, 500);
                    } else {
                        setTimeout(function () {
                            self.$picking_dest_location.appendTo($('.cl_show_credit_debit'));
                        }, 1000);
                    }

                    new Model("stock.picking").call("get_location_list", []).then(function (categ_ids) {
                        sbr_autocomplete(self.$picking_dest_location.find('#input_dest_location_name')[0], categ_ids);
                    });

                    if (self.last_context && self.last_context.active_model == 'stock.picking.type') {
                        active_id = self.last_context.active_id
                        new Model("stock.picking").call("get_state_list", [active_id]).then(function (state_ids) {
                            if (state_ids[0].length > 0) {
                                self.$search_state_pick = $(QWeb.render('TTS.SearchStatePick', {
                                    'sky_fields': state_ids[0],
                                    'state_data': state_ids[1]
                                }))
                                var state = self.$search_state_pick.find('.tts_select_state_picking_field').val()
                                if ((state == 'state_pack' || state == 'internal_transfer_state' || state == 'receipt') && self.$picking_dest_location && self.$picking_source_location) {
                                    self.$picking_dest_location.addClass('hidden')
                                    self.$picking_source_location.addClass('hidden')
                                }
                                else {
                                    self.$picking_dest_location.removeClass('hidden')
                                    self.$picking_source_location.removeClass('hidden')
                                }
                                self.$search_state_pick.find('.search_picking_state').on('change', function () {
                                    self.tgl_search();
                                });
                                // // self.$search_customer.appendTo($('.cl_search_by_range'));
                                if ($('.cl_show_credit_debit').length > 0) {
                                    self.$search_state_pick.appendTo($('.cl_show_credit_debit'));
                                } else {
                                    setTimeout(function () {
                                        self.$search_state_pick.appendTo($('.cl_show_credit_debit'));
                                    }, 1000);
                                }
                            }
                        });
                    }
                }


                if (self.ViewManager.action.xml_id == 'tts_internal_transfer.exported_history_action') {
                    if (self.$picking_dest_location) {
                        self.$picking_dest_location.addClass('hidden')
                    }
                    if (self.$picking_source_location) {
                        self.$picking_source_location.addClass('hidden')
                    }
                    if (self.button_export_picking_receipt) {
                        self.button_export_picking_receipt.addClass('hidden')
                    }
                    if (self.button_export_picking_delivery) {
                        self.button_export_picking_delivery.addClass('hidden')
                    }

                    self.picking_export_overview = $(QWeb.render('button_picking_export_overview', {}));
                    self.picking_export_overview.click(function () {
                        var domain = self.dataset.domain;
                        session.get_file({
                            url: '/exported_picking_overview',
                            dataType: 'json',
                            data: {
                                domain: JSON.stringify(domain),
                            },
                            complete: framework.unblockUI,
                            error: crash_manager.rpc_error.bind(crash_manager),
                        });
                    });
                    if (self.$buttons[0].getElementsByClassName('o_picking_export_overview').length == 0) {
                        self.$buttons.append(self.picking_export_overview);
                    }
                }
            }
            if (self.model == 'account.invoice') {
                if ($('.tts_select_state_picking_field').length == 0) {
                    new Model("stock.picking").call("get_inv_state_list", []).then(function (state_ids) {
                        if (state_ids[0].length > 0) {
                            self.$search_state_pick = $(QWeb.render('TTS.SearchStatePick', {
                                'sky_fields': state_ids[0],
                                'state_data': state_ids[1]
                            }))
                            self.$search_state_pick.find('.search_picking_state').on('change', function () {
                                self.tgl_search();
                            });
                            // // self.$search_customer.appendTo($('.cl_search_by_range'));
                            if ($('.cl_show_credit_debit').length > 0) {
                                self.$search_state_pick.appendTo($('.cl_show_credit_debit'));
                            } else {
                                setTimeout(function () {
                                    self.$search_state_pick.appendTo($('.cl_show_credit_debit'));
                                }, 1000);
                            }
                        }
                    });
                }
            }

            if (self.model == 'income.inventory') {
                if (self.ViewManager.action.xml_id == 'tts_internal_transfer.income_inventory_action') {
                    if (self.$picking_dest_location) {
                        self.$picking_dest_location.addClass('hidden')
                    }
                    if (self.$picking_source_location) {
                        self.$picking_source_location.addClass('hidden')
                    }
                    if (self.button_export_picking_receipt) {
                        self.button_export_picking_receipt.addClass('hidden')
                    }
                    if (self.button_export_picking_delivery) {
                        self.button_export_picking_delivery.addClass('hidden')
                    }

                    sky_fields = [];
                    _.each(self.columns, function (value, key, list) {
                        if (value.string && value.string.length > 1 && value.name === "user_delivery_id") {
                            sky_fields.push([value.name, value.string]);
                        }
                    });
                    if (sky_fields.length > 0) {
                        self.delivery_user = $(QWeb.render('TTS.DeliveryUser', {'sky_fields': sky_fields}))
                        self.delivery_user.find('.tts_delivery_user').on('change', function () {
                            self.tgl_search();
                        });
                        // self.$search_customer.appendTo($('.cl_search_by_range'));
                        if ($('.cl_show_credit_debit').length > 0) {
                            self.delivery_user.appendTo($('.cl_show_credit_debit'));
                        } else {
                            setTimeout(function () {
                                self.delivery_user.appendTo($('.cl_show_credit_debit'));
                            }, 1000);
                        }
                    }

                    self.picking_export_overview = $(QWeb.render('button_picking_export_overview', {}));
                    self.picking_export_overview.click(function () {
                        var domain = self.dataset.domain;
                        session.get_file({
                            url: '/picking_export_overview',
                            dataType: 'json',
                            data: {
                                domain: JSON.stringify(domain),
                            },
                            complete: framework.unblockUI,
                            error: crash_manager.rpc_error.bind(crash_manager),
                        });
                    });
                    if (self.$buttons[0].getElementsByClassName('o_picking_export_overview').length == 0) {
                        self.$buttons.append(self.picking_export_overview);
                    }
                }
            }
        },

        clear_tgl_search: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (self.$search_state_pick) {
                var state_pick = self.$search_state_pick.find('.search_picking_state')
                state_list = [];
                _.each(state_pick, function (value) {
                    if (value.checked) {
                        value.checked = false
                    }
                });
            }
        },

        tgl_search: function () {
            console.log('run 323 tts');
            var self = this;
            var domain = self.dataset.domain;
            this._super.apply(this, arguments);

            if (self.$picking_source_location) {
                var source_location = self.$picking_source_location.find('.tts_source_location_name').val();
                if (source_location) {
                    new Model('stock.picking').call('get_picking_search', [source_location, 'source']).then(function (picking_ids) {
                        domain.push(['id', 'in', picking_ids]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }

            }

            if (self.$search_state_pick) {
                var state_pick = self.$search_state_pick.find('.search_picking_state')
                var state = self.$search_state_pick.find('.tts_select_state_picking_field').val()
                state_list = [];
                _.each(state_pick, function (value) {
                    if (value.checked) {
                        state_list.push(value.value)
                    }
                });
                if (state_list) {
                    var new_domain = []
                    var check_domain = false;
                    for (var i = domain.length - 1; i >= 0; i--) {
                        if (domain[i][0] != state) {
                            new_domain.push(domain[i])
                        }
                        else {
                            check_domain = true;
                        }
                    }
                    domain = new_domain
                    if (state_list.length != 0) {
                        domain.push([state, 'in', state_list]);
                    }
                    if (check_domain || state_list.length != 0) {
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    }
                }
            }

            if (self.$picking_dest_location) {
                var dest_location = self.$picking_dest_location.find('.tts_dest_location_name').val();
                if (dest_location) {
                    new Model('stock.picking').call('get_picking_search', [dest_location, 'dest']).then(function (picking_ids) {
                        domain.push(['id', 'in', picking_ids]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }

            if (self.delivery_user) {
                var delivery_user = self.delivery_user.find('.tts_delivery_user').val();
                if (delivery_user) {
                    new Model('income.inventory').call('search_delivery_user', [delivery_user]).then(function (picking_ids) {
                        domain.push(['user_delivery_id', 'in', picking_ids]);
                        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                        self.dataset.domain = compound_domain.eval();
                        return self.old_search(compound_domain, self.last_context, self.last_group_by);
                    });
                }
            }

        },
    });

    FormView.include({
        load_record: function(record) {
            var self = this;
            self._super.apply(self, arguments);
            if (self.model === 'stock.picking'){
                setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Phiếu Hoạt Động Kho')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu Nhập Kho')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu Hoạt Động Kho A4')").addClass('hidden');
                    }, 400)
                if (this.get_fields_values().check_is_pick === true){
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Phiếu giao hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu nhận hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu kiểm hàng')").addClass('hidden');
                    }, 400)
                }
                if (this.get_fields_values().check_is_pack === true){
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Phiếu lấy hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu nhận hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu kiểm hàng')").addClass('hidden');
                    }, 400)
                }
                if (this.get_fields_values().check_is_delivery === true){
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Phiếu lấy hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu nhận hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu kiểm hàng')").addClass('hidden');
                    }, 400)
                }
                if (this.get_fields_values().is_internal_transfer === true){
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Phiếu lấy hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu giao hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu nhận hàng')").addClass('hidden');
                    }, 400)
                }
                if (this.get_fields_values().picking_type_code == 'incoming'){
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Phiếu lấy hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu giao hàng')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Phiếu kiểm hàng')").addClass('hidden');
                    }, 400)
                }
                if (this.get_fields_values().is_internal_transfer === false) {
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Xuất file')").addClass('hidden');
                    }, 400)
                }
            }
        }
      });
});