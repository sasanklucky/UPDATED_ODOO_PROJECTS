odoo.define("odoo_web_login.reset_password_toast", function (require) {
    "use strict";

    var ajax = require("web.ajax");

    function showNotification(text, background) {
        if (!window.Toastify) {
            console.error("Toastify.js not loaded!");
            return;
        }

        Toastify({
            text: text,
            duration: -1,
            close: true,
            gravity: "top",
            position: "center", // Change to top-right for better UX
            className: "custom-toast-rest-password",
            style: {
                background: background,
                width: "400px",
                textAlign: "center",
                whiteSpace: "normal",
                wordWrap: "break-word",
                borderRadius: "10px",
                padding: "12px"
            }
        }).showToast();
    }

    $(document).ready(function () {
    function showAlerts() {
        var errorElement = $(".alert.alert-danger:visible"); // Only pick visible error messages
        var successElement = $(".alert.alert-success:visible"); // Only pick visible success messages

        if (errorElement.length) {
            var errorMessage = errorElement.text().trim();
            if (errorMessage) {
                showNotification(errorMessage, "linear-gradient(to right, #ff5f6d, #ffc371)");
                errorElement.hide(); // Hide original error message
            }
        }

        if (successElement.length) {
            var successMessage = successElement.text().trim();
            if (successMessage) {
                showNotification(successMessage, "linear-gradient(to right, #00b09b, #96c93d)");
                successElement.hide(); // Hide original success message
            }
        }
    }

    // Run check on page load
    showAlerts();

    // Listen for form submission and re-check for new errors
    $("form").on("submit", function (e) {
        setTimeout(showAlerts, 50); // Delay to wait for error message to appear
    });
});

});
