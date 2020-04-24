odoo.define('web_tree_gantt.TreeGanttView', function (require) {

    var exports = {};
    var Backbone = window.Backbone;
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;

    exports.TreeGanttView = Backbone.Model.extend({
        template: 'WebTreeGantt',
        initialize: function (element,dataset,attributes,model) {
            this.tree_node = element;
            this.dataset = dataset;
            this.model = model;
            this.$el = null;
            this.attributes = attributes;
            this.data = this.parse_data();
            this.task_data = this.prepare_task_data();
            this.start();
        },

        start: function () {
            let self = this;
            this.load_lib().done(function(load_item) {
                if(window.gantt) {
                    if (load_item) {
                    };
                    self.add_gantt_config();
                    self.render_gantt();
                }
            });
        },

        render_gantt() {
            let self = this;
            this.$el = $(QWeb.render(this.template, {}));
            this.$el.filter('button.o_cp_switch_gantt').click(this.gantt_button_click.bind(this));
            this.$el.filter('button.o_cp_switch_list').click(this.tree_button_click.bind(this));
            this.tree_node.before(this.$el);
            gantt.init("gantt_here");
            gantt.parse({'data':this.task_data});
        },

        tree_button_click() {
            this.tree_node.removeClass('hidden');
            this.$el.filter('#gantt_here').addClass('hidden');
            this.$el.filter('.o_cp_switch_list').addClass('active');
            this.$el.filter('.o_cp_switch_gantt').removeClass('active');
        },

        gantt_button_click() {
            this.tree_node.addClass('hidden');
            this.$el.filter('#gantt_here').removeClass('hidden');
            this.$el.filter('.o_cp_switch_list').removeClass('active');
            this.$el.filter('.o_cp_switch_gantt').addClass('active');
        },

        add_gantt_config() {
            gantt.config.scale_height = 3 * 28;
            gantt.config.date_grid = "%Y-%m-%d";
            gantt.config.scale_unit = "month";
            //month top format
            gantt.config.date_scale = "%F, %Y";
            //height top line
            gantt.config.scale_height = 50;
            //date top format
            gantt.config.subscales = [
                {unit: "day", step: 1, date: "%d"}
            ];
            //cell width
            gantt.config.min_column_width = 25;
            //duration unit
            if(this.attributes['duration_unit']){
                gantt.config.duration_unit = this.attributes['duration_unit'];
            }
            //column
            let columns = [{name:"text",label:"Name",min_width: 350,tree:true,align: "left" }];
            if(this.attributes['column_label']){
                let values = this.attributes['column_value'].split(',');
                this.attributes['column_label'].split(',').forEach((item,index,list) => {
                    let column = {
                        'name': values[index],
                        'label': item,
                        'min_width': 75,
                        'align': "center"
                    };
                    if(values[index] === 'progress'){
                        column['template'] = function (obj) {
                             return obj.progress * 100 + '%';
                        }
                    }
                    columns.push(column);
                });
            }
            gantt.config.columns = columns;

            gantt.ext.inlineEditors.attachEvent("onEditStart",function(state){
                if(state.columnName == "progress"){
                    var task = gantt.getTask(state.id);
                    $("div[data-column-name='progress'][task_id='"+state.id+"']").find('input').val(task.progress * 100);
                }
            });
            gantt.ext.inlineEditors.attachEvent("onBeforeSave", function(state){
                if(state.columnName == "progress") {
                    state.newValue = parseInt(state.newValue) / 100;
                }
                return true;
            });
        },

        parse_data() {
            let data = [];
            $.each(this.dataset.cache,function (index,value) {
                data.push(value.from_read)
            });
            return data;
        },

        prepare_task_data() {
            return this.data.map(item => {
                let readonly = true;
                if(this.attributes['readonly'] && (['false','0'].includes(this.attributes['readonly'].toLowerCase()))){
                    readonly = false;
                }
                let open = false;
                if(this.attributes['open'] && (['true','1'].includes(this.attributes['open'].toLowerCase()))){
                    open = true;
                }
                let result =  {
                    'id': item.id,
                    'text':item.name,
                    'start_date': moment(item[this.attributes['start_date']],'YYYY-MM-DD HH:mm:ss').format('DD-MM-YYYY'),
                    'readonly':readonly,
                    'open':open,
                };
                if(this.attributes['end_date']){
                    result['end_date'] = moment(item[this.attributes['end_date']],'YYYY-MM-DD HH:mm:ss').format('DD-MM-YYYY');
                }else{
                    result['duration'] = eval(this.attributes['duration']);
                }
                $.each(item,(name,value) => {
                    if(!(['id','name','start_date','end_date','progress','readonly','open','duration','duration_unit'].includes(name)))
                    result[name] = value;
                });
                if(this.attributes['progress']){
                    result['progress'] = item[this.attributes['progress']] / 100;
                }
                return result
            });
        },

        load_lib() {
            var defs = [];
            if (!window.gantt) {
                defs.push(ajax.loadJS('/web_tree_gantt/static/lib/dhtmlxgantt/dhtmlxgantt.js'));
                defs.push(ajax.loadCSS('/web_tree_gantt/static/lib/dhtmlxgantt/dhtmlxgantt.css'));
            }else{
                defs.push($.when(true));
            }
            return $.when.apply($, defs);
        }
    });
    return exports;
});
