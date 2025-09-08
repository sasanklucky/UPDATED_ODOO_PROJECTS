odoo.define("ac_rms.tour", function (require) {
"use strict";

var core = require("web.core");
var tour = require("web_tour.tour");
var base = require("web_editor.base");
var _t = core._t;

tour.register("ac_rms_tour", {
    url: "/",
    wait_for: base.ready(),
}, [{
	trigger: "a[data-action=edit1]",
    extra_trigger: '#wrapwrap',
    content:  _t("Select registration number and drop on calender to create a slot on bay."),
    position: "top",
}]);
});