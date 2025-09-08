odoo.define("odoo_web_login.password_instruction_list_v3", function (require) {
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
            position: "left", // Change to top-right for better UX
            className: "custom-toast-password-instruction",
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
         setTimeout(function() {
            console.log("Fetching Password Instruction Messages...");

            ajax.jsonRpc("/get_password_instruction_messages", "call", {}).then(function (message) {
                console.log("Received Messages:", message.password_lower);
                console.log("Checking if Toastify is loaded:", window.Toastify);

                let instructions = [];

                if (message.password_lower && message.password_lower > 0)
                    instructions.push(`✅ Must contain at least **${message.password_lower} lowercase letter**.`);

                if (message.password_upper && message.password_upper > 0)
                    instructions.push(`✅ Must contain at least **${message.password_upper} uppercase letter**.`);

                if (message.password_numeric && message.password_numeric > 0)
                    instructions.push(`✅ Must contain at least **${message.password_numeric} numeric digit**.`);

                if (message.password_special && message.password_special > 0)
                    instructions.push(`✅ Must contain at least **${message.password_special} special character**.`);

                if (message.password_length && message.password_length > 0)
                    instructions.push(`✅ Must be **at least ${message.password_length} characters long**.`);

                console.log("Compiled Instructions:", instructions);

                if (instructions.length > 0) {
                    let instructionText = "🔐 **Password Requirements:**\n\n" + instructions.join("\n");
                    console.log("Showing Notification:", instructionText);
                    showNotification(instructionText, "linear-gradient(to right, #00b09b, #96c93d)");
                }

            }).fail((error) => console.error("Error fetching password instruction messages:", error));
         }, 1000);


    });
});
