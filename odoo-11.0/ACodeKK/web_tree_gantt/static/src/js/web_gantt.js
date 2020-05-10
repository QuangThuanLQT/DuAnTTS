odoo.define('web_tree_gantt.web_gantt', function(require) {
	"use strict";

    var GanttView = require('web_gantt.GanttView');
    var data_manager = require('web.data_manager');
    var ajax = require('web.ajax');

    //update lib to 6.0.2
    GanttView.include({
        on_data_loaded: function () {
            if(!gantt._click){
                gantt._click = {};
            }
            return this._super.apply(this, arguments);
        },
        willStart: function () {
            var self = this;

            var defs = [];
            defs.push($.when());
            defs.push(data_manager.load_fields(this.dataset).then(function (fields) {
                self.fields = fields;
                if(self.fields.color) {
                    self.fields_to_fetch.push('color');
                }
                if(self.fields.active) {
                    self.fields_to_fetch.push('active');
                }
            }));

            if (!window.gantt) {
                defs.push(ajax.loadJS('/web_tree_gantt/static/lib/dhtmlxgantt/dhtmlxgantt.js'));
                defs.push(ajax.loadCSS('/web_tree_gantt/static/lib/dhtmlxgantt/dhtmlxgantt.css'));
            }

            return $.when.apply($, defs);
        },
    });
});