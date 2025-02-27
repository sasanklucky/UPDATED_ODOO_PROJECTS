odoo.define('model_access_rights.kanban_controller', function (require) {
    "use strict";

    var KanbanController = require('web.KanbanController');
    var rpc = require('web.rpc');

    KanbanController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            var self = this;

            // Fetch user permissions only once
            rpc.query({
                model: 'access.right',
                method: 'hide_buttons',
                args: [],
                kwargs: {
                    model: self.modelName,
                    user_id: self.getSession().uid,
                },
            }).then(function (records) {
                var removedActions = [];
                if (records.is_delete) removedActions.push("Delete");
                if (records.is_archive) removedActions.push("Archive");
                if (records.is_edit) removedActions.push("Edit");

//                console.log("Removed Actions:", removedActions);

                // Apply the changes to all Kanban dropdowns after rendering
                setTimeout(function () {
                    var dropdowns = self.$el.find('.o_dropdown_kanban .dropdown-menu');

                    if (!dropdowns.length) return;

                    dropdowns.each(function () {
                        var dropdown = $(this);

                        dropdown.find('a').each(function () {
                            var actionLabel = $(this).text().trim();
                            if (removedActions.includes(actionLabel)) {
                                $(this).remove(); // Remove the restricted actions
                            }
                        });
                    });

                }, 500); // Delay for proper dropdown rendering

            }).fail(function (error) {
                console.error("RPC Error:", error);
            });

        }
    });

});





