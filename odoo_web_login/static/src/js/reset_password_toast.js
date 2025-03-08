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
        console.log("Checking for alerts...");

        // Delay execution to ensure alerts are present
        setTimeout(function () {
            var errorElement = $(".alert.alert-danger");
            var successElement = $(".alert.alert-success");

            console.log("Error Elements Found:", errorElement.length);
            console.log("Success Elements Found:", successElement.length);

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
        }, 10); // Delay by 500ms to ensure elements are available
    });
});
