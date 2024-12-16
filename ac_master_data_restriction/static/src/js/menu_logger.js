//odoo.define('ac_master_data_restriction.menu_logger', function (require) {
//    'use strict';
//
//    var Menu = require('web.Menu');
//    var session = require('web.session');
//
//    Menu.include({
//        start: function () {
//            var self = this;
//            this.$el.on('click', 'a[data-menu]', function (event) {
//                var menu_id = $(event.currentTarget).data('menu'); // Get menu ID
//                console.log('Menu Clicked:', menu_id);
//
//                // Optionally, store the menu_id in the session context
//                session.user_context.current_menu_id = menu_id;
//            });
//            return this._super.apply(this, arguments);
//        },
//    });
//});

odoo.define('ac_master_data_restriction.menu_logger', function (require) {
    "use strict";

    var Menu = require('web.Menu');
    var session = require('web.session');
    var core = require('web.core');

    Menu.include({
        bind_menu: function () {
            // Call the original bind_menu method to preserve existing functionality
            this._super.apply(this, arguments);

            // Clear any previously bound click events to prevent duplication
            this.$el.off('click', 'a[data-menu]');
            this.$secondary_menus.off('click', 'a[data-menu]');

            var self = this;

            // Handle parent menu clicks
            this.$el.on('click', 'a[data-menu]', function (event) {
                event.preventDefault();
                event.stopPropagation(); // Stop event propagation to prevent unexpected behavior

                var menu_id = $(event.currentTarget).data('menu');
                if (menu_id) {
                    console.log('Parent Menu Clicked:', menu_id);

                    // Update session with the current menu ID
                    session.user_context.current_menu_id = menu_id;

                    // Trigger menu section change for the core bus
                    core.bus.trigger('change_menu_section', menu_id);
                }
            });

            // Handle submenu clicks
            this.$secondary_menus.on('click', 'a[data-menu]', function (event) {
                event.preventDefault();
                event.stopPropagation();

                var submenu_id = $(event.currentTarget).data('menu');
                if (submenu_id) {
                    console.log('Submenu Clicked:', submenu_id);

                    // Update session with the current submenu ID
                    session.user_context.current_menu_id = submenu_id;

                    // Trigger menu section change for the core bus
                    core.bus.trigger('change_menu_section', submenu_id);
                }
            });

            // Ensure nested submenus are toggled correctly
            this.$secondary_menus.find('.oe_menu_toggler')
                .siblings('.oe_secondary_submenu')
                .addClass('o_hidden');

            if (self.current_menu) {
                self.open_menu(self.current_menu);
            }

            this.trigger('menu_bound');
        },

        /**
         * Opens a given menu by id, as if a user had browsed to that menu manually.
         * @param {Number} id - ID of the terminal menu to select.
         */
        open_menu: function (id) {
            this.current_menu = id;
            session.active_id = id;
            var $clicked_menu, $sub_menu, $main_menu;

            $clicked_menu = this.$el.add(this.$secondary_menus).find('a[data-menu=' + id + ']');
            this.trigger('open_menu', id, $clicked_menu);

            if (this.$secondary_menus.has($clicked_menu).length) {
                $sub_menu = $clicked_menu.parents('.oe_secondary_menu');
                $main_menu = this.$el.find('a[data-menu=' + $sub_menu.data('menu-parent') + ']');
            } else {
                $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + $clicked_menu.attr('data-menu') + ']');
                $main_menu = $clicked_menu;
            }

            // Activate current main menu
            this.$el.find('.active').removeClass('active');
            $main_menu.parent().addClass('active');

            // Show current sub menu
            this.$secondary_menus.find('.oe_secondary_menu').hide();
            $sub_menu.show();

            // Hide/Show the left bar menu depending on the presence of sub-items
            this.$secondary_menus.toggleClass('o_hidden', !$sub_menu.children().length);

            // Activate current menu item and show parents
            this.$secondary_menus.find('.active').removeClass('active');
            if ($main_menu !== $clicked_menu) {
                $clicked_menu.parents().removeClass('o_hidden');
                if ($clicked_menu.is('.oe_menu_toggler')) {
                    $clicked_menu.toggleClass('oe_menu_opened')
                        .siblings('.oe_secondary_submenu:first').toggleClass('o_hidden');
                } else {
                    $clicked_menu.parent().addClass('active');
                }
            }
        },
    });
});





//odoo.define('ac_master_data_restriction.menu_logger', function (require) {
//    "use strict";
//
//    var core = require('web.core');
//    var session = require('web.session');
//    var Widget = require('web.Widget');
//
//    var Menu = require('web.Menu');
//
//    Menu.include({
//        // Bind menu with logging and nested submenu handling
//        bind_menu: function() {
//            var self = this;
//
//            // Call the original bind_menu method to preserve existing functionality
//            this._super.apply(this, arguments);
//
//            // Parent menu click logging
//            this.$el.on('click', 'a[data-menu]', function (event) {
//                event.preventDefault();
//                var menu_id = $(event.currentTarget).data('menu');
//                if (menu_id) {
//                    console.log('Parent Menu Clicked:', menu_id);
//                    session.user_context.current_menu_id = menu_id;
//                    core.bus.trigger('change_menu_section', menu_id);
//                }
//            });
//
//            // Submenu click logging and nested submenu handling
//            this.$secondary_menus.on('click', 'a[data-menu]', function (event) {
//                event.preventDefault();
//                var submenu_id = $(event.currentTarget).data('menu');
//                if (submenu_id) {
//                    console.log('Submenu Clicked:', submenu_id);
//                    session.user_context.current_menu_id = submenu_id;
//                    core.bus.trigger('change_menu_section', submenu_id);
//                }
//
//                // Ensure the submenu opens correctly if it's a nested submenu
//                var $subMenu = $(event.currentTarget).siblings('.oe_secondary_submenu');
//                if ($subMenu.length) {
//                    $subMenu.toggleClass('o_hidden');  // Toggle visibility of the submenu
//                    $(event.currentTarget).toggleClass('oe_menu_opened'); // Toggle open/close icon or class
//                }
//            });
//
//            // Hide second-level submenus initially (for styling/behavior consistency)
//            this.$secondary_menus.find('.oe_menu_toggler').siblings('.oe_secondary_submenu').addClass('o_hidden');
//
//            // Make sure the menu is opened when a submenu exists
//            if (self.current_menu) {
//                self.open_menu(self.current_menu);
//            }
//
//            // Trigger reflow for responsive layout (optional, but helps with resizing)
//            var lazyreflow = _.debounce(this.reflow.bind(this), 200);
//            core.bus.on('resize', this, function () {
//                if ($(window).width() < 768) {
//                    lazyreflow('all_outside');
//                } else {
//                    lazyreflow();
//                }
//            });
//            core.bus.trigger('resize');
//        },
//
//        // Reflow the menu for responsive design (optional)
//        reflow: function(behavior) {
//            var self = this;
//            var $more_container = this.$('#menu_more_container').hide();
//            var $more = this.$('#menu_more');
//            var $systray = this.$el.parents().find('.oe_systray');
//
//            $more.children('li').insertBefore($more_container);  // Pull all the items out of the more menu
//
//            if (behavior === 'all_outside') {
//                self.$el.show();
//                this.$el.find('li').show();
//                $more_container.hide();
//                return;
//            }
//
//            var $toplevel_items = this.$el.find('li').not($more_container).not($systray.find('li')).hide();
//            self.$el.show();
//            $toplevel_items.each(function() {
//                var remaining_space = self.$el.parent().width() - $more_container.outerWidth();
//                self.$el.parent().children(':visible').each(function() {
//                    remaining_space -= $(this).outerWidth();
//                });
//
//                if ($(this).width() >= remaining_space) {
//                    return false;
//                }
//                $(this).show();
//            });
//            $more.append($toplevel_items.filter(':hidden').show());
//            $more_container.toggle(!!$more.children().length);
//
//            var $toplevel = self.$el.children("li:visible");
//            if ($toplevel.length === 1) {
//                $toplevel.hide();
//            }
//        },
//
//        // Open a menu by its ID
//        open_menu: function (id) {
//            this.current_menu = id;
//            session.active_id = id;
//            var $clicked_menu, $sub_menu, $main_menu;
//            $clicked_menu = this.$el.add(this.$secondary_menus).find('a[data-menu=' + id + ']');
//
//            if (this.$secondary_menus.has($clicked_menu).length) {
//                $sub_menu = $clicked_menu.parents('.oe_secondary_menu');
//                $main_menu = this.$el.find('a[data-menu=' + $sub_menu.data('menu-parent') + ']');
//            } else {
//                $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + $clicked_menu.attr('data-menu') + ']');
//                $main_menu = $clicked_menu;
//            }
//
//            this.$el.find('.active').removeClass('active');
//            $main_menu.parent().addClass('active');
//
//            this.$secondary_menus.find('.oe_secondary_menu').hide();
//            $sub_menu.show();
//            this.$secondary_menus.toggleClass('o_hidden', !$sub_menu.children().length);
//
//            this.$secondary_menus.find('.active').removeClass('active');
//            if ($main_menu !== $clicked_menu) {
//                $clicked_menu.parents().removeClass('o_hidden');
//                if ($clicked_menu.is('.oe_menu_toggler')) {
//                    $clicked_menu.toggleClass('oe_menu_opened').siblings('.oe_secondary_submenu:first').toggleClass('o_hidden');
//                } else {
//                    $clicked_menu.parent().addClass('active');
//                }
//            }
//
//            this.$secondary_menus.find('.oe_secondary_submenu li a span').each(function() {
//                $(this).tooltip(this.scrollWidth > this.clientWidth ? {title: $(this).text().trim(), placement: 'right'} :'destroy');
//            });
//        },
//
//        // Handle menu item click
//        menu_click: function(id) {
//            if (!id) { return; }
//
//            var $item = this.$el.find('a[data-menu=' + id + ']');
//            if (!$item.length) {
//                $item = this.$secondary_menus.find('a[data-menu=' + id + ']');
//            }
//            var action_id = $item.data('action-id');
//
//            if (!action_id) {
//                if(this.$el.has($item).length) {
//                    var $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + id + ']');
//                    var $items = $sub_menu.find('a[data-action-id]').filter('[data-action-id!=""]');
//                    if($items.length) {
//                        action_id = $items.data('action-id');
//                        id = $items.data('menu');
//                    }
//                }
//            }
//
//            if (action_id) {
//                this.trigger('menu_click', {
//                    action_id: action_id,
//                    id: id,
//                    previous_menu_id: this.current_menu
//                }, $item);
//            } else {
//                console.log('Menu no action found web test 04 will fail');
//            }
//            this.open_menu(id);
//        }
//    });
//
//    return Menu;
//});


//
//odoo.define('ac_master_data_restriction.menu_logger', function (require) {
//    "use strict";
//
//    var Menu = require('web.Menu');
//    var session = require('web.session');
//    var core = require('web.core');
//
//    Menu.include({
//        bind_menu: function () {
//            // Call the original bind_menu method to preserve existing functionality
//            this._super.apply(this, arguments);
//
//            var self = this;
//
//            // Parent menu click logging and handling submenu toggling
//            this.$el.on('click', 'a[data-menu]', function (event) {
//                var menu_id = $(event.currentTarget).data('menu');
//                if (menu_id) {
//                    console.log('Parent Menu Clicked:', menu_id);
//                    session.user_context.current_menu_id = menu_id;
//                    core.bus.trigger('change_menu_section', menu_id);
//
//                    // Ensure submenu toggling when a parent menu is clicked
//                    var $submenu = self.$el.find('.oe_secondary_menu[data-menu-parent=' + menu_id + ']');
//                    if ($submenu.length) {
//                        $submenu.removeClass('o_hidden').show(); // Open the submenu
//                    }
//                }
//            });
//
//            // Submenu click logging and toggling
//            this.$secondary_menus.on('click', 'a[data-menu]', function (event) {
//                var submenu_id = $(event.currentTarget).data('menu');
//                if (submenu_id) {
//                    console.log('Submenu Clicked:', submenu_id);
//                    session.user_context.current_menu_id = submenu_id;
//                    core.bus.trigger('change_menu_section', submenu_id);
//
//                    // Open the submenu's nested submenus (if applicable)
//                    var $nested_submenu = self.$secondary_menus.find('.oe_secondary_submenu[data-parent=' + submenu_id + ']');
//                    if ($nested_submenu.length) {
//                        $nested_submenu.removeClass('o_hidden').show(); // Open nested submenu
//                    }
//                }
//            });
//
//            // Ensure all submenus are hidden by default when the page is loaded
//            this.$secondary_menus.find('.oe_menu_toggler').siblings('.oe_secondary_submenu').addClass('o_hidden');
//
//            // Close all submenus initially
//            this.$el.find('.oe_secondary_submenu').addClass('o_hidden');
//        },
//    });
//});