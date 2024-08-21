var maintenance_scenario_table;
var selectedRowData = {};
$(function () {
    //global setting to make bootstrap table editable
    $.fn.editable.defaults.mode = 'inline';
    getMaintenanceScenarioListData();
});

function getMaintenanceScenarioListData() {
    MMOUtils.showLoader();

    // API call to get the maintenance scenario list
    $.ajax({
        url: '/get_maintenance_scenario_list',
        type: 'GET',
        dataType: "json",
        processData: false,
        contentType: false,
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        success: function (response) {
            //table of maintenance scenarios
            maintenance_scenario_table = $("#maintenance-scenario-table");
            maintenance_scenario_table.bootstrapTable({
                data: response,
                pagination: true,
                pageSize: 25,
                search: true,
                columns: [
                    { field: 'id', title: 'Scenario ID', align: 'center' },
                    { field: 'scenario_name', title: 'Scenario Name', align: 'left' },
                    {
                        field: 'category', title: 'Category',
                    },
                    {
                        field: 'optimization_type_id', title: 'Scenario Type',
                        formatter: function (data, row, index) {
                            if (parseInt(data) === 3) {
                                return 'New Budget Allocation';
                            } else if (parseInt(data) === 4) {
                                return 'Incremental Budget Allocation';
                            } else if (parseInt(data) === 1) {
                                return 'Budget Reallocation';
                            }
                            else {
                                return '<div style="text-align: center;">-</div>';
                            }
                        }
                    },
                    { field: 'outcome_maximize', title: 'Outcome To <br> Maxmize', align: 'center' },
                    {
                        field: 'status', title: 'Status', align: 'center',
                    },
                    {
                        field: 'name', title: 'Base Scenario',
                        formatter: function (data, row, index) {
                            if (data == '-') {
                                return '<div style="text-align: center;">-</div>'
                            }
                            else {
                                return data
                            }
                        }
                    },
                    {
                        field: 'base_budget', title: 'Base Budget($)', align: 'right', formatter: function (value, row, index) {
                            // return value
                            if (value == '-') {
                                return '<div style="text-align: center;">-</div>'
                            }
                            else {
                                if (value == 0) {
                                    return d3.format(",.0f")(value)
                                } else {
                                    return d3.format(",.0f")(value)
                                }
                            }
                        }
                    },
                    {
                        field: 'total_budget', title: 'Total Budget($)', align: 'right', formatter: function (value, row, index) {
                            // return value

                            if (value) {
                                if (value == '-') {
                                    return '<div style="text-align: center;">-</div>'
                                }
                                else {
                                    if (value == 0) {
                                        return d3.format(",.0f")(value)
                                    } else {
                                        return d3.format(",.0f")(value)
                                    }
                                }
                            }
                            else {
                                return '<div style="text-align: center;">-</div>'

                            }
                        }
                    },
                    { field: 'period_year', title: 'Year', align: 'center' },
                    { field: 'period_type', title: 'Period Type', align: 'center' },
                    { field: 'period_start', title: 'Period Start', align: 'center' },
                    { field: 'period_end', title: 'Period End', align: 'center' },
                    { field: 'username', title: 'Created By', align: 'left' },
                    { field: 'created_on', title: 'Created On' },
                    {
                        field: 'select', title: 'Select', align: 'center',
                        formatter: function (value, row, index) {
                            return '<input type="radio" name="selectRadio" class="select-radio" data-index="' + index + '"/>';
                        },
                        events: {
                            'change .select-radio': function (e, value, row, index) {
                                $('.select-radio').prop('checked', false);
                                $(e.target).prop('checked', true);
                            }
                        }
                    },
                ],
                onPostBody: function () {
                    // After the table is rendered, update header cells for multiline text
                    // updateMultilineHeader();
                    MMOUtils.hideLoader();
                },
            });
        },
        error: function (error) {
            MMOUtils.hideLoader();
            console.log(error);
        }
    });

}
function updateMultilineHeader() {
    var headers = $('#maintenance-scenario-table thead tr th');
    headers.eq(3).html('<div style="white-space: normal;">Outcome To<br>Maximize</div>');
}
$('#maintenance-scenario-table').on('change', '.select-radio', function () {
    // Get the selected radio button
    var selectedRadio = $(this);
    var rowIndex = selectedRadio.data('index');
    selectedRowData = $('#maintenance-scenario-table').bootstrapTable('getData')[rowIndex];
    if (selectedRadio.prop('checked')) {
        $('#deletescenario, #downloadscenario').prop('disabled', false);
    } else {
        $('#deletescenario, #downloadscenario').prop('disabled', true);
    }
});
$('#downloadscenario').on('click', function () {
    MMOUtils.showLoader()
    console.log('Download button clicked for row:', selectedRowData);
    var scenario_optim_id = selectedRowData.id
    var queryString = `scenario_id=${scenario_optim_id}&status=${selectedRowData.status}&scenario_name=${selectedRowData.scenario_name}&user_name=${selectedRowData.username}&period_type=${selectedRowData.period_type}&period_end=${selectedRowData.period_end}&period_start=${selectedRowData.period_start}&base_scenario=${selectedRowData.name}&category=${selectedRowData.category}`;
    // $.ajax({
    //     url: '/download_app_logs?' + queryString,
    //     type: 'GET',
    //     headers: {
    //         "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    //     },
    //     success: function (data) {
    //         document.location.href = '/download_app_logs?' + queryString,
    //             MMOUtils.hideLoader()
    //     },
    //     error: function (error) {
    //         MMOUtils.hideLoader()
    //         console.error('Error downloading file:', error);
    //     }
    // });
    window.location.href = '/download_app_logs?' + queryString;
    MMOUtils.hideLoader();
});

$('#deletescenario').on('click', function () {
    console.log('Download button clicked for row:', selectedRowData);
    var scenario_optim_id = selectedRowData.id
    var data = {
        "optimization_scenario_id": scenario_optim_id,
        "scenario_name": selectedRowData.scenario_name,
        "category": selectedRowData.category
    };
    var isConfirmed = confirm("Are you sure you want to delete this scenario?");

    if (isConfirmed) {
        MMOUtils.showLoader()
        $.ajax({
            url: '/delete_optimized_scenario',
            type: "POST",
            data: JSON.stringify(data),
            processData: false,
            contentType: false,
            dataType: "json",
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (data) {
                getMaintenanceScenarioListData()
                maintenance_scenario_table.bootstrapTable('load', data);
                MMOUtils.hideLoader()
            },
            error: function (error) {
                MMOUtils.hideLoader()
                console.error('Error deleting scenario:', error);
            }
        });
    }
});
function multilineHeaderFormatter(value, row, index) {
    return '<div style="white-space: normal;">' + value + '</div>';
}

function radioBtnHandler(scenario_name, scenario_id) {

    // var activeValue = true;
    // if (active === 'true') {
    //     activeValue = false;
    // }

    // var inputs = {
    //     "active": activeValue,
    //     "scenario_id": scenario_id,
    //     "scenario_name": scenario_name,
    //     "type": "update_scenario_status"
    // }
    // callUpdateScenarioAPI(inputs)
}

// function callUpdateScenarioAPI(inputs) {
//     MMOUtils.showLoader();

//     $.ajax({
//         url: '/update_spend_scenario',
//         type: 'POST',
//         data: JSON.stringify(inputs),
//         dataType: "json",
//         processData: false,
//         contentType: false,
//         headers: {
//             "content-type": "application/json",
//             "cache-control": "no-cache"
//         },
//         success: function (response) {
//             MMOUtils.hideLoader();
//             maintenance_scenario_table.bootstrapTable("load", response)
//             showScenarioModel("#scenarioModal", '#scenarioModalLabel', 'Success',
//                 '.modal-body', 'Scenario status updated successfully.');
//         },
//         error: function (error) {
//             MMOUtils.hideLoader();
//             showScenarioModel("#scenarioModal", '#scenarioModalLabel', 'Error',
//                 '.modal-body', 'Error occurred while updating scenario status.');
//             console.log(error);
//         }
//     });
// }

// edit the scenario name (make editable to true for scenario name in table)
// $('#maintenance-scenario-table').on('editable-save.bs.table', function(e, field, row, rowIndex, oldValue) {
//     var inputs = {
//         "scenario_name": row.scenario_name,
//         "scenario_id": row.scenario_id,
//         "active": row.active,
//         "type": "update_scenario_name"
//     }
//     MMOUtils.showLoader();
//     $.ajax({
//         url: '/update_spend_scenario',
//         type: 'POST',
//         data: JSON.stringify(inputs),
//         dataType: "json",
//         processData: false,
//         contentType: false,
//         headers: {
//             "content-type": "application/json",
//             "cache-control": "no-cache"
//         },
//         success: function (response) {
//             MMOUtils.hideLoader();
//             if(response.status == "error") {
//                 showScenarioModel("#scenarioModal", '#scenarioModalLabel', 'Error',
//                     '.modal-body', response.message);
//             } else {
//                 maintenance_scenario_table.bootstrapTable("load", response);
//                 showScenarioModel("#scenarioModal", '#scenarioModalLabel', 'Success',
//                     '.modal-body', 'Scenario name updated successfully.');
//             }

//         },
//         error: function (error) {
//             MMOUtils.hideLoader();
//              showScenarioModel("#scenarioModal", '#scenarioModalLabel', 'Error',
//                 '.modal-body', 'Error occurred while updating scenario name.');
//             console.log(error);
//         }

//     })
// })

function showScenarioModel(modelId, modelTitleId, modelTitleText, modelMessageId, modelMessageText) {
    if (modelTitleText === 'Success') {
        $(".modal-header").addClass("btn-success").removeClass("btn-danger");
    } else {
        $(".modal-header").addClass("btn-danger").removeClass("btn-success");
    }
    $(modelId).modal('show');
    $(modelTitleId).text(modelTitleText);
    $(modelMessageId).text(modelMessageText);
}

// hide modal
$("[data-hide]").on("click", function () {
    $('#scenarioModal').modal('hide');
});



