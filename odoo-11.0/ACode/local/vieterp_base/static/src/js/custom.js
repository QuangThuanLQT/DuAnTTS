odoo.define('vieterp_base.custom', function (require) {
	"use strict";

	var core          = require('web.core');
	var form_common   = require('web.form_common');
	var Model         = require('web.Model');
	var ListView      = require('web.ListView');

	ListView.include({
        load_list: function() {
            var self   = this;
            var result = self._super();
            var index;

            this.$('tbody .o_list_record_selector input').click(function() {
                var checked = $(this).prop('checked');
                if (checked) {
                    $(this).closest('tr').addClass('text-success');
                } else {
                    $(this).closest('tr').removeClass('text-success');
                }
            });
            return result;
        },
        // keydown_LEFT: function (e) {
        //     var source_field = $(e.target).closest('[data-fieldname]').attr('data-fieldname');
        //     var fields_order = this.editor.form.fields_order;
        //     var field_index  = _(fields_order).indexOf(source_field);
        //     var fields       = this.editor.form.fields;
        //     var prev_field   = false;
        //     var field;
        //
        //     for (var index = 0; index < field_index; index++) {
        //         field = fields[fields_order[index]];
        //         if (field.$el.is(':visible') && !field.get('effective_readonly')) {
        //             prev_field = field;
        //         }
        //     }
        //
        //     if (prev_field) {
        //         e.preventDefault();
        //         prev_field.focus();
        //         return false;
        //     }
        //     return $.when();
        // },
        //
        // keydown_RIGHT: function (e) {
        //     var source_field = $(e.target).closest('[data-fieldname]').attr('data-fieldname');
        //     var fields_order = this.editor.form.fields_order;
        //     var field_index  = _(fields_order).indexOf(source_field);
        //     var fields       = this.editor.form.fields;
        //     var next_field   = false;
        //     var field;
        //
        //     if (field_index >= fields_order.length - 1) {
        //         e.preventDefault();
        //         return this._next();
        //     } else {
        //         for (var index = field_index + 1; index < fields_order.length; index++) {
        //             field = fields[fields_order[index]];
        //             if (field.$el.is(':visible') && !field.get('effective_readonly')) {
        //                 next_field = field;
        //                 console.log('fields_order[index]', fields_order[index]);
        //                 break;
        //             }
        //         }
        //     }
        //
        //     if (next_field) {
        //         e.preventDefault();
        //         next_field.focus();
        //         return false;
        //     }
        //     return $.when();
        // },

        // keyup_UP: function (e) {
        //     console.log('keyup_UP');
        //     var self = this;
        //     var next_record = 'pred';
        //     var options = {};
        //     return this.save_edition().then(function (saveInfo) {
        //         if (!saveInfo) { return null; }
        //         if (saveInfo.created) {
        //             return self.start_edition();
        //         }
        //         if (!options) {
        //             options = {};
        //         }
        //         options.wraparound = !self.is_action_enabled('create');
        //         var record = self.records[next_record](saveInfo.record, options);
        //         if (record === undefined) {
        //             return self.start_edition();
        //         }
        //         self.__focus = true;
        //         return self.start_edition(record, options);
        //     });
        // },

        keyup_UP: function (e) {
            if(!this.editor.record || !this.editor.record.id ){
                if(!$(e.target).hasClass('ui-autocomplete-input')){
                    $('tr.o_row_edition').prev().find('[data-field="'+$(e.target).attr('data-fieldname')+'"]').click()
                }
            }else{
                return this._super.apply(this, arguments);
            }
        },

        keyup_DOWN: function (e) {
            var docViewTop =    $('.o_main').scrollTop();
            var docViewBottom = docViewTop + $('.o_main').height();

            var elemTop = $('tr.o_row_edition').next().offset().top + $('.o_main').scrollTop();
            var elemBottom = elemTop + $('tr.o_row_edition').next().height();

            if ((elemBottom >= docViewBottom)){
                let scrollto = $('.o_main').scrollTop()+40;
                $('.o_main').animate({
                    scrollTop: scrollto
                }, 700);
            }
            if(!this.editor.record || !this.editor.record.id ){
                if(!$(e.target).hasClass('ui-autocomplete-input')){
                    $('tr.o_row_edition').parent().find('tr td.o_form_field_x2many_list_row_add a').click();
                }
            }else{
                return this._super.apply(this, arguments);
            }
        },

        do_add_record: function () {
            this._super.apply(this, arguments);
            let scrollto = $('.o_main').scrollTop()+35;
            $('.o_main').animate({
                scrollTop: scrollto
            }, 700);
        },
    });

	var checkBoxLastShift = null;
	ListView.List.include({
        render: function () {
            this._super.apply(this, arguments);
            let list_checkbox = this.$current.find('.o_list_record_selector .o_checkbox input');
            checkBoxLastShift = null;
            list_checkbox.each((index,item) => {
                $(item).click(function (event) {
                    if(event.shiftKey){
                        console.log('checkBoxLastShift',checkBoxLastShift);
                        if(checkBoxLastShift !== null){
                            list_checkbox.each((index1,item1) => {
                                if( index1 < index && index1 > checkBoxLastShift ){
                                    $(item1).click();
                                }
                            });
                        }
                        checkBoxLastShift = index;
                    }
                });
            });
        }
    })
});