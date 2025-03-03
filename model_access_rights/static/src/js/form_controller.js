odoo.define('model_access_rights.form_controller', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var rpc = require('web.rpc');

    FormController.include({

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
            var self = this;
            this._super.apply(this, arguments);

            if (this.sidebar && this.sidebar.options.actions) {

                // Modify actions while keeping existing ones (like Attachments)
                this.sidebar.options.actions.other = (this.sidebar.options.actions.other || []).filter(function (action) {
                    return !self.removedActions.includes(action.label);
                });
                this.sidebar.items.other = (this.sidebar.items.other || []).filter(function (action) {
                    return !self.removedActions.includes(action.label);
                });

                // Force Sidebar UI to update without losing Attachments
                this.sidebar._redraw();
            }
        }
    });

    return FormController;
});
