odoo.define('web_tree_gantt.main', function(require) {
	"use strict";

    var ListView = require('web.ListView');
    var TreeGanttView = require('web_tree_gantt.TreeGanttView');

    ListView.include({
        load_list: function() {
            let self = this;
            let result = self._super();
            if(this.x2m && this.x2m.$el.hasClass('tree_gantt_view') && !this.tree_gantt_view){
                this.create_tree_gantt_view();
            }
            return result;
        },
        create_tree_gantt_view(){
            this.tree_gantt_view = new TreeGanttView.TreeGanttView(this.x2m.$el,this.dataset,this.x2m.node.attrs,this.model);
        },
    });


});