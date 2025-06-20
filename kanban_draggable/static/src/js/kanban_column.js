odoo.define('kanban_draggable.kanban_column',function(require){
"use strict";


var KanbanColumn = require('web.KanbanColumn');

KanbanColumn.include({
    start: function () {
        this._super.apply(this, arguments);

        if (this.record_options.sortable==false){
            this.$el.sortable( "disable" );
            // Disable clicking on the dropdown (gear icon)
            this.$('.o_kanban_config .dropdown-toggle').off('click').on('click', function (e) {
                e.stopPropagation();
                e.preventDefault();
            });
            this.$('.o_kanban_quick_add').off('click').on('click', function (e) {
                e.stopPropagation();
                e.preventDefault();
            });
        }

    },

});
});