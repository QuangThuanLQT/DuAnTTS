odoo.define('vieterp_customer.product_tree', function (require) {
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

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            $('.pr_search_by_range').addClass('hidden')
        },
    });

    ListView.include({

        load_list: function () {
            var self   = this;
            var result = self._super();
            if (self.last_domain) {
                if ($('.pr_search_by_range').hasClass('hidden') && $('.pr_search_by_range').length != 0 && $('.pr_search_by_range')[0].children.length == 0 ) {
                    self.render_buttons()
                  }
                $('.pr_search_by_range').removeClass('hidden')
            }
            else {
                $('.pr_search_by_range').addClass('hidden')
            }
            this.$('tfoot').css('display', 'table-header-group');
            return result;
        },

        do_search: function (domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            this.tgl_search()

        },

        tgl_search: function() {
            var self = this;
            var domain = [], value, value_tmp;

            _.each(self.ts_fields, function (field) {
                value = $('.sky_item_' + field).val();

                var select_fields = $('.sky_multi_item_' + field).children('.selected'),
                    select_value = [];
                if (select_fields.length > 0) {
                    _.each(select_fields, function (item) {
                        value_tmp = $(item).data('field');
                        if (value_tmp > 0) {
                            select_value.push($(item).data('field'));
                        }
                    });
                    if (select_value.length) {
                        domain.push([field, 'in', select_value]);
                    }

                }
            });



            if (self.$search_partner_phone) {
                var phone = self.$search_partner_phone.find('.sky_partner_phone').val()
                if (phone) {
                    domain.push(['phone', 'ilike', phone]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            if (self.$search_partner_user_id) {
                var user_id_name = self.$search_partner_user_id.find('.sky_user_id').val()
                if (user_id_name) {
                    domain.push(['user_id', 'like', user_id_name]);
                    var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                    self.dataset.domain = compound_domain.eval();
                    return self.old_search(compound_domain, self.last_context, self.last_group_by);
                }
            }
            if (self.$search_button) {
                var start_date  = self.$search_button.find('.sky_start_date').val(),
                    end_date    = self.$search_button.find('.sky_end_date').val(),
                    field       = self.$search_button.find('.sky_select_field').val();

                var l10n = _t.database.parameters;
                if (start_date) {
                    var start_date_list = start_date.split('/')
                    var mydate = new Date(start_date_list[2]+"/"+start_date_list[1]+"/"+start_date_list[0]);
                    var copiedDate = mydate.setHours(mydate.getHours() - 7);
                    copiedDate = moment(copiedDate).format('YYYY-MM-DD HH:mm:SS')
                    domain.push([field, '>=', copiedDate]);
                }
                if (end_date) {
                    end_date = moment(moment(end_date, time.strftime_to_moment_format(l10n.date_format))).format('YYYY-MM-DD');
                    domain.push([field, '<=', end_date]);
                }
                var compound_domain = new data.CompoundDomain(self.last_domain, domain);
                self.dataset.domain = compound_domain.eval();
                return self.old_search(compound_domain, self.last_context, self.last_group_by);
            }

            this._super.apply(this, arguments);
        },

        render_buttons: function ($node) {
            var self = this;

            this._super.apply(this, arguments);
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
            if (this.dataset.child_name && this.dataset.child_name != null ) return false;
            self.$buttons.find('.sky-search').remove();
            $('.pr_search_by_range').html('')

            var sky_fields = [];
            _.each(self.columns, function (value, key, list) {
                if (value.store && value.type === 'datetime' || value.type === 'date') {
                    sky_fields.push([value.name, value.string]);
                }
            });
            if (sky_fields.length > 0) {
                self.$search_button = $(QWeb.render('SkyERP.buttons', {'sky_fields': sky_fields}))
                self.$search_button.find('.sky_start_date').datetimepicker(datepickers_options);
                self.$search_button.find('.sky_end_date').datetimepicker(datepickers_options);

                self.$search_button.find('.sky_start_date').on('change', function () {
                    self.tgl_search();
                });
                self.$search_button.find('.sky_end_date').on('change', function () {
                    self.tgl_search();
                });
                self.$search_button.find('.sky_select_field').on('change', function () {
                    self.tgl_search();
                });

                if ($('.pr_search_by_range').length > 0) {
                    self.$search_button.appendTo($('.pr_search_by_range'));
                } else {
                    setTimeout(function () {
                        self.$search_button.appendTo($('.pr_search_by_range'));
                        $('.pr_search_by_range').removeClass('hidden')
                    }, 1000);
                }
            }

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
                    if ($('.pr_search_by_range').length > 0) {
                        self.$search_partner_phone.appendTo($('.pr_search_by_range'));
                    } else {
                        setTimeout(function () {
                            self.$search_partner_phone.appendTo($('.pr_search_by_range'));
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

                if (sky_fields.length > 0) {
                    self.$search_partner_user_id = $(QWeb.render('SkyERP.SearchPartnerUser', {'sky_fields': sky_fields}))
                    self.$search_partner_user_id.find('.sky_user_id').on('change', function () {
                        self.tgl_search();
                    });
                    // self.$search_customer.appendTo($('.cl_search_by_range'));
                    if ($('.pr_search_by_range').length > 0) {
                        self.$search_partner_user_id.appendTo($('.pr_search_by_range'));
                    } else {
                        setTimeout(function () {
                            self.$search_partner_user_id.appendTo($('.pr_search_by_range'));
                            // self.$clear_all.appendTo($('.cl_search_by_range'));
                        }, 500);
                    }
                }

            if (self.$search_button || self.$search_partner_phone || self.$search_partner_user_id) {
                self.$clear_all = $(QWeb.render('SkyERP.ClearAll', {}))
                $('.pr_search_by_range').on('click', '.button_clear_all', function () {
                    self.clear_tgl_search();
                });
                if ($('.pr_search_by_range').length > 0) {
                    setTimeout(function () {
                        self.$clear_all.appendTo($('.pr_search_by_range'));
                    }, 1000);
                } else {
                    setTimeout(function () {
                        self.$clear_all.appendTo($('.pr_search_by_range'));
                        $('.pr_search_by_range').on('click', '.button_clear_all', function () {
                            self.clear_tgl_search();
                        });
                    }, 1000);
                }
            }

        },
    clear_tgl_search: function () {
            try {
                var self = this;
                var compound_domain = new data.CompoundDomain(self.last_domain, []);
                self.dataset.domain = compound_domain.eval();
                console.log("clear ----")
                return self.old_search(compound_domain, self.last_context, self.last_group_by);
            } catch (err) {
            }
        },


    });
});