odoo.define('cptuanhuy_tree_gantt_custom.main',  function(require) {
	"use strict";

    var model = require('web_tree_gantt.TreeGanttView');
    var TreeGanttViewModel = model.TreeGanttView.prototype;
    var Model = require('web.Model');
    /*
        gantt.showTask(30) move screen to task.
        gantt.selectTask(19); select task
    */

    model.TreeGanttView = model.TreeGanttView.extend({
        add_gantt_config: function () {
            TreeGanttViewModel.add_gantt_config.call(this);

            if(this.model !== "project.planning") return false;
            let textEditor = {type: "text", map_to: "text"};
            let start_forecast = {type: "number", map_to: "start_forecast"};
            let doing_forecast = {type: "number", map_to: "doing_forecast"};
            let start_actual = {type: "number", map_to: "start_actual"};
            let doing_actual = {type: "number", map_to: "doing_actual"};
            let progress = {type: "number", map_to: "progress",min:0, max: 100};

            let columns = [
                {name:"text", editor:textEditor, resize: true, label:"Name", min_width: 300, tree:true, align: "left" },
                {name:"start_forecast",editor:start_forecast, resize: true, label:"(Dự kiến)Bắt đầu triển khai", min_width: 155, align: "center" , template: function (obj) {return obj.start_forecast;}},
                {name:"doing_forecast",editor:doing_forecast, resize: true, label:"(Dự kiến)Thời gian triển khai", min_width: 155, align: "center" , template: function (obj) {return obj.doing_forecast;}},
                {name:"start_actual",editor:start_actual, resize: true, label:"(Thực tế)Bắt đầu triển khai", min_width: 155, align: "center" , template: function (obj) {return obj.start_actual;}},
                {name:"doing_actual",editor:doing_actual, resize: true, label:"(Thực tế)Thời gian triển khai", min_width: 155, align: "center" , template: function (obj) {return obj.doing_actual;}},
                {name:"progress",editor:progress, resize: true, label:"Tiến Độ Triển Khai", min_width: 100, align: "center" , template: function (obj) {return obj.progress * 100 + '%';}},
            ];
            gantt.config.columns = columns;

            gantt.ext.inlineEditors.attachEvent("onSave",function(state){
                let col = state.columnName;
                if(gantt.autoSchedule && (col == "start_date" || col == "end_date" || col == "duration")){
                    gantt.autoSchedule();
                }
            });
            gantt.ext.inlineEditors.attachEvent("onEditStart",function(state){
                if(state.columnName == "progress"){
                    var task = gantt.getTask(state.id);
                    $("div[data-column-name='progress'][task_id='"+state.id+"']").find('input').val(task.progress * 100);
                }
            });
            gantt.ext.inlineEditors.attachEvent("onBeforeSave", function(state){
                let values = {};
                if(state.columnName == "progress") {
                    values[state.columnName] = state.newValue * 100;
                }else{
                    values[state.columnName] = state.newValue
                }
                new Model('project.planning').call('write', [parseInt(state.id), values]).done(function(result){
                    console.log('write done');
                });
                return true;
            });
        }
    })
});