odoo.define('inventory_search_by_range.tree', function (require) {
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
            if (self.model == 'stock.inventory') {
                self.button_export_over = $(QWeb.render('inventory_export_over', {}));
                self.button_export_over.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/export_overview',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_button_overview').length == 0) {
                    self.$buttons.append(self.button_export_over);
                }


                self.button_export_detail = $(QWeb.render('inventory_export_detail', {}));
                self.button_export_detail.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/export_detail',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_button_detail').length == 0) {
                    self.$buttons.append(self.button_export_detail);
                }

                sky_fields = [];
                _.each(self.columns, function (value, key, list) {
                    if (value.string && value.string.length > 1 && value.name === "state") {
                        sky_fields.push([value.name, value.string]);
                    }
                });
                if (sky_fields.length > 0) {
                    self.$state_inventory = $(QWeb.render('SkyERP.InventoryState', {'sky_fields': sky_fields}))
                    self.$state_inventory.find('.sky_state').on('change', function () {
                        self.tgl_search();
                    });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.cl_show_credit_debit').length > 0) {
                        self.$state_inventory.appendTo($('.cl_search_by_range'));
                    } else {
                        setTimeout(function () {
                            self.$state_inventory.appendTo($('.cl_search_by_range'));
                        }, 1000);
                    }
                }

            }
            if (self.model == 'product.product' && self.ViewManager.action.xml_id == 'tts_modifier_inventory.not_sellable_product_action') {
                self.button_export = $(QWeb.render('not_sellable_product_export', {}));
                self.button_export.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/export_not_sellable_product',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_button_not_sellable_product').length == 0) {
                    self.$buttons.append(self.button_export);
                }
                self.$buttons.find('.o_product_buttons_print_excel').addClass('hidden');// Ẩn button Xuất file
            }

        },

        tgl_search: function () {
            var self = this;
            var domain = self.dataset.domain;

            if (self.$state_inventory) {
                var state = self.$state_inventory.find('.sky_state').val()
                if (state) {
                    domain.push(['state', '=', state]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            this._super.apply(this, arguments);

        },
    });

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);

            if (self.model == 'stock.picking') {
                console.log('hide picking ------------')
                if (self.get_fields_values().state == 'done') {
                    setTimeout(function () {
                        $(".o_form_button_edit").addClass('hidden');
                    }, 600)
                }
            }
        }
    });


});