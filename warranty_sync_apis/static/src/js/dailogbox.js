odoo.define('warranty_sync_apis.DataLineItemSplit', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var NotificationManager = require('web.notification');
    var QWeb = core.qweb;
    var _t = core._t;




    var DataLineItemSplit = Dialog.extend({
        template: 'split_order_line_data',

        init: function(parent, record, selectedRecords, context) {
            this.selected_records = selectedRecords;
            this.record = record;
            this.records_data = {};
            this.contexts = context;

            var options = {
                title: _t("Split Line Items"),
                buttons: [],
            };
            this._super(parent, options);
        },

        start: function() {
            var self = this;
            var $modalBody = this.$el.find('.modal-body');
             // Show loading animation
             $modalBody.find('.loading-spinner').show();

            self._rpc({
                model: 'sale.order.line',
                method: 'fetch_data_orders_line',
                args: [],
                kwargs: {
                    model: self.record.model,
                    res_ids: self.record.res_ids,
                    selected_ids: self.selected_records,
                    context: self.contexts,
                },
            }).done(function (records) {
                console.log("Fetched records:", records);
                console.log("Context after RPC:", self.contexts);
                self.records_data = records;

                // Hide the loading animation
                $modalBody.find('.loading-spinner').hide();

                self._renderTable(records);
            }).fail(function (error) {
                console.error("RPC Error:", error);
                // Hide the loading animation even in case of failure
                $modalBody.find('.loading-spinner').hide();
            });
        },

        _renderTable: function(records) {
            var self = this;
            var $modalBody = this.$el.find('.modal-body');
            $modalBody.empty();

            let grouped_data = {};
            records.forEach(record => {
                if (!grouped_data[record.sale_order_line]) {
                    grouped_data[record.sale_order_line] = [];
                }
                grouped_data[record.sale_order_line].push(record);
            });

            Object.keys(grouped_data).forEach(function (sale_line) {
                var $tableContainer = $('<div class="sale-order-line-table"></div>');

                var $table = $(`
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th></th>
                                <th style="width: 200px;">Customer</th>
                                <th>Percentage (%)</th>
                                <th>Un-Tax Amount</th>
                                <th>Tax</th>
                                <th>Taxable Amount</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                `);

                var $headerRow = $(QWeb.render('split_order_line_header', { sale_order_line: sale_line }));
                $table.find('tbody').append($headerRow);

                grouped_data[sale_line].forEach((record, index) => {
                    var isFirstInGroup = [0,1].includes(index);
                    var $row = $(QWeb.render('split_order_line_data_row', {
                        customer_id: record.customer_id,
                        category_id: record.category_id,
                        product_id: record.product_id,
                        line_id: record.line_id,
                        customer_name: record.customer_name,
                        customers_list: record.customers_list,
                        percent_val: record.percentage || "0.00",
                        subtotal_val: record.subtotal || "0.00",
                        tax_val: record.tax || "0.00",
                        tax_ids: record.tax_ids || "[]",
                        taxamount_val: record.taxable_amount || "0.00",
                        is_first: isFirstInGroup,
                    }));
                    $table.find('tbody').append($row);
                });

                $tableContainer.append($table);
                $modalBody.append($tableContainer);
            });

            this._bindEvents();
        },

        _bindEvents: function() {
            var self = this;

            // Event Delegation for "Add" button
            this.$el.off('click', '.add-row').on('click', '.add-row', function() {
                var $btn = $(this);
                var $tr = $btn.closest('tr');
                var $tbody = $tr.closest('tbody');

                // Fetch available customers
                var customers = [];
                self.$el.find('.customer_select:first option').each(function() {
                    customers.push({ id: $(this).val(), name: $(this).text() });
                });

                // Get the tax value from the **previous row**
                var prevRow = $tr.prev('tr');  // Get the row just before the current one
                var tax_val = prevRow.find('.tax_value').val() || "0.00";
                var tax_ids = prevRow.find('.tax_ids').val() || "0.00";
                var product_id = prevRow.find('.product_id').val() || "0";
                var category_id = prevRow.find('.category_id').val() || "0";
                var line_id = prevRow.find('.line_id').val() || "0";
                var newRow = $(QWeb.render('split_order_line_data_row', {
                    customer_id: "",
                    product_id: product_id,
                    line_id: line_id,
                    customer_name: "",
                    customers_list: customers,
                    category_id: category_id,
                    percent_val: "0.00" + "%",
                    subtotal_val: "0.00",
                    tax_val: tax_val,
                    tax_ids: tax_ids,
                    taxamount_val: "0.00",
                    is_first: false,
                }));

                $tbody.append(newRow);
                self._makeRowsReadonly();

            });

            // Event Delegation for "Remove" button
            this.$el.off('click', '.remove-row').on('click', '.remove-row', function() {
                var $btn = $(this);
                var $tr = $btn.closest('tr');
                var removedRowData = {};
                var len_index = null;
                var $tbody = $tr.closest('tbody');
                var $rows = $tbody.find('tr:has(td)');
                var rowIndex = $tr.index();
                console.log("Number of rows:", rowIndex);
                var dynamicClasses = ['customer_select', 'percentage_value', 'subtotal_value', 'tax_value', 'taxamount_value'];
                $rows.each(function(index) {
                    if (index === rowIndex) {
                        $(this).find('td').each(function() {
                            var value = null;
                            for (var i = 0; i < dynamicClasses.length; i++) {
                                var $element = $(this).find('.' + dynamicClasses[i]); // Find element with dynamic class
                                if ($element.length) {
                                     var key = dynamicClasses[i]; // Use the class name as the key
                                     var value = $element.val() || $element.text().trim(); // Get value
                                     removedRowData[key] = value; // Store key-value pair
                                }
                            }
                        });
                    }
                    len_index = index
                });
               var $previousRow = $rows.eq(2); // Get the previous row
               if ($previousRow.length) {
                    // Update Subtotal Value
                    var $subtotalCell = $previousRow.find('.subtotal_value');
                    if ($subtotalCell.length) {
                        var subtotalValue = parseFloat($subtotalCell.val()) || 0;
                        var removedSubtotalValue = parseFloat(removedRowData.subtotal_value) || 0;
                        $subtotalCell.val(subtotalValue + removedSubtotalValue);
                        console.log('Subtotal Updated:', subtotalValue + removedSubtotalValue);
                    } else {
                        console.error("Subtotal cell not found in the previous row.");
                    }

                    // Update Percentage Value
                    var $percentageCell = $previousRow.find('.percentage_value');
                    if ($percentageCell.length) {
                        var percentageValue = parseFloat($percentageCell.val().replace('%', '')) || 0; // Remove % and convert to number
                        var removedPercentageValue = parseFloat(removedRowData.percentage_value.replace('%', '')) || 0; // Ensure the removed value is numeric
                        console.log(removedPercentageValue, 'removedPercentageValue')

                        var updatedPercentage = percentageValue + removedPercentageValue; // Sum percentages
                        $percentageCell.val(updatedPercentage + '%'); // Append % back
                        console.log('Percentage Updated:', updatedPercentage + '%');

                    } else {
                        console.error("Percentage cell not found in the previous row.");
                    }
               } else {
                    console.error("Previous row not found.");
                }

            $rows.each(function(index) {
                var $row = $(this);

                // Get tax value and subtotal from the row
                var $element_tax = $row.find('.tax_value');
                var $element_subtotal = $row.find('.subtotal_value');
                var $elementTaxAmountUpdate = $row.find('.taxamount_value');

                if ($element_tax.length && $element_subtotal.length) {
                    var tax_value = $element_tax.val() || '0'; // Get tax text (e.g., "GST 18%")
                    var subtotal_value = parseFloat($element_subtotal.val()) || 0; // Convert subtotal to float

                    // Extract numeric tax percentage (e.g., "GST 18%" -> 18)
                    var tax_per = tax_value.match(/\d+/);
                    var taxRate = tax_per ? parseFloat(tax_per[0]) : 0;

                    // Calculate taxable amount
                    var taxableAmount = (subtotal_value * taxRate) / 100;

                    // Update tax amount field
                    $elementTaxAmountUpdate.val(taxableAmount.toFixed(2));

                    console.log(`Row ${index}: Subtotal = ${subtotal_value}, Tax Rate = ${taxRate}%, Taxable Amount = ${taxableAmount}`);
                }
            });


                $tr.remove();
                console.log("Last Rows:", removedRowData);
            });

            // Event Delegation for Customer Selection
            this.$el.off('change', '.customer_select').on('change', '.customer_select', function() {
                console.log("Selected customer:", $(this).val());
            });

            this.$el.on('change', '.subtotal_value, .percentage_value', function(){
            var $btn = $(this);
            var $tr = $btn.closest('tr');
            var $tbody = $tr.closest('tbody');
            var changedField = $btn.hasClass('subtotal_value') ? 'subtotal' : 'percentage';
            self._recalculateAmounts($tbody, $tr, self.records_data, changedField);
            console.log("ONCHANGE")
            });
            var previousValues = {};

            this.$el.on('input', '.subtotal_value, .percentage_value', function(event) {
                var self = this;
                var $input = $(this);
                var value = parseFloat($input.val());
                var changedField = $input.hasClass('subtotal_value') ? 'subtotal' : 'percentage';

                if (value < 0) {
                    self.do_notify && self.do_notify("Warning", "Negative values are not allowed!", "info"); // Ensure function exists

                    if (changedField === 'subtotal') {
                        $input.val(0);
                    } else if (changedField === 'percentage') {
                        $input.val('0.00%');
                    }
                }
            });


           this.$el.on('keydown', '.subtotal_value, .percentage_value', function(event) {
                if (event.keyCode !== 8 && event.keyCode !== 46) {
                    return; // Ignore other keys
                }

                var $btn = $(this);
                var $tr = $btn.closest('tr');
                var $tbody = $tr.closest('tbody');
                var changedField = $btn.hasClass('subtotal_value') ? 'subtotal' : 'percentage';
                console.log(changedField,'changedField')
                self._recalculateAmountsBackSpace(event, $tbody, $tr, $(this).val(), changedField, self.records_data); // Pass current value before deletion
           });

           this.$el.off('click', '.save-button').on('click', '.save-button', function() {
                console.log("Selected customer:");
                var $btn = $(this);
                var $tr = $btn.closest('tr');
                var $tbody = $tr.closest('tbody');
                self._onSave();
            });


        },

        _recalculateAmountsBackSpace: function(event, $tbody, $tr, previousInputValue, changedField, records_data) {
            var $rows = $tbody.find('tr:has(td)');
            var presentRowData = {};
            var dynamicClasses = ['percentage_value', 'subtotal_value'];
            if (event.keyCode === 8 || event.keyCode === 46) {  // Backspace or Delete
                var rowIndex = $tr.index();
                $rows.each(function(index) {
                    if (index === rowIndex) {
                        $(this).find('td').each(function() {
                            for (var i = 0; i < dynamicClasses.length; i++) {
                                var $element = $(this).find('.' + dynamicClasses[i]);
                                if ($element.length) {
                                    var key = dynamicClasses[i];
                                    var value = $element.val() || $element.text().trim();
                                    presentRowData[key] = value;
                                    break;
                                }
                            }
                        });
                    }
                });

            }
            console.log("Backspace/Delete pressed! Previous Value:", presentRowData);

            var dynaSubtotalClasses = ['subtotal_value'];
            var totalSubtotal = 0; // Variable to store the total
            var $rows = $tbody.find('tr:has(td)');

            $rows.each(function(index) {
                if (index >=2){
                    $(this).find('td').each(function() {
                        for (var i = 0; i < dynaSubtotalClasses.length; i++) {
                            var $elementSubtotal = $(this).find('.' + dynaSubtotalClasses[i]);
                            if ($elementSubtotal.length) {
                                var valueSubtotal = parseFloat($elementSubtotal.val() || $elementSubtotal.text().trim()) || 0;
                                totalSubtotal += valueSubtotal; // Add the value to the total
                                console.log("Row Subtotal:", totalSubtotal); // Log each row's subtotal
                                break;
                            }
                        }
                    });
                }
            });

            console.log("Total Subtotal:", totalSubtotal); // Log the final total


            // Get first two keys & values safely
            var firstTwoKeys = Object.keys(presentRowData).slice(0, 2);
            var firstValue = firstTwoKeys.map(key => presentRowData[key] || "0"); // Ensure default value

            console.log("First Values from presentRowData:", firstValue);
            var saleOrderLine = $tbody.find('.sale-order-line-header').text().trim();
            const uniqueData = [];
            const seen = new Map(); // Use Map to track occurrences

            for (const item of records_data) {
                const count = seen.get(item.sale_order_line) || 0;
                seen.set(item.sale_order_line, count + 1);

                if (count === 1) { // Add only the second occurrence
                    uniqueData.push(item);
                }
            }

            console.log(uniqueData);

            // Find the second occurrence matching `saleOrderLine`
            let singleMatchSubtotal = null;
            let singleMatchPercentage = null;
            for (const item of uniqueData) {
                if (item.sale_order_line === saleOrderLine) {
                    singleMatchSubtotal = item.subtotal;
                    singleMatchPercentage = item.percentage.replace('%', '');
                    break; // Stop once the first second occurrence is found
                }
            }

            console.log(singleMatchSubtotal);
            console.log(singleMatchPercentage);

            if (changedField == 'subtotal'){
                var subClasses = ['subtotal_value'];
                $rows.each(function(index) {
                    if (index === 2) {  // Target the third row
                        $(this).find('td').each(function() {
                            for (var i = 0; i < subClasses.length; i++) {
                                var $element = $(this).find('.' + subClasses[i]);
                                if ($element.length) {
                                    var value = parseInt($element.val()) || 0; // Handle NaN case
                                    var x = parseInt(previousInputValue) || 0; // Use old value before backspace
                                    var y = value + x;
                                    if (!(x > value) && !(y > singleMatchSubtotal) && !(totalSubtotal != singleMatchSubtotal)) {
                                        $element.val(y);
                                    }
                                }
                            }
                        });
                    }
                });
            } else if(changedField == 'percentage') {
                    var subClasses = ['percentage_value'];
                    $rows.each(function(index) {
                        if (index === 2) {  // Target the third row
                            $(this).find('td').each(function() {
                                for (var i = 0; i < subClasses.length; i++) {
                                    var $element = $(this).find('.' + subClasses[i]);
                                    if ($element.length) {
                                        var value = parseFloat($element.val().replace('%', '')) || 0; // Handle NaN case
                                        console.log(previousInputValue,value,$element.val(), 'previousInputValue')
                                        var x = parseFloat(previousInputValue.replace('%', '')) || 0; // Use old value before backspace
                                        var y = value + x;
                                        console.log(y, 'KRISHNA');
                                        if (!(x > value)) {
                                            $element.val(y+'%');
                                        }
                                    }
                                }
                            });
                        }
                    });
            }
        },




        _recalculateAmounts: function($tbody, $tr, records_dataa, changedField) {
            var $t = $tr
            var rowIndex = $tr.index();
            var $rows = $tbody.find('tr:has(td)');
            console.log(changedField, 'changedField');
            const rowData = {};
            var allRowsSubtotalAmt = {};
            var allRowsPercentage = {};
            var lastRowData = {};
            var len_index = null;
            var subtotalClass = ['subtotal_value'];
            var percentageClass = ['percentage_value'];
            var taxClass = ['tax_value'];
            var dynamicClasses = ['customer_select', 'percentage_value', 'subtotal_value', 'tax_value', 'taxamount_value'];
            var $previousRows = $rows.eq(2);
            var $targetCells = $previousRows.find('.subtotal_value');

            var saleOrderLine = $tbody.find('.sale-order-line-header').text().trim();
            console.log(saleOrderLine);
            const uniqueData = [];
            const seen = new Set();
            for (const item of records_dataa) {
                if (!seen.has(item.sale_order_line)) {
                    seen.add(item.sale_order_line);
                    uniqueData.push(item);
                }
            }
            console.log(uniqueData);
            var singleMatch = null;
            for (var key in uniqueData) {
                if (uniqueData[key].sale_order_line === saleOrderLine) {
                    singleMatch = uniqueData[key].totals;
                    break; // Stop once the first match is found
                }
            }

            console.log("Single Sale Order Line:", singleMatch);

            // Retrieve previous row data (row index 2)
            $rows.each(function(index) {
                if (index === 2) {
                    $(this).find('td').each(function() {
                        for (var i = 0; i < dynamicClasses.length; i++) {
                            var $element = $(this).find('.' + dynamicClasses[i]);
                            if ($element.length) {
                                var key = dynamicClasses[i];
                                var value = $element.val() || $element.text().trim();
                                rowData[key] = value;
                            }
                        }
                    });
                }
                len_index = index;
            });

            if (changedField === 'subtotal'){
                const subtotal_value = parseFloat(rowData.subtotal_value) || 0;

                // Retrieve last row data
                $rows.each(function(index) {
                    if (index === rowIndex) {
                        $(this).find('td').each(function() {
                            for (var i = 0; i < dynamicClasses.length; i++) {
                                var $element = $(this).find('.' + dynamicClasses[i]);
                                if ($element.length) {
                                    var key = dynamicClasses[i];
                                    var value = $element.val() || $element.text().trim();
                                    lastRowData[key] = value;
                                    break;
                                }
                            }
                        });
                    }
                });

                console.log(lastRowData, 'lastRowData');
                const lastSubtotalValue = parseFloat(lastRowData.subtotal_value) || 0;

                if (!isNaN(lastSubtotalValue)) {
                    var changed_subtotal = parseFloat(subtotal_value) - parseFloat(lastSubtotalValue);
                    console.log(changed_subtotal, 'Changed');
                    console.log(lastSubtotalValue, 'lastSubtotalValue');

                    var $previousRow = $rows.eq(2);
                    var $targetCell = $previousRow.find('.subtotal_value');

                    if ($targetCell.length) {
                        if (!isNaN(changed_subtotal)) {
                            if (lastSubtotalValue == 0){
                                this.do_notify("Warning", "Don't leave blank in subtotal.", "danger", false);

                            }else{
                                console.log($targetCells.val(), '$targetCells.val()')
                                $targetCell.val(changed_subtotal);
                            }
                        } else {
                            $targetCell.val(subtotal_value);
                        }
                    } else {
                        console.error("Target cell not found in the previous row.");
                    }
                }

                // Collect all subtotal values
                $rows.each(function(index) {
                    $(this).find('td').each(function() {
                        for (var i = 0; i < subtotalClass.length; i++) {
                            var $element = $(this).find('.' + subtotalClass[i]);
                            if ($element.length) {
                                var key = subtotalClass[i];
                                var value = parseFloat($element.val()) || 0; // Convert to number safely
                                allRowsSubtotalAmt[index] = value;
                            }
                        }
                    });
                });

                const totalSubtotalSum = Object.values(allRowsSubtotalAmt).reduce((sum, value) => sum + value, 0);

                console.log(allRowsSubtotalAmt, totalSubtotalSum);


                const updatedPercentage = {};

                // Iterate through allRowsSubtotalAmt and update rows
                Object.entries(allRowsSubtotalAmt).forEach(([index, value]) => {
                    const numValue = parseFloat(value) || 0; // Ensure it's a valid number
                    const percentage = totalSubtotalSum > 0 ? ((numValue / totalSubtotalSum) * 100).toFixed(2) : 0; // Avoid division by zero


                    const rowIndex = parseInt(index, 10);
                    const $row = $rows.eq(rowIndex);

                    // Update the row's percentage field
                    $row.find('.percentage_value').val(percentage + "%");

                    // Store updated percentage values
                    updatedPercentage[rowIndex] = { amount: numValue, percentage: percentage + "%" };
                });

                console.log("Updated Percentages:", updatedPercentage);

            }else if (changedField === 'percentage'){
                const RowPercentage = parseFloat(rowData.percentage_value.replace('%', '')) || 0;
                console.log(RowPercentage)
                // Retrieve last row data
                $rows.each(function(index) {
                    if (index === rowIndex) {
                        $(this).find('td').each(function() {
                            for (var i = 0; i < dynamicClasses.length; i++) {
                                var $element = $(this).find('.' + dynamicClasses[i]);
                                if ($element.length) {
                                    var key = dynamicClasses[i];
                                    var value = $element.val() || $element.text().trim();
                                    lastRowData[key] = value;
                                    break;
                                }
                            }
                        });
                    }
                });
                const lastPercentageValue = parseFloat(lastRowData.percentage_value.replace('%', '')) || 0;
                if (lastPercentageValue < RowPercentage && lastPercentageValue > 0){

                if (!isNaN(lastPercentageValue)) {
                    var changed_percentage = parseFloat(RowPercentage) - parseFloat(lastPercentageValue);
                    console.log(changed_percentage, 'Changed');
                    console.log(lastPercentageValue, 'lastPercentageValue');

                    var $previousRow = $rows.eq(2);
                    var $targetCell = $previousRow.find('.percentage_value');

                    if ($targetCell.length) {
                        if (!isNaN(changed_percentage)) {
                            if (lastPercentageValue == 0 || lastPercentageValue == 0.00 || lastPercentageValue == '0.00%'){
                                this.do_notify("Warning", "Don't leave blank in percentage." , "info");
                            }else{
                                console.log($targetCells.val(), '$targetCells.val()')
                                $targetCell.val(changed_percentage + '%');
                            }
                        } else {
                            $targetCell.val(RowPercentage + '%');
                        }
                    } else {
                        console.error("Target cell not found in the previous row.");
                    }
                }

                // Collect all percentage values
                $rows.each(function(index) {
                    $(this).find('td').each(function() {
                        for (var i = 0; i < percentageClass.length; i++) {
                            var $element = $(this).find('.' + percentageClass[i]);
                            if ($element.length) {
                                var key = percentageClass[i];
                                var value = parseFloat($element.val()) || 0; // Convert to number safely
                                allRowsPercentage[index] = value;
                            }
                        }
                    });
                });

                // Collect all subtotal values
                $rows.each(function(index) {
                    $(this).find('td').each(function() {
                        for (var i = 0; i < subtotalClass.length; i++) {
                            var $element = $(this).find('.' + subtotalClass[i]);
                            if ($element.length) {
                                var key = subtotalClass[i];
                                var value = parseFloat($element.val()) || 0; // Convert to number safely
                                allRowsSubtotalAmt[index] = value;
                            }
                        }
                    });
                });

                const totalSubtotalSum = Object.values(allRowsSubtotalAmt).reduce((sum, value) => sum + value, 0);
                console.log(totalSubtotalSum, 'totalSubtotalSum')
                console.log(allRowsPercentage, 'allRowsPercentage');
                const totalPercentageSum = Object.values(allRowsPercentage).reduce((sum, value) => sum + value, 0);
                const totalPercentageSumUp = parseFloat(totalPercentageSum);
                console.log(allRowsPercentage,totalPercentageSum, totalPercentageSumUp);

                const updatedAmt = {};

                // Iterate over data and update rows
                Object.entries(allRowsPercentage).forEach(([index, value]) => {
                    const numValue = parseFloat(value);
                    //const percentage = ((numValue / totalSum) * 100).toFixed(2); // Calculate percentage
                    const dividedAmount = ((numValue / totalPercentageSumUp) * totalSubtotalSum).toFixed(2); // Compute divided amount
                    if (index >=2){
                        // Find the corresponding row
                    const rowIndex = parseInt(index, 10);
                    const $row = $rows.eq(rowIndex);


                    // Update subtotal and percentage in the row
                    $row.find('.subtotal_value').val(Math.round(dividedAmount));
                    // $row.find('.percentage_value').val(percentage + "%");
                    // Store updated percentage values
                    updatedAmt[rowIndex] = { amount: numValue, percentage: dividedAmount };
                    }

                });
                console.log(updatedAmt);
                }else{
                this.do_notify("Warning", `Don't give a percentage less than 0.00 and greater than ${RowPercentage}%` , "info");
                }
            }

            if (changedField === 'subtotal' || changedField === 'percentage') {
                var subtotalValue = parseFloat($t.find('.subtotal_value').val()) || 0;
                var taxRate = parseFloat($t.find('.tax_value').val()) || 0;

                // Calculate the taxable amount
                var taxableAmount = (subtotalValue * taxRate) / 100;
                console.log(taxableAmount, 'taxableAmount')
                $t.find('.taxamount_value').val(taxableAmount.toFixed(2)); // Update the field


                // Collect all tax values
                $rows.each(function(index) {
                    var $row = $(this);

                    // Get tax value and subtotal from the row
                    var $element_tax = $row.find('.tax_value');
                    var $element_subtotal = $row.find('.subtotal_value');
                    var $elementTaxAmountUpdate = $row.find('.taxamount_value');

                    if ($element_tax.length && $element_subtotal.length) {
                        var tax_value = $element_tax.val() || '0'; // Get tax text (e.g., "GST 18%")
                        var subtotal_value = parseFloat($element_subtotal.val()) || 0; // Convert subtotal to float

                        // Extract numeric tax percentage (e.g., "GST 18%" -> 18)
                        var tax_per = tax_value.match(/\d+/);
                        var taxRate = tax_per ? parseFloat(tax_per[0]) : 0;

                        // Calculate taxable amount
                        var taxableAmount = (subtotal_value * taxRate) / 100;

                        // Update tax amount field
                        $elementTaxAmountUpdate.val(taxableAmount.toFixed(2));

                        console.log(`Row ${index}: Subtotal = ${subtotal_value}, Tax Rate = ${taxRate}%, Taxable Amount = ${taxableAmount}`);
                    }
                });


            }
        },

         _makeRowsReadonly: function() {
            var $tables = $('.table-striped'); // Select all tables

            $tables.each(function() {
                var $rows = $(this).find('tbody tr'); // Get all rows
                var rowCount = $rows.length;

                $rows.each(function(index) {
                    var $row = $(this);
                    var $inputs = $row.find('input, select, textarea'); // Find input fields
                    var $element_subtotal = $row.find('.percentage_value');
                    var $elementTaxAmtVal = $row.find('.taxamount_value');
                    if (index < 3) {
                        //  First two rows - Always readonly
                        $inputs.prop('readonly', true);
                        $inputs.prop('disabled', true);
                    } else if (index < rowCount - 1) {
                        //  All previous rows after first two - Readonly
                        $inputs.prop('readonly', true);
                        $inputs.prop('disabled', true);
                    } else {
                        //  Last row (newly added) - Editable
                        $inputs.prop('readonly', false);
                        $inputs.prop('disabled', false);
                        $element_subtotal.prop('readonly', true);
                        $element_subtotal.prop('disabled', true);
                        $elementTaxAmtVal.prop('readonly', true);
                        $elementTaxAmtVal.prop('disabled', true);
                    }
                });
            });
        },



        _onSave: function() {
            console.log("Save button clicked!");
            var self = this;
            var grouped_data = {};

            // Loop through each sale order line section
            this.$el.find('.sale-order-line-table').each(function () {
                var $table = $(this).find('table');

                // Get the Sale Order Line ID from the header row
                var sale_order_line = $table.find('.sale-order-line-header strong').text().trim();

                if (!grouped_data[sale_order_line]) {
                    grouped_data[sale_order_line] = [];
                }

                // Loop through each row in the table
                $table.find('tbody tr').each(function () {
                    var $row = $(this);

                    var customer_id = $row.find('.customer_select').val();
                    var category_id = $row.find('.category_id').val();
                    var product_id = $row.find('.product_id').val();
                    var line_id = $row.find('.line_id').val();
                    var percentage = $row.find('.percentage_value').val();
                    var subtotal = $row.find('.subtotal_value').val();
                    var tax = $row.find('.tax_value').val();
                    var tax_ids = $row.find('.tax_ids').val();
                    var taxable_amount = $row.find('.taxamount_value').val();

                    if (customer_id) {
                        grouped_data[sale_order_line].push({
                            customer_id: parseInt(customer_id),
                            category_id: parseInt(category_id),
                            product_id: parseInt(product_id),
                            line_id: parseInt(line_id),
                            percentage: parseFloat(percentage) || 0,
                            subtotal: parseFloat(subtotal) || 0,
                            tax: tax || 0,
                            tax_ids: tax_ids || 0,
                            taxable_amount: parseFloat(taxable_amount) || 0
                        });
                    }
                });
            });

            console.log("Collected Data:", grouped_data);  // Debugging

            self._rpc({
                model: 'sale.order.line',
                method: 'create_data_orders_line',
                args: [grouped_data],
                kwargs: {
                },
            }).done(function (response) {
                self.close();
                console.log('heloo')
            }).fail(function (err) {
                console.error("Error saving data:", err);
            });
        },
    });

    return DataLineItemSplit;
});
