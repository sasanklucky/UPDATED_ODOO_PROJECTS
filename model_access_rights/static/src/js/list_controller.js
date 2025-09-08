odoo.define('model_access_rights.list_controller', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var rpc = require('web.rpc');

    var CustomListController = ListController.include({

        willStart: function () {
            var self = this;
            self.removedActions = [];

            return this._super.apply(this, arguments).then(function () {
                return self._rpc({
                    model: 'access.right',
                    method: 'hide_buttons',
                    args: [],
                    kwargs: {
                        model: self.modelName,
                        user_id: self.getSession().uid,
                    },
                }).then(function (records) {

                    if (records.is_delete) self.removedActions.push("Delete");
                    if (records.is_export) self.removedActions.push("Export");
                    if (records.is_create_or_update) {
                        self.removedActions.push("Create");
                        self.removedActions.push("Update");
                    }
                    if (records.is_archive) self.removedActions.push("Archive");


                }).fail(function (error) {
                    console.error("RPC Error:", error);
                });
            });
        },

        renderSidebar: function ($node) {
            this._super.apply(this, arguments);
            if (this.sidebar && this.sidebar.options && this.sidebar.options.actions) {
                var actions = this.sidebar.options.actions.other || [];

                // Remove actions based on permissions
                this.sidebar.options.actions.other = actions.filter(function (action) {
                    return !this.removedActions.includes(action.label);
                }.bind(this));


                var newActions = {
                    print: this.sidebar.options.actions.print || [],
                    action: this.sidebar.options.actions.action || [],
                    relate: this.sidebar.options.actions.relate || [],
                    other: this.sidebar.options.actions.other || []
                };

                this.sidebar = new Sidebar(this, {
                    editable: this.is_action_enabled('edit'),
                    env: {
                        context: this.model.get(this.handle, { raw: true }).getContext(),
                        activeIds: this.getSelectedIds(),
                        model: this.modelName,
                    },
                    actions: newActions,
                });

                this.sidebar.appendTo($node);
                this._toggleSidebar();
            }
        }

    });

    return CustomListController;
});





