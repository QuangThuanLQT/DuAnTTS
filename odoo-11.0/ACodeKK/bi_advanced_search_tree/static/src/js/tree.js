odoo.define('bi_advanced_search_tree.tree', function (require) {
"use strict";

var time        = require('web.time');
var core        = require('web.core');
var data        = require('web.data');
var session     = require('web.session');
var utils       = require('web.utils');
var Model       = require('web.Model');
var ListView   = require('web.ListView');
var datepicker  = require('web.datepicker');
var ViewManager = require('web.ViewManager')
var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;

ListView.include({

    init: function(parent, dataset, view_id, options) {
        this._super.apply(this, arguments);
        this.ts_context = dataset.context.tree_search;
        this.fields_range = dataset.context.fields_range;
        this.ts_fields = [];
        this.field_values = []
    },

    on_button_click: function (event) {
        var self = this;
        var $target = $(event.target),
            field, key, first_item;

        field   = $target.parent().data('field');
        key     = $target.parent().data('key');

        if (field == -1) {
            first_item = $target.parent().parent().children('.tgl_first_item.selected');
            if (!first_item.length) {
                $target.parent().parent().children('li').removeClass('selected')
            }
        } else {
            first_item = $target.parent().parent().children('.tgl_first_item').removeClass('selected');
        }

        $target.parent().toggleClass('selected');
        this.tgl_search_new()
        event.stopPropagation();

    },
    load_search_row: function(){
    var self = this;
    var list_view = false;
    if(typeof self.last_domain != 'undefined'){
    if(typeof self.ViewManager.active_view != 'undefined')
    {
    list_view = true;
    }
        var l10n = _t.database.parameters;
        var datepickers_options = {
            pickTime: false,
            startDate: moment({ y: 1900 }),
            endDate: moment().add(200, "y"),
            calendarWeeks: true,
            icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            language : moment.locale(),
            format : time.strftime_to_moment_format(l10n.date_format),
        }


        var sky_fields = [];
        _.each(self.columns, function(value, key, list){
            if (value.string && value.string.length > 1 && value.invisible !== '1' || value.widget == 'handle') {
                if (value.store == false) {
                    sky_fields.push([value.name, value.string,'handle','handle']);
                }
                else {
                    if(typeof value.selection == 'undefined')
                    {
                    sky_fields.push([value.name, value.string,value.type,value.widget]);
                    }
                    else{
                    sky_fields.push([value.name, value.string,value.type,value.selection]);
                    }
                }
            }
        });

        if (sky_fields.length == 0) {
            if (self.fields_range) {
                sky_fields = self.fields_range;
            }
        }

        if (sky_fields.length > 0) {
            self.$search_range = $(QWeb.render('SearchRow', {'sky_fields': sky_fields,'list_view':list_view}))

            self.$search_range.find('.start_date').datetimepicker(datepickers_options);
            self.$search_range.find('.end_date').datetimepicker(datepickers_options);
            self.$search_range.find('.search_field').on('change', function() {
                self.tgl_search_new();
            });
            self.$search_range.find('.selection_field').on('change', function() {
                self.tgl_search_new();
            });
            // self.$search_range.find('.start_date').on('change', function() {
            //     self.tgl_search_new();
            // });
            // self.$search_range.find('.end_date').on('change', function() {
            //     self.tgl_search_new();
            // });

             self.$search_range.find('.end_date').keypress(function (e) {
                  if (e.which == 13) {
                    self.tgl_search_new();
                    return false;    //<---- Add this line
                  }
                });
            self.$search_range.find('.end_date').keypress(function (e) {
              if (e.which == 13) {
                self.tgl_search_new();
                return false;    //<---- Add this line
              }
            });
             self.$search_range.appendTo(self.$('#bullseye'));

        }
        }
        _.each(this.field_values, function(item){
                if(typeof item[2] == 'undefined'){
                  self.$('#'+item[0]).val(item[1]);
                }
                else{
                 self.$('#'+item[0]+item[2]).val(item[1]);
                }

            });
    },

    load_list: function() {
        var self = this;
        var result = this._super.apply(this, arguments);
        this.load_search_row();
        return result;
    },

    tgl_search_new: function() {
        var self = this;

        $('.o_filters_menu li').each(function() {
            if ($(this).hasClass('unselected')){
                $('li.unselected a').trigger('click');
                $(this).removeClass('unselected');
            }else if ($(this).hasClass('selected')){
                $(this).addClass('unselected');
                $('.o_facet_remove').trigger('click');
                $(this).remove();
            }

        });

        var domain = [], value, value_tmp;

        _.each(self.ts_fields, function(field){
            value = $('.sky_item_' + field).val();

            var select_fields = $('.sky_multi_item_' + field).children('.selected'),
                select_value = [];
            if (select_fields.length > 0) {
                _.each(select_fields, function(item){
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

        if (self.$search_range) {
            var l10n = _t.database.parameters;
            var search_fields = self.$search_range.find('.search_field');
            var start_date = self.$search_range.find('.start_date');
            var end_date = self.$search_range.find('.end_date');
            var selection_fields = self.$search_range.find('.selection_field');
            _.each(search_fields, function(item){
            var input_field  = item.name,
                input_value  = item.value;
                // input_type = item.type;
            self.field_values.push([input_field, input_value]);
            if (input_value) {
                var $filter_menu = $('.o_filters_menu')
                // open advanced search (not actually useful)
                $filter_menu.find('.o_add_filter').click();
                // open second condition
                // $filter_menu.find('button.o_add_condition').click();

                // select first proposition
                var $prop1 = $filter_menu.find('.o_filter_condition:first');
                $prop1.find('select.o_searchview_extended_prop_field').val(input_field).change();
                $prop1.find('select.o_searchview_extended_prop_op').val('ilike');
                $prop1.find('.o_searchview_extended_prop_value input')
                     .val(input_value);

                $filter_menu.find('button.o_apply_filter').click();
            }
            });
            _.each(start_date, function(item){
            var input_field  = item.name,
                input_value  = item.value;
                // input_type = item.type;
            self.field_values.push([input_field, input_value,item.className]);
            if (input_value) {
                input_value  = moment(moment(item.value, time.strftime_to_moment_format(l10n.date_format))).format('DD/MM/YYYY 00:00:00');
                var $filter_menu = $('.o_filters_menu')
                // open advanced search (not actually useful)
                $filter_menu.find('.o_add_filter').click();
                // open second condition
                // $filter_menu.find('button.o_add_condition').click();

                // select first proposition
                var $prop1 = $filter_menu.find('.o_filter_condition:first');
                $prop1.find('select.o_searchview_extended_prop_field').val(input_field).change();
                $prop1.find('select.o_searchview_extended_prop_op').val('>=');
                $prop1.find('input.o_datepicker_input').click();
                $prop1.find('input.o_datepicker_input').val(input_value);
                $prop1.find('input.o_datepicker_input').change();

                $filter_menu.find('button.o_apply_filter').click();
            }
           });
             _.each(end_date, function(item){
            var input_field  = item.name,
                input_value  = item.value;                // input_type = item.type;
             self.field_values.push([input_field, input_value,item.className]);
            if (input_value) {
                input_value  = moment(moment(item.value, time.strftime_to_moment_format(l10n.date_format))).format('DD/MM/YYYY 23:59:59');

                var $filter_menu = $('.o_filters_menu')
                // open advanced search (not actually useful)
                $filter_menu.find('.o_add_filter').click();
                // open second condition
                // $filter_menu.find('button.o_add_condition').click();

                // select first proposition
                var $prop1 = $filter_menu.find('.o_filter_condition:first');
                $prop1.find('select.o_searchview_extended_prop_field').val(input_field).change();
                $prop1.find('select.o_searchview_extended_prop_op').val('<=');
                $prop1.find('input.o_datepicker_input').click();
                $prop1.find('input.o_datepicker_input').val(input_value);
                $prop1.find('input.o_datepicker_input').change();

                $filter_menu.find('button.o_apply_filter').click();
            }
           });
            _.each(selection_fields, function(item){
            var input_field  = item.name,
                input_value  = item.value;
            self.field_values.push([input_field, input_value]);// input_type = item.type;
            if (input_value) {
                var $filter_menu = $('.o_filters_menu')
                // open advanced search (not actually useful)
                $filter_menu.find('.o_add_filter').click();
                // open second condition
                // $filter_menu.find('button.o_add_condition').click();

                // select first proposition
                var $prop1 = $filter_menu.find('.o_filter_condition:first');
                $prop1.find('select.o_searchview_extended_prop_field').val(input_field).change();
                $prop1.find('select.o_searchview_extended_prop_op').val('=');
                $prop1.find('.o_searchview_extended_prop_value select').val(input_value).change();

                $filter_menu.find('button.o_apply_filter').click();
            }
           });
        }


        console.log(domain);
        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
        self.dataset.domain = compound_domain.eval();
        return self.old_search(compound_domain, self.last_context, self.last_group_by);
    },

});
});