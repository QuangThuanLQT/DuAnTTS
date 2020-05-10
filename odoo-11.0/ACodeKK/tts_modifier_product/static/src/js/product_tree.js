odoo.define('tts_modifier_product.product_tree', function (require) {
    "use strict";

    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var _t = core._t;
    var QWeb = core.qweb;
    var FormView = require('web.FormView');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');

    ListView.include({
        do_search: function (domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            this.tgl_search()
            if (self.model == 'product.product' && self.$product_search_categ) {
                this.new_tgl_search()
            }
        },
        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);

            self.$buttons.find('.o_product_buttons_print_excel').remove();
            if (self.model == 'product.product') {
                self.$product_print = $(QWeb.render('product.buttons_print_excel', {}));

                self.$product_print.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/print_product_excel',
                        dataType: 'json',
                        data: {
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                self.$buttons.append(self.$product_print)

                self.$product_search_categ = $(QWeb.render('TTS.SearchProductCateg', {}));
                self.$clear_all = $(QWeb.render('SkyERP.ClearAll', {}))
                self.$product_search_categ.find('.tts_categ_name').on('change', function () {
                    self.new_tgl_search();
                });
                $('.cl_search_by_range').on('click', '.button_clear_all', function () {
                    self.clear_tgl_search();
                });
                // if ($('.cl_search_by_range').length > 0) {
                //     self.$clear_all.appendTo($('.cl_search_by_range'));
                // }
                if ($('.cl_search_by_range').length > 0) {
                    setTimeout(function () {
                        self.$product_search_categ.appendTo($('.cl_search_by_range'));
                    }, 500);
                    setTimeout(function () {
                        self.$clear_all.appendTo($('.cl_search_by_range'));
                    }, 1500);
                } else {
                    setTimeout(function () {
                        self.$product_search_categ.appendTo($('.cl_search_by_range'));
                    }, 500);
                    setTimeout(function () {
                        self.$clear_all.appendTo($('.cl_search_by_range'));
                    }, 1500);
                }
                new Model("product.product").call("get_categ_list", []).then(function (categ_ids) {
                    sbr_autocomplete(self.$product_search_categ.find('#input_categ_name')[0], categ_ids);
                });
            }
        },
        new_tgl_search: function () {
            var self = this;
            var categ_name = self.$product_search_categ.find('.tts_categ_name').val();
            var domain = []
            if (categ_name) {
                new Model('product.product').call('get_categ_name_search', [categ_name]).then(function (product_ids) {
                    domain.push(['id', 'in', product_ids]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                });
            }
            // else {
            //     self.clear_tgl_search()
            // }
        },
    });
});