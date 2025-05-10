odoo.define('ac_company_branch.SwitchBranchMenu', function(require) {
    "use strict";

    var config = require('web.config');
    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var _t = core._t;

    var SwitchBranchMenu = Widget.extend({
        template: 'SwitchBranchMenu',

        willStart: function() {
            this.isMobile = config.device.isMobile;
            if (!session.user_branches) {
                return $.Deferred().reject();
            }
            return this._super();
        },

        start: function() {
            var self = this;
            var current_branch = session.user_branches.current_branch;
            var allowed_branches = session.user_branches.allowed_branches;

            // 🔁 Handle branch click
            this.$el.on('click', '.dropdown-menu li a[data-menu]', _.debounce(function(ev) {
                ev.preventDefault();
                var branch_id = $(ev.currentTarget).data('branch-id');
                self._rpc({
                    model: 'res.users',
                    method: 'write',
                    args: [[session.uid], { 'branch_id': branch_id }],
                }).then(function() {
                    location.reload();
                });
            }, 1500, true));

            // ✅ Auto-select if only one branch is available
            if ((!current_branch || !current_branch[0]) && allowed_branches.length === 1) {
                var auto_branch_id = allowed_branches[0][0];
                this._rpc({
                    model: 'res.users',
                    method: 'write',
                    args: [[session.uid], { 'branch_id': auto_branch_id }],
                }).then(function() {
                    location.reload();
                });
                return;  // prevent further execution
            }

            // 👇 Render dropdown list
            var branches_list = '';
            if (this.isMobile) {
                branches_list = '<li class="bg-info">' + _t('Tap on the list to change branch') + '</li>';
            }

            if (current_branch && current_branch[1]) {
                self.$('.oe_topbar_name').text(current_branch[1]);
            } else {
                self.$('.oe_topbar_name').text("Select Branch");
                self.do_notify(_t("No Branch Selected"), _t("Please select a branch from the dropdown."));
            }

            //  Add branches to dropdown
            _.each(allowed_branches, function(branch) {
                var a = (branch[0] === (current_branch && current_branch[0])) ?
                        '<i class="fa fa-check mr8"></i>' :
                        '<span class="mr24"/>';
                branches_list += '<li><a href="#" data-menu="branch" data-branch-id="' + branch[0] + '">' + a + branch[1] + '</a></li>';
            });

            self.$('.dropdown-menu').html(branches_list);
            return this._super();
        },
    });

    SystrayMenu.Items.push(SwitchBranchMenu);
    return SwitchBranchMenu;
});
