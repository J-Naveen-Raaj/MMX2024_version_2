$(function () {

    timeperiod()
    var media_touchpoint_table;
    var individualspendTable;
    var base_spend_table;
    var group_constraints_table;
    var current_optimization_id = 1;
    var touchpoints_groups
    var ScenarioTree = {};
    var total_budget = 0;
    var alltouchpoints
    var lower_sum = '';
    var upper_sum = '';
    var base_sum = '';
    var SUBHEADERS = [{
        title: 'Spend',
        editable: true,
        custom: false,
        key: 'new'
    }];

    var HEADER_STRUCTURE = {
        "qtrly": [{
            title: 'Q1',
            key: 'Q1',
            subheaders: SUBHEADERS
        },
        {
            title: 'Q2',
            key: 'Q2',
            subheaders: SUBHEADERS
        },
        {
            title: 'Q3',
            key: 'Q3',
            subheaders: SUBHEADERS
        },
        {
            title: 'Q4',
            key: 'Q4',
            subheaders: SUBHEADERS
        },
        {
            title: 'Total',
            key: 'Total',
            subheaders: [{
                title: 'Spend',
                editable: false,
                custom: false,
                key: 'new'
            }]
        }
        ]
    };
    MMOUtils.showLoader()
    ScenarioTree = new MMOTree({
        tableNode: { 'id': "table#base_scenario_table", 'class': "simple-tree-table" },
        treeHeadNode: '.treeDataHeader',
        treeBodyNode: '.treeDatabody',
        headerStructure: HEADER_STRUCTURE,
        formatCellData: formatCellData,
        changeHandler: updateField
    });

    individualspendTable = $("#individualspendTable").bootstrapTable({
        data: [],
        columns: [
            { field: "variable_category", title: "Channel" },
            { field: "variable_description", title: "Variable Description" },
            {
                field: "period",
                title: "Period",
                formatter: function (value, row, index) {
                    var period_type = $("#period_type").val();

                    if (period_type === "quarter") {
                        return "Q" + value;
                    } else if (period_type === "month") {
                        return monthName(value);
                    } else {
                        return value; // Handle other cases if needed
                    }
                },
            },
            // { field: "period", title: "Period", formatter: function (value, row, index) { return "Q" + value } },
            // { field: "spend", title: "Base Spend", align: 'right', formatter: function (value, row, index) { return d3.format("$,.0f")(value) } },
            {
                field: "spend", title: "Base Spend", align: 'right', editable: {
                    type: 'number',
                    noeditFormatter: function (value, row, index) {
                        if (row.lock) {
                            if (value == 0) {
                                return d3.format("$,.0f")(value)
                            } else {
                                return d3.format("$,.0f")(value)
                            }
                        } else {
                            var scenario_type = $('#scenario_type').find("option:selected").data("name");
                            if (scenario_type !== "New Budget") {
                                if (value == 0) {
                                    return d3.format("$,.0f")(value)
                                } else {
                                    return d3.format("$,.0f")(value)
                                }
                            }

                            return false
                        }

                    }
                }, formatter: function (value, row, index) {
                    // return value
                    if (value == 0) {
                        return d3.format("$,.0f")(value)
                    } else {
                        return d3.format("$,.0f")(value)
                    }
                }, class: 'base_spend'
            },
            {
                field: "lock", title: "Lock", checkbox: true,
                formatter: function (value) {
                    return value
                },
            },
            {
                field: "Lower Bound %", title: "Lower Bound %", align: 'right', editable: {
                    emptytext: '----', type: 'number', step: true,
                    noeditFormatter: function (value, row, index) {
                        if (row.lock) {
                            return ''
                        }
                        return false
                    }
                }, class: 'lower_bound lower_bound_dollar'
            },
            {
                field: "Upper Bound %", title: "Upper Bound %", align: 'right',
                editable: {
                    emptytext: '----',
                    type: 'number',
                    noeditFormatter: function (value, row, index) {
                        if (row.lock) {
                            return ''
                        }
                        return false
                    }
                }, class: 'upper_bound lower_bound_dollar'
            },
            {
                field: "Lower Bound $", title: "Lower Bound $", align: 'center', class: 'lower_bound lower_values',
                editable: {
                    type: 'number',
                    noeditFormatter: function (value, row, index) {
                        if (row.lock) {
                            if (value == 0) {
                                return ''
                            } else {
                                return d3.format(",.0f")(value)
                            }
                        }
                        return false
                    }
                }, formatter: function (value, row, index) {
                    // return value
                    if (value == 0) {
                        return ''
                    } else {
                        return d3.format(",.0f")(value)
                    }
                }
            },
            {
                field: "Upper Bound $", title: "Upper Bound $", align: 'center', class: 'upper_bound upper_values',
                editable: {
                    type: 'number',
                    noeditFormatter: function (value, row, index) {
                        if (row.lock) {
                            if (value == 0) {
                                return ''
                            } else {
                                return d3.format(",.0f")(value)
                            }
                        }
                        return false
                    }
                }, formatter: function (value, row, index) {
                    // return value
                    if (value == 0) {
                        return ''
                    } else {
                        return d3.format(",.0f")(value)
                    }
                }
            },
            { field: "Lower Bound Eff", title: "LB Effective", align: 'right', formatter: function (value, row, index) { return d3.format("$,.0f")(value) } },
            { field: "Upper Bound Eff", title: "UB Effective", align: 'right', formatter: function (value, row, index) { return d3.format("$,.0f")(value) } }
        ]
    })
    function monthName(monthNumber) {
        const monthNames = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ];

        return monthNames[monthNumber - 1];
    }
    function formatCellData(cellData, roundoff) {
        return MMOUtils.commaSeparatevalue(MMOUtils.round(MMOUtils.replaceComma(cellData), 0));
    }
    function updateField(e) {
        e.preventDefault();
        ScenarioTree.cellData[e.target.name] = MMOUtils.replaceComma($(this).val());
        var objId = e.target.name.split('_')
        var total = 0;
        HEADER_STRUCTURE['qtrly'].map(function (d) {
            total += Number(MMOUtils.replaceComma($("#" + objId[0] + "_" + objId[1] + "_" + d.key + "_" + objId[3]).val()));
        })
        $("#" + objId[0] + "_" + objId[1] + "_Total_new").html(formatCellData(total.toString(), 0))
        ScenarioTree.cellData[objId[0] + "_" + objId[1] + "_Total_new"] = total.toString();
        var total_spend = Object.keys(ScenarioTree.cellData).filter(function (d) { return d.indexOf("Total") > -1 }).reduce((a, b) => Number(a) + Number(ScenarioTree.cellData[b]), 0)
        $("#total_spend").html(d3.formatPrefix("$.1", MMOUtils.round(total_spend, 0))(MMOUtils.round(total_spend, 0)).replace(/G/, "B"));
    }
    intialconfiguration()
    var uploadButton = $("#ib-browse-btn");
    var fileInfo = $("#ib-display-file");
    var fileInput = $("#importIndividualBounds");

    uploadButton.on("click", (e) => {
        e.preventDefault();
        fileInput.click();
    });

    fileInput.on("change", () => {
        var filename = fileInput.val().split(/(\\|\/)/g).pop();
        var truncated = filename.length > 50 ? filename.substr(filename.length - 50) : filename;
        fileInfo.html(truncated);
    });

    var uploadButton1 = $("#scenario-browse-btn");
    var fileInfo1 = $("#scenario-browse-file");
    var fileInput1 = $("#importScenario");

    uploadButton1.on("click", (e) => {
        e.preventDefault();
        fileInput1.click();
    });

    fileInput1.on("change", () => {
        var filename = fileInput1.val().split(/(\\|\/)/g).pop();
        var truncated = filename.length > 50 ? filename.substr(filename.length - 50) : filename;
        fileInfo1.html(truncated);
    });


    $('#group_name_mtp_save').click(function () {
        var group_name_mtp = $('#group_name_mtp').val();
        var val = [];
        $(':checkbox:checked').each(function (i) {
            val[i] = $(this).val();
        });
        if (!group_name_mtp) {
            $(".mtgroup_error").show();
            $(".mtgroup_error").html("Fill Groupname");
            return false;
        }

        if (val.length == 0) {
            $(".mtgroup_error").show();
            $(".mtgroup_error").html("Check Groupname listed below");
            return false;
        }
        $(".mtgroup_error").hide();
    });
    function createLabel(text, classname) {
        const label = $("<div>").text(text).addClass(classname);
        return label;
    }

    function addLowerandUpperLabels(lower_sum, upper_sum, base_sum = '') {
        lower_sum = d3.format("$,")(lower_sum)
        upper_sum = d3.format("$,")(upper_sum)
        base_sum = d3.format("$,")(base_sum)
        const lowerBoundLabel = createLabel(lower_sum, "lower_label");
        const upperBoundLabel = createLabel(upper_sum, "upper_label");
        const basespendLabel = createLabel(base_sum, "basespend_label");
        const totallablel = createLabel("Total", "total_lablel")
        if ($('#individualspendTable thead tr th[data-field="Lower Bound Eff"] .lower_label').length > 0) {
            $('#individualspendTable thead tr th[data-field="Lower Bound Eff"] .lower_label').remove();
            // $('#individualspendTable thead tr th.lower_bound.lower_values .lower_label').val(lower_sum);
        }
        $('#individualspendTable thead tr th[data-field="Lower Bound Eff"]').append(lowerBoundLabel);
        if ($('#individualspendTable thead tr th[data-field="Upper Bound Eff"] .upper_label').length > 0) {
            $('#individualspendTable thead tr th[data-field="Upper Bound Eff"] .upper_label').remove();

        }

        $('#individualspendTable thead tr th[data-field="Upper Bound Eff"]').append(upperBoundLabel);
        if ($('#individualspendTable thead tr th.base_spend').length > 0) {
            $('#individualspendTable thead tr th.base_spend .basespend_label').remove();

        }

        $("#individualspendTable thead tr th.base_spend").append(basespendLabel);
        $("#individualspendTable thead tr th[data-field='variable_category']").append(totallablel);
    }

    $('.group_constraints_list').click(function () {
        MMOUtils.showLoader()
        $('.optimization_spend_constraint_import').hide();
        var Stringparams = `scenario_id=${current_optimization_id}`
        $.ajax({
            url: '/getGroupConstraints?' + Stringparams,
            type: 'GET',
            dataType: "json",
            headers: {
                "cache-control": "no-cache"
            },
            success: function (response) {
                group_constraints_table = $("#group_constraints_table").bootstrapTable({
                    data: response,
                    columns: [{ field: "name", title: 'Variable Group' },
                    {
                        field: "period", title: "Period", formatter: function (value, row, index) {
                            if (value == 'Overall') {
                                return value
                            } else {
                                if (row.period_type == "month") {
                                    var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                                    var monthIndex = parseInt(value) - 1; // Adjust for zero-based index
                                    return monthNames[monthIndex];
                                }
                                else {
                                    return "Q" + value;
                                }
                            }
                        }
                    },
                    {
                        field: "constraint_type", title: "Constraint Type",
                        formatter: function (value, row, index) {
                            if (value === 'Cap') {
                                return 'Max'
                            } else {
                                return value;
                            }
                        }
                    },
                    { field: "value", title: "Value", formatter: function (value, row, index) { return d3.format("$,.2f")(value) } },
                    { field: "remove", formatter: function (value, row, index) { return '<b class="remove_icon"><i class="fa fa-trash" aria-hidden="true"></i></b>' }, class: "remove_data" }
                    ],
                })
                MMOUtils.hideLoader();
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });

    });

    $('.individualspend_list').click(function () {
        $('.optimization_spend_constraint_import').show();
    });

    $("#sc_managegroups").on('shown.bs.modal', function () {
        MMOUtils.showLoader()
        $.ajax({
            url: '/getMediaTouchpointGroupsList',
            type: 'GET',
            dataType: "json",
            processData: false,
            contentType: false,
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                // get the required response to update the select box
                manageTouchpointGroups(response);
                MMOUtils.hideLoader()
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
    })

    $("#add_group").on('shown.bs.modal', function () {
        get_base_spend_for_touch_points();
    })

    $('#touchpointGroups_2').on('change', function () {
        get_base_spend_for_touch_points()
    })
    $('#gc-period').on('change', function () {
        get_base_spend_for_touch_points()

    })
    $('#managegrpBtn').click(function () {
        $("#sc_managegroups").modal('show');
    });

    $("#sc_managegroups").on('hidden.bs.modal', function () {
        $(".modal-backdrop").remove();
    });
    $("#add_group").on('hidden.bs.modal', function () {
        $(".modal-backdrop").remove();
    });
    $('#addGroupBtn').click(function () {
        $("#add_group").modal('show');
    });
    function get_base_spend_for_touch_points() {
        MMOUtils.showLoader()
        var base_scenario_id = $("#base_scenario").val();
        var period_type = $("#period_type").val() || 'quarter';
        var grp_period = $("#gc-period").val();
        if (period_type == 'quarter') {
            var period_start = $("#period_start").val() || 1;
            var period_end = $("#period_end").val() || 4;
            if (grp_period == "Select") {
                grp_period = period_start
            }
        }
        else {
            var period_start = $("#monthddl1").val()
            var period_end = $("#monthddl2").val()
            if (grp_period == "Select") {
                grp_period = period_start
            }
        }
        var touchpoint_groups_id = $('#touchpointGroups_2').val();
        $.ajax({
            url: '/get_base_spend_value_for_group_constraints?base_scenario_id=' + base_scenario_id + '&touchpoint_groups_id=' + touchpoint_groups_id + '&period_type=' + period_type + '&period_start=' + period_start + '&period_end=' + period_end + '&grp_period=' + grp_period,
            type: 'GET',
            dataType: "json",
            processData: false,
            contentType: false,
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                if (response && response.message === 'No variable node mapping found for the given touchpoint group') {
                    $("#status_message").text(response.message);
                    $('#app_status').modal('show');
                } else {
                    if (response && response.length !== 0) {
                        $('#base_spend_value').val(d3.format(",.2f")(response[0]['base_spend']))
                    } else {
                        $("#status_message").text("No base spend found for the selected touchpoint group");
                        $('#app_status').modal('show');
                    }
                }
                MMOUtils.hideLoader();
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
    }

    $("#modalscenarioslist").on("change", function () {
        var selected_scenario = $(this).val();
        $("#base_scenario_table").bootstrapTable('destroy');
        $.ajax({
            url: '/getSpendScenarioGranularLevel',
            type: 'POST',
            data: JSON.stringify({ scenario_id: selected_scenario }),
            dataType: "json",
            processData: false,
            contentType: false,
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                // get the required response to update the select box
                ScenarioTree.refreshTable(response, 'qtrly', "new");
                var total_spend = response.reduce((a, b) => Number(a) + Number(b.Total), 0);
                $("#total_spend").html(d3.formatPrefix("$.1", MMOUtils.round(total_spend, 0))(MMOUtils.round(total_spend, 0)).replace(/G/, "B"));
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });

    })

    $("#scenario_type").change(function () {
        var scenario_type = $(this).find("option:selected").data("name");
        $("#budget_type").html(scenario_type);

        if (scenario_type == "Base Budget") {
            $("#budget_value").attr('readonly', true);
            $("#budget_value").removeClass('budget_format');
            $("#budget_value").val(d3.format("$,.0f")(total_budget));
            $("#total_budget").val(d3.format("$,.0f")(total_budget));
        }
        else if (scenario_type == "New Budget") {
            $("#budget_value").attr('readonly', false);
            $("#budget_value").val(d3.format("$,.0f")(0));
            $("#budget_value").addClass('budget_format');
            var budget = Number(MMOUtils.replaceComma($("#budget_value").val()).replace("$", ""));
            $("#total_budget").val(d3.format("$,.0f")(budget));
        }
        else {
            $("#budget_value").attr('readonly', false);
            $("#budget_value").addClass('budget_format');
            var incremental_budget = Number(MMOUtils.replaceComma($("#budget_value").val()).replace("$", ""));
            $("#total_budget").val(d3.format("$,.0f")(incremental_budget + total_budget));
        }

    })

    $("#budget_value").on("change", function () {
        // var scenario_type = $(this).find("option:selected").data("name");
        var scenario_type = $('#scenario_type').find("option:selected").data("name");
        if (scenario_type == "Base Budget") {
            $("#budget_value").attr('readonly', true);
            $("#budget_value").val(d3.format("$,.0f")(total_budget));
            $("#total_budget").val(d3.format("$,.0f")(total_budget));
        }
        else if (scenario_type == "New Budget") {
            $("#budget_value").attr('readonly', false);
            var budget = Number(MMOUtils.replaceComma($("#budget_value").val()).replace("$", ""));
            $("#total_budget").val(d3.format("$,.0f")(budget));
        }
        else {
            $("#budget_value").attr('readonly', false);
            incremental_budget = Number(MMOUtils.replaceComma($("#budget_value").val()).replace("$", ""));
            $("#total_budget").val(d3.format("$,.0f")(incremental_budget + total_budget));
        }
    })
    $("#period_type").on("change", function () {
        var period_type = $(this).val();
        updateOptions(period_type);
        if (period_type == "month") {
            $(".quarterddl-item").hide();
            $(".monthddl-item").show();
        }
        else {
            $(".quarterddl-item").show();
            $(".monthddl-item").hide();
        }
    })
    $("#base_scenario,#period_start,#period_end,#monthddl1,#monthddl2,#period_type").change(function () {
        MMOUtils.showLoader();
        var scenario_id = $("#base_scenario").val();
        var period_type = $("#period_type").val() || 'quarter';
        if (period_type == 'quarter') {
            var period_start = $("#period_start").val() || 1;
            var period_end = $("#period_end").val() || 4;
        }
        else {
            var period_start = $("#monthddl1").val()
            var period_end = $("#monthddl2").val()
        }
        var queryString = `scenario_id=${scenario_id}&period_type=${period_type}&period_start=${period_start}&period_end=${period_end}`
        $.ajax({
            url: '/get_base_scenario_budget?' + queryString,
            type: 'GET',
            dataType: "json",
            headers: {
                "cache-control": "no-cache"
            },
            success: function (response) {
                $("#opt_scenario_name").attr('readonly', false).addClass('inputscenario');
                $("#opt_scenario_name").parent().addClass('inputscenario');
                $('#scenario_type').prop('disabled', false).selectpicker('refresh');
                $('#outcome_to_maximum').prop('disabled', false).selectpicker('refresh');
                $('#create_scenario').prop('disabled', false)
                $('#period_year').prop('disabled', false).selectpicker('refresh');
                $("#period_year").find('option[value="2022"]').attr('selected', 'selected')
                $("#period_year").selectpicker("refresh");
                $('#period_start').prop('disabled', false).selectpicker('refresh');
                $('#period_end').prop('disabled', false).selectpicker('refresh');
                $("#period_start").find('option[value="1"]').attr('selected', 'selected')
                $("#period_start").selectpicker("refresh");
                $("#period_end").find('option[value="4"]').attr('selected', 'selected')
                $("#period_end").selectpicker("refresh");
                $("#period_type").prop('disabled', false).selectpicker('refresh');
                $("#period_type").find('option[value="quarter"]').attr('selected', 'selected')
                $("#period_type").selectpicker("refresh");
                $("#period_year").find('option[value="2024"]').attr('selected', 'selected')
                $("#period_year").selectpicker("refresh");
                total_budget = response.total_budget;
                var scenario_type = $("#scenario_type").find("option:selected").data("name")
                $("#base_budget_value").val(d3.format("$,.0f")(total_budget));
                if (scenario_type == "Base Budget") {
                    $("#budget_value").attr('readonly', true);
                    $("#budget_value").val(d3.format("$,.0f")(total_budget));
                    $("#total_budget").val(d3.format("$,.0f")(total_budget));
                }
                else if (scenario_type == "New Budget") {
                    $("#budget_value").attr('readonly', false);
                    var budget = 0;
                    $("#budget_value").val(d3.format("$,.0f")(budget));
                    $("#total_budget").val(d3.format("$,.0f")(budget));
                }
                else {
                    $("#budget_value").attr('readonly', false);
                    var incremental_budget = Number(MMOUtils.replaceComma($("#budget_value").val()).replace("$", ""));
                    $("#total_budget").val(d3.format("$,.0f")(incremental_budget + total_budget));
                }
                MMOUtils.hideLoader();
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        })
    })

    $("#create_scenario").on("click", function () {
        var scenario_name = $("#opt_scenario_name").val();
        var optimization_type = $("#scenario_type").val();
        var period_type = $("#period_type").val();
        var year = $("#period_year").val();
        if (period_type == 'quarter') {
            var period_start = $("#period_start").val();
            var period_end = $("#period_end").val();
        }
        else {
            var period_start = $("#monthddl1").val()
            var period_end = $("#monthddl2").val()
        }
        var base_scenario = $("#base_scenario").val();
        var outcome_to_maximum = $("#outcome_to_maximum").val();
        var base_budget = $("#base_budget_value").val();
        var budget = $("#budget_value").val();
        var total_budget = $("#total_budget").val();

        var same_scenario_name_repeat = false;

        $("#base_scenario > option").each(function () {
            if ($(this).text().toLowerCase().trim() === scenario_name.toLowerCase().trim()) {
                same_scenario_name_repeat = true;
                $('#app_status').modal('show');
                $("#status_message").text("Same scenario name already exists. Please change and try again.");
            }
        });

        var inputs = {};
        inputs.scenario_name = scenario_name;
        inputs.scenario_type = optimization_type;
        inputs.year = year;
        inputs.period_start = period_start;
        inputs.period_end = period_end;
        inputs.period_type = period_type;
        inputs.base_scenario = base_scenario;
        inputs.outcome_to_maximum = outcome_to_maximum;

        var scenario_type = $("#scenario_type").find("option:selected").data("name")
        if (scenario_type == "Base Budget") {
            inputs.incremental_budget = 0;
            inputs.budget = Number(MMOUtils.replaceComma(base_budget).replace("$", ""));
            inputs.total_budget = Number(MMOUtils.replaceComma(total_budget).replace("$", ""));
        }
        else if (scenario_type == "New Budget") {
            inputs.incremental_budget = 0
            inputs.budget = Number(MMOUtils.replaceComma(budget).replace("$", ""));;
            inputs.total_budget = Number(MMOUtils.replaceComma(budget).replace("$", ""));;
        }
        else {
            inputs.budget = Number(MMOUtils.replaceComma(base_budget).replace("$", ""));;
            inputs.incremental_budget = Number(MMOUtils.replaceComma(budget).replace("$", ""));
            inputs.total_budget = inputs.budget + inputs.incremental_budget;
        }
        if (parseInt(period_end) < parseInt(period_start)) {
            MMOUtils.hideLoader()
            $('#app_status').modal('show');
            $("#status_message").text("Please select a valid range from the drop downs.");
            return;
        }
        if ($("#runscenario_form")[0].checkValidity() && !same_scenario_name_repeat) {
            MMOUtils.showLoader()
            var userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            inputs.userTimezone = userTimezone
            $.ajax({
                url: '/create_optimization_scenario',
                type: 'POST',
                dataType: "json",
                data: JSON.stringify(inputs),
                processData: false,
                contentType: false,
                headers: {
                    "content-type": "application/json",
                    "cache-control": "no-cache"
                },
                success: function (response) {
                    $('#importIndividualBoundsBtn').prop('disabled', false)
                    $('#ib-browse-btn').prop('disabled', false)
                    current_optimization_id = response.optimization_scenario_id;
                    var period = response.spend_bounds[0].period_type
                    $("#sample_import").html("<a class='btn waves-effect waves-light btn-rounded button-green' href='/download_individual_spend_bounds?optim-id=" + response.optimization_scenario_id + "&period_type=" + period + "&period_start=" + inputs.period_start + "&period_end=" + inputs.period_end + " ' download>Download Sample</a>")
                    // response.spend_bounds.sort(function (a, b) {
                    //     node1 = a.variable_description.toLowerCase();
                    //     node2 = b.variable_description.toLowerCase();
                    //     return (node1 < node2) ? -1 : (node1 > node2) ? 1 : 0;
                    // });
                    updateOptions(inputs.period_type)
                    group_cons_list(inputs.period_start, inputs.period_end);
                    $("#gc-period").selectpicker("refresh");
                    $("#run_scenario").prop("disabled", false)
                    lower_sum = response.lower_bound_sum
                    upper_sum = response.upper_bound_sum
                    base_sum = response.base_spend_sum
                    individualspendTable.bootstrapTable("load", response.spend_bounds);
                    // var lowerBoundCell = $('#individualspendTable th[data-field="Lower Bound $"]');
                    // lowerBoundCell.find('.th-inner').html("Lower Bound $<br>" + lower_sum);

                    // // Update the title of the "Upper Bound $" cell
                    // var upperBoundCell = $('#individualspendTable th[data-field="Upper Bound $"]');
                    // upperBoundCell.find('.th-inner').html("Upper Bound $<br>" + upper_sum);
                    addLowerandUpperLabels(lower_sum, upper_sum, base_sum)
                    MMOUtils.hideLoader();
                },
                error: function (error) {
                    MMOUtils.hideLoader();
                }
            });
        }
        else {
            $("#runscenario_form")[0].reportValidity();
        }
    })

    $("#importIndividualBoundsBtn").on("click", function () {
        $(".preloader").show();
        var formData = new FormData();
        var period_type = $("#period_type").val();
        var file = $('#importIndividualBounds')[0].files[0];
        formData.append('file', file);
        formData.append('scenario_id', current_optimization_id);
        formData.append('period_type', period_type)
        formData.append('base_sum', base_sum);
        $.ajax({
            url: "/import_individual_spend_bounds",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            dataType: "json",
            success: function (response) {
                response.data.map(function (d) {
                    if (d["lock"] == 'Yes') {
                        d["lock"] = true
                    } else {
                        d["lock"] = false
                    }
                })
                response.data.sort(function (a, b) {
                    node1 = a.variable_description.toLowerCase();
                    node2 = b.variable_description.toLowerCase();
                    return (node1 < node2) ? -1 : (node1 > node2) ? 1 : 0;
                });
                individualspendTable.bootstrapTable("load", response.data);
                lower_sum = response.lower_sum
                upper_sum = response.upper_sum
                base_sum = response.base_sum
                // var lowerBoundCell = $('#individualspendTable th[data-field="Lower Bound $"]');
                // lowerBoundCell.find('.th-inner').html("Lower Bound $<br>" + lower_sum);

                // // Update the title of the "Upper Bound $" cell
                // var upperBoundCell = $('#individualspendTable th[data-field="Upper Bound $"]');
                // upperBoundCell.find('.th-inner').html("Upper Bound $<br>" + upper_sum);
                addLowerandUpperLabels(lower_sum, upper_sum, base_sum)
                $(".preloader").hide();
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
    })

    $("#touchpointGroups").on("change", function () {
        var selected_group = $(this).val();
        var StringParams = `group=${selected_group}`
        $.ajax({
            url: "/getGroupTouchpoints?" + StringParams,
            type: "GET",
            dataType: "json",
            success: function (response) {

                var OpHtml = ""
                $.map(response["included_touchpoints"], function (v) {

                    OpHtml += "<option value='" + v["variable_id"] + "'>" + v["variable_description"] + "</option>";
                });
                $("#touchpointListAdded").html(OpHtml);

                var OpHtml = ""
                $.map(response["excluded_touchpoints"], function (v) {
                    OpHtml += "<option value='" + v["variable_id"] + "'>" + v["variable_description"] + "</option>";
                });
                $("#touchpointListAvailable").html(OpHtml);

                $('.btn-group-vertical button').attr('disabled', 'disabled');
                $("#SaveGroup").prop('disabled', true);
            }
        })
    })

    $("#group_name").on("input", function () {
        $("#touchpointGroups").val('');
        $('#touchpointGroups').selectpicker('refresh');
        $('.btn-group-vertical button').removeAttr('disabled');
        $("#SaveGroup").prop('disabled', false);
        $("#touchpointListAdded").html("");
        var OpHtml = ""
        $.each(alltouchpoints, function (i, v) {
            OpHtml += "<option value='" + i + "'>" + v + "</option>";
        });
        $("#touchpointListAvailable").html(OpHtml);
        $('.multiselect').multiselect();

    })

    function manageTouchpointGroups(data) {

        MMOUtils.buildDDlFromListWithNoSelect("#touchpointGroups", data["touchpoint_groups"], "");

        $('#touchpointGroups').selectpicker('refresh');
        alltouchpoints = data["touchpoints"];
        var OpHtml = ""
        $.each(data["touchpoints"], function (i, v) {
            OpHtml += "<option value='" + i + "'>" + v + "</option>";
        });
        $("#touchpointListAvailable").html(OpHtml);
        $('.multiselect').multiselect();
    }

    $("#SaveGroup").on("click", function () {
        var group_name = $("#group_name").val().trim();
        var touchpoints = [];
        var duplicate_group_name = false;
        $('#touchpointListAdded option').each(function () {
            touchpoints.push($(this).val());
        });

        $("#touchpointGroups option").each(function () {
            if ($(this).text().toLowerCase() === group_name.toLowerCase()) {
                duplicate_group_name = true;
                $('#app_status').modal('show');
                $("#status_message").text("This touchpoint group name already exists.Please change and save again.");
                return;
            }
        })

        if (!duplicate_group_name) {
            $.ajax({
                url: '/saveGroupTouchpoints',
                type: 'POST',
                dataType: "json",
                data: JSON.stringify({ "group_name": group_name, "touchpoints": touchpoints }),
                processData: false,
                contentType: false,
                headers: {
                    "content-type": "application/json",
                    "cache-control": "no-cache"
                },
                success: function (response) {
                    $("#sc_managegroups").modal('hide');
                    $('#app_status').modal('show');
                    $("#status_message").text("Successfully added a new touchpoint group.");
                    MMOUtils.buildDDlFromListWithNoSelect("#touchpointGroups", response, "");
                    MMOUtils.buildDDlFromListWithNoSelect("#touchpointGroups_2", response, "");
                    $('#touchpointGroups').selectpicker('refresh');
                    $('#touchpointGroups_2').selectpicker('refresh');

                    // clear the existing values field
                    $("#group_name").val("");
                    $("#touchpointListAdded").html("");
                },
                error: function (error) {
                    MMOUtils.hideLoader();
                }
            });
        }
    })
    $('.error_group').hide();
    $('#gc-budget-value').keypress(function () {
        var charCode = (event.which) ? event.which : event.keyCode;
        var selected_gc_btn = $('[name=gc-radio-btn]:checked').val();
        if (selected_gc_btn === 'by_percentage') {
            if (charCode != 46 && charCode > 31
                && (charCode < 48 || charCode > 57) && charCode != 45)
                return false;
            return true;
        } else {
            if (charCode != 46 && charCode > 31
                && (charCode < 48 || charCode > 57))
                return false;
            return true;
        }
    });

    $('#gc-budget-value').blur(function () {
        var budget_val = $(this).val() // get the current value of the input field.
        budget_val = d3.format(",.2f")(budget_val)
        $(this).val(budget_val)
        var calculated_spend = 0
        var base_spend = $('#base_spend_value').val();
        var group_constraint_value = $('#gc-budget-value').val()
        base_spend = parseFloat(base_spend.replace(/,/g, ""))
        group_constraint_value = parseFloat(group_constraint_value.replace(/,/g, ""))
        if ($('[name=gc-radio-btn]:checked').val() === 'by_percentage') {
            calculated_spend = base_spend + ((base_spend * group_constraint_value) / 100)
            $('#gc-calculated-value').val(d3.format(",.2f")(calculated_spend))
        } else {
            calculated_spend = group_constraint_value
            $('#gc-calculated-value').val(d3.format(",.2f")(calculated_spend))
        }
    });

    $('#gc-budget-value').focus(function () {
        var budget_val = $(this).val() // get the current value of the input field.
        $(this).val(budget_val.replace(/,/g, ""))
    });

    $('.gc-amount').on('change', function () {
        $('#gc-budget-value').val(0)
        $('#gc-calculated-value').val(0)
    })

    $("#AddGroupConstraint").on("click", function () {
        var inputs = {}
        var period_type = $("#period_type").val();
        inputs.optimization_scenario_id = current_optimization_id
        inputs.group_id = $("#touchpointGroups_2").val();
        inputs.period = $("#gc-period").val();
        inputs.constraint_type = $("#gc-constraint-type").val();
        //        inputs.budget_value = $("#gc-budget-value").val();
        inputs.budget_value = $("#gc-calculated-value").val().replace(/,/g, "");
        inputs.period_type = period_type

        if (inputs.budget_value < 0) {
            $('.error_group').show();
            return false;

        } else {
            $('.error_group').hide();
        }
        $.ajax({
            url: '/addGroupConstraint',
            type: 'POST',
            dataType: "json",
            data: JSON.stringify(inputs),
            processData: false,
            contentType: false,
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                $("#add_group").modal('hide');
                $('#app_status').modal('show');
                $("#status_message").text("Successfully added a group constraint.");
                group_constraints_table.bootstrapTable("load", response);
                $('#gc-budget-value').val(0)
                $('#gc-calculated-value').val(0)
                $("#gc_value").prop("checked", true);
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
    })

    $("#importSampleData").on("click", function () {
        var scenario_id = $("#modalscenarioslist").val()
        if (scenario_id === '') {
            $('#app_status').modal('show');
            return $("#status_message").text("Please select a base scenario");
        }
        document.location.href = "/download_base_scenario?scenario_id=" + scenario_id;
    })

    $("#importScenarioBtn").on("click", function () {
        $(".preloader").show();
        var formData = new FormData();
        var file = $('#importScenario')[0].files[0];
        formData.append('file', file);
        formData.append('scenario_id', current_optimization_id);
        $.ajax({
            url: "/optimization_import_scenario_spends",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            dataType: "json",
            success: function (response) {
                ScenarioTree.refreshTable(response, 'qtrly', "new");
                var total_spend = response.reduce((a, b) => Number(a) + Number(b.Total), 0);
                $("#total_spend").html(d3.formatPrefix("$.1", MMOUtils.round(total_spend, 0))(MMOUtils.round(total_spend, 0)).replace(/G/, "B"));
                $(".preloader").hide();
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
    })

    $("#save_scenario").on("click", function () {
        var scenario_name = $("#scenario_saveas").val();
        var inputs = {}
        inputs.scenario_name = scenario_name
        inputs.data = ScenarioTree.cellData
        if ($("#new_base_scenario_form")[0].checkValidity()) {
            MMOUtils.showLoader();
            $.ajax({
                url: "/optimization_create_base_scenario",
                type: "POST",
                data: JSON.stringify(inputs),
                processData: false,
                contentType: false,
                dataType: "json",
                headers: {
                    "content-type": "application/json",
                    "cache-control": "no-cache"
                },
                success: function (response) {
                    MMOUtils.buildDDlFromListWithNoSelect("#base_scenario", response, "");
                    MMOUtils.buildDDlFromListWithNoSelect("#modalscenarioslist", response, "");
                    $("#base_scenario").selectpicker("refresh");
                    $("#modalscenarioslist").selectpicker("refresh");
                    $("#new_base_scenario_modal").modal('hide');
                    $('#scenario_saveas').val("")
                    MMOUtils.hideLoader();
                    $('#app_status').modal('show');
                    $("#status_message").text("Successfully created and ran a new base scenario.");
                },
                error: function (error) {
                    MMOUtils.hideLoader();
                }
            });
        }
        else {
            $("#new_base_scenario_form")[0].reportValidity();
        }
    })

    $("#opt_scenarios").on("change", function () {

        var opt_scenario_id = $(this).val();
        var Stringparams = `scenario_id=${opt_scenario_id}`
        $.ajax({
            url: "/get_optimization_scenario_details?" + Stringparams,
            type: "GET",
            dataType: "json",
            success: function (data) {
                data.map(function (d) {
                    $("#scenario_type").selectpicker('val', d["optimization_type_id"]);
                    $("#period_year").selectpicker('val', d["period_year"]);
                    $("#period_start").selectpicker('val', d["period_start"]);
                    $("#period_end").selectpicker('val', d["period_end"]);
                    $("#base_scenario").selectpicker('val', d["base_scenario_id"]);
                    $("#outcome_to_maximum").selectpicker('val', d["outcome_maximize"]);
                    $("#budget_value").val(d["base_budget"]);
                    $("#total_budget").val(d["total_budget"]);
                    $("#scenario_type").trigger("change")
                })
            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
    })

    $("#run_scenario").on("click", function () {
        //var opt_scenario_id = 1;
        MMOUtils.showLoader()
        var statusCheckInterval
        function checkScenarioStatus() {
            $.ajax({
                url: "/optimization_scenario_status",
                type: "GET",
                data: { "optimization_scenario_id": current_optimization_id },
                dataType: "json",
                headers: {
                    "content-type": "application/json",
                    "cache-control": "no-cache"
                },
                success: function (data) {
                    if (data.status === "Completed") {
                        clearInterval(statusCheckInterval);  // Stop checking once completed
                        $(".preloader").hide();
                        MMOUtils.hideLoader();
                    } else if (data.status === "Failed") {
                        clearInterval(statusCheckInterval);  // Stop checking on failure too
                        $(".preloader").hide();
                    }
                }
            });

        }
        $.ajax({
            url: "/run_scenario_optimization",
            type: "POST",
            data: JSON.stringify({ "optimization_scenario_id": current_optimization_id }),
            processData: false,
            contentType: false,
            dataType: "json",
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            beforeSend: function () {
                $(".preloader").show();

            },
            success: function (data) {
                statusCheckInterval = setInterval(checkScenarioStatus, 20000);
                setTimeout(function () {
                    clearInterval(statusCheckInterval);  // Stop checking after 1 minutes
                    $(".preloader").hide();
                    $('#app_status').modal('show');
                    $("#status_message").text("Optimization in progress, please check in scenario comparision after 5 min.");
                    $('#app_status').on('hidden.bs.modal', function () {
                        location.reload(true); // true forces a reload from the server, not from the cache
                    });
                }, 60000);
            },
            error: function (xhr) {
                $(".preloader").hide();
            },
        })
    });

    // $("#opt_scenarios_new").on("change", function () {
    //     $.ajax({
    //         url: "/get_optimization_scenario_outcome_results",
    //         type: "POST",
    //         data: JSON.stringify({ "optimization_scenario_id": $(this).val() }),
    //         processData: false,
    //         contentType: false,
    //         dataType: "json",
    //         headers: {
    //             "content-type": "application/json",
    //             "cache-control": "no-cache"
    //         },
    //         success: function (response) {
    //             create_optimization_outcomes(response["outcomes"], response['scenarioNames']);
    //             create_optimization_summary(response["summary"]);
    //         }
    //     })
    // })

    // function create_optimization_outcomes(response, scenarioNames) {
    //     $("#optimization_outcomes").html("")
    //     var base_scenario_name = "Base Scenario (" + scenarioNames[0]['base'] + ")"
    //     var optimized_scenario_name = "Optimized Scenario (" + scenarioNames[0]['optim'] + ")"
    //     /*
    //     changes: Mayank Prakash on 09/28/2022
    //     added O_TOTALASSET_IN for KPI outcome calculation
    //     */
    //     var customer_names = {
    //         'O_EXASSET_IN': "Existing Assets In", 'O_NTFHH_CNT': "NTF HH Count",
    //         'O_NTFASSET_IN': "NTF Assets In", 'O_TOTALASSET_IN': "Total Assets In"
    //     }
    //     var base_data = response.filter(function (d) { return d["name"] == "Base" });
    //     var Optimized_data = response.filter(function (d) { return d["name"] == "Optimized" });
    //     var data = [];
    //     base_data.map(function (d) {
    //         d["BS-Base"] = parseInt(d["BaseAttribution"])
    //         d["BS-Marketing"] = parseInt(d["MarketingAttribution"])
    //         d["BS-Total"] = parseInt(d["Total"])
    //         var temp = Optimized_data.filter(function (o) { return o["Outcome"] == d["Outcome"] && o["Segment"] == d["Segment"] })
    //         d["OS-Base"] = parseInt(temp[0]["BaseAttribution"])
    //         d["OS-Marketing"] = parseInt(temp[0]["MarketingAttribution"])
    //         d["OS-Total"] = parseInt(temp[0]["Total"])
    //     });
    //     var outcomes = d3.map(response, function (d) { return d["Outcome"] }).keys();
    //     function totalTextFormatter(data) {
    //         return 'Total'
    //     }

    //     function totalNameFormatter(data) {
    //         return data.length
    //     }

    //     function totalPriceFormatter(data) {
    //         var field = this.field
    //         return cellformatter(data.map(function (row) {
    //             return +row[field]
    //         }).reduce(function (sum, i) {
    //             return sum + i
    //         }, 0))
    //     }

    //     function totalFormatter(data) {
    //         var field = this.field
    //         return cellNumberformatter(data.map(function (row) {
    //             return +row[field]
    //         }).reduce(function (sum, i) {
    //             return sum + i
    //         }, 0))
    //     }

    //     function cellStyle(value, row, index) {
    //         if (row['OS-Base'] > row['BS-Base']) {
    //             return { classes: 'green' }
    //         } else if (row['BS-Base'] == row['OS-Base']) {
    //             return { classes: 'equal' }
    //         } else {
    //             return { classes: 'danger' }
    //         }
    //     }
    //     function cellStyle2(value, row, index) {

    //         if (row['OS-Marketing'] > row['BS-Marketing']) {
    //             return { classes: 'green' }
    //         } else if (row['BS-Marketing'] == row['OS-Marketing']) {
    //             return { classes: 'equal' }
    //         } else {
    //             return { classes: 'danger' }
    //         }

    //     }
    //     function cellStyle3(value, row, index) {
    //         if (row['OS-Total'] > row['BS-Total']) {
    //             return { classes: 'green' }
    //         } else if (row['BS-Total'] == row['OS-Total']) {
    //             return { classes: 'equal' }
    //         } else {
    //             return { classes: 'danger' }
    //         }

    //     }
    //     function cellformatter(data) {
    //         return d3.format("$,.0f")(data)
    //     }
    //     function cellNumberformatter(data) {
    //         return d3.format(",.0f")(data)
    //     }

    //     outcomes.map(function (d) {
    //         $("#optimization_outcomes").append("<div class='card col-12'> <h5 class='card-title'>" + customer_names[d] + "</h5><table id=" + d + "></div></div>");
    //         var columns = {
    //             "spends": [
    //                 [{ field: "Segment", title: "Segment", rowspan: 2, footerFormatter: totalTextFormatter },
    //                 { field: "Base Scenario", title: base_scenario_name, colspan: 3, align: 'center' },
    //                 { field: "Optimized Scenario", title: optimized_scenario_name, colspan: 3, align: 'center' }],
    //                 [
    //                     { field: "BS-Base", title: "Base Attribution", falign: "right", formatter: cellformatter, footerFormatter: totalPriceFormatter },
    //                     { field: "BS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellformatter, footerFormatter: totalPriceFormatter },
    //                     { field: "BS-Total", title: "Total", falign: "right", formatter: cellformatter, footerFormatter: totalPriceFormatter },
    //                     { field: "OS-Base", title: "Base Attribution", falign: "right", formatter: cellformatter, cellStyle: cellStyle, footerFormatter: totalPriceFormatter },
    //                     { field: "OS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellformatter, cellStyle: cellStyle2, footerFormatter: totalPriceFormatter },
    //                     { field: "OS-Total", title: "Total", falign: "right", formatter: cellformatter, cellStyle: cellStyle3, footerFormatter: totalPriceFormatter },
    //                 ]
    //             ], "counts": [
    //                 [{ field: "Segment", title: "Segment", rowspan: 2, footerFormatter: totalTextFormatter },
    //                 { field: "Base Scenario", title: base_scenario_name, colspan: 3, align: 'center' },
    //                 { field: "Optimized Scenario", title: optimized_scenario_name, colspan: 3, align: 'center' }],
    //                 [
    //                     { field: "BS-Base", title: "Base Attribution", falign: "right", formatter: cellNumberformatter, footerFormatter: totalFormatter },
    //                     { field: "BS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellNumberformatter, footerFormatter: totalFormatter },
    //                     { field: "BS-Total", title: "Total", falign: "right", formatter: cellNumberformatter, footerFormatter: totalFormatter },
    //                     { field: "OS-Base", title: "Base Attribution", falign: "right", formatter: cellNumberformatter, cellStyle: cellStyle, footerFormatter: totalFormatter },
    //                     { field: "OS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellNumberformatter, cellStyle: cellStyle2, footerFormatter: totalFormatter },
    //                     { field: "OS-Total", title: "Total", falign: "right", formatter: cellNumberformatter, cellStyle: cellStyle3, footerFormatter: totalFormatter },
    //                 ]
    //             ]
    //         }

    //         $("#" + d).bootstrapTable('destroy').bootstrapTable({
    //             classes: "table table-hover table-bordered",
    //             showFooter: "true",
    //             data: base_data.filter(function (c) { return c["Outcome"] == d }),
    //             columns: d == "O_NTFHH_CNT" ? columns["counts"] : columns["spends"]
    //         })

    //     })
    // }
    // function create_optimization_summary(response) {
    //     $("#optimization_summary").html("")
    //     var htmlTemplate = "";
    //     response.map(function (data, index) {
    //         htmlTemplate += '<div id="opt_sum_' + index + '" class="col-md-12"><div class="row"><div class="col summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t500 text-normal">&nbsp;</div></div><div class="px-0 center"><div class="row"><div class="col-12"><h2 class="green spendTxt"><span>' + data["summary_name"] + '</span>' + '</h2></div></div></div></div></div>';
    //         htmlTemplate += '<div class="col summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t500 text-normal">Base Spend</div></div><div class="px-0 center"><div class="row"><div class="col-12"><h2 class="green spendTxt">' + d3.format("$,.0f")(data["base_spend"]) + '</h2></div></div></div></div></div>';
    //         htmlTemplate += '<div class="col summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t500 text-normal">Optimized Spend</div></div><div class="px-0 center"><div class="row"><div class="col-12"><h2 class="green spendTxt">' + d3.format("$,.0f")(data["optimized_spend"]) + '</h2></div></div></div></div></div>';
    //         htmlTemplate += '<div class="col summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t500 text-normal">Change</div></div><div class="px-0 center"><div class="row"><div class="col-12"><h2 class="green spendTxt">' + d3.format("$,.0f")(data["change"]) + '</h2></div></div></div></div></div>';
    //         htmlTemplate += '<div class="col summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t500 text-normal">% Change</div></div><div class="px-0 center"><div class="row"><div class="col-12"><h2 class="green spendTxt">' + d3.format(".2f")(data["%change"]) + '</h2></div></div></div></div></div></div></div>';
    //     })
    //     $("#optimization_summary").html(htmlTemplate);
    // }
    $.fn.editable.defaults.mode = 'inline';
    $('#group_constraints_table').on('click-cell.bs.table', function (field, value, row, $element) {
        if (value == 'remove') {
            delete_group_constraints($element);
        }
    });

    $('#individualspendTable').on('check.bs.table', function (row, $element) {
        // $element["Lower Bound %"] = ''
        // $element["Upper Bound %"] = ''
        individualspend_table_update($element);
    });
    $('#individualspendTable').on('uncheck.bs.table', function (row, $element) {
        // $element["Lower Bound %"] = -10
        // $element["Upper Bound %"] = 10
        // $element["Lower Bound $"] = 0
        // $element["Upper Bound $"] = 0
        individualspend_table_update($element, check = 'unchecked');

    });
    $('#individualspendTable').on('check-all.bs.table', function (row, $element) {
        update_individual_spend_lock_unlock_all("Yes");
    });
    $('#individualspendTable').on('uncheck-all.bs.table', function (row, $element) {
        update_individual_spend_lock_unlock_all("No");
    });

    $('#individualspendTable').on('editable-save.bs.table', function (event, field, row, index, oldvalue, $element) {
        individualspend_table_update(row);
    });

    function update_individual_spend_lock_unlock_all(lockall) {
        MMOUtils.showLoader()
        var data = individualspendTable.bootstrapTable("getData");
        if (lockall == 'Yes') {
            data.forEach((row) => {
                row["Lower Bound $"] = row["spend"]
                row["Lower Bound %"] = ""
                row["Lower Bound Eff"] = row["spend"]
                row["Upper Bound $"] = row["spend"]
                row["Upper Bound %"] = ""
                row["Upper Bound Eff"] = row["spend"]
            })
        }
        individualspendTable.bootstrapTable("load", data);
        $.ajax({
            url: '/update_individual_spends_lock_unlock',
            type: "POST",
            data: JSON.stringify({ "lockall": lockall, "optimization_scenario_id": current_optimization_id }),
            processData: false,
            contentType: false,
            dataType: "json",
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                MMOUtils.hideLoader()
            },
            error: function (error) {
                MMOUtils.hideLoader()
            }
        });
    }

    function individualspend_table_update(data, check = '') {
        MMOUtils.showLoader()
        data.period_type = $("#period_type").val();
        $.ajax({
            url: '/update_individual_spends_bounds',
            type: "POST",
            data: JSON.stringify({ ...data, lower_sum: lower_sum, upper_sum: upper_sum, base_sum: base_sum }),
            processData: false,
            contentType: false,
            dataType: "json",
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                var data = individualspendTable.bootstrapTable("getData");
                data.map(function (d) {
                    if (d["variable_name"] == response["variable_name"] && d["period"] == response["period"]) {
                        d["Lower Bound %"] = response["Lower Bound %"]
                        d["Lower Bound $"] = response["Lower Bound $"]
                        d["Upper Bound %"] = response["Upper Bound %"]
                        d["Upper Bound $"] = response["Upper Bound $"]
                        // if (check !== 'unchecked') {
                        d["Lower Bound Eff"] = response["Lower Bound Eff"]
                        d["Upper Bound Eff"] = response["Upper Bound Eff"]
                        // }
                        d["lock"] = response["lock"]
                    }
                    return d
                })
                data.sort(function (a, b) {
                    node1 = a.variable_description.toLowerCase();
                    node2 = b.variable_description.toLowerCase();
                    return (node1 < node2) ? -1 : (node1 > node2) ? 1 : 0;
                });
                lower_sum = response.lower_sum
                upper_sum = response.upper_sum
                base_sum = response.base_sum
                individualspendTable.bootstrapTable("load", data);
                // var lowerBoundCell = $('#individualspendTable th[data-field="Lower Bound $"]');
                // lowerBoundCell.find('.th-inner').html("Lower Bound $<br>" + lower_sum);

                // // Update the title of the "Upper Bound $" cell
                // var upperBoundCell = $('#individualspendTable th[data-field="Upper Bound $"]');
                // upperBoundCell.find('.th-inner').html("Upper Bound $<br>" + upper_sum);
                addLowerandUpperLabels(lower_sum, upper_sum, base_sum)

                MMOUtils.hideLoader()

            },
            error: function (error) {
                MMOUtils.hideLoader()
            }
        });
    }
    function delete_group_constraints(data) {
        data["optimization_scenario_id"] = current_optimization_id
        $.ajax({
            url: '/delete_group_constraints',
            type: "POST",
            data: JSON.stringify(data),
            processData: false,
            contentType: false,
            dataType: "json",
            headers: {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            success: function (response) {
                group_constraints_table.bootstrapTable("load", response);
            },
            error: function (error) {
            }
        });
    }

    // $(".download_output_file").on("click", function () {
    //     var optimization_id = $("#opt_scenarios_new").val();
    //     document.location.href = "/download_optim_output_new?optimization_id=" + optimization_id
    // });

    // $(".download_kpi_output_comparison_file").on("click", function () {
    //     var scenario_one = $("#opt_scenarios_1").val();
    //     var scenario_two = $("#opt_scenarios_2").val();
    //     document.location.href = "/download_kpi_output_comparison?scenario_one=" + scenario_one + "&scenario_two=" + scenario_two
    // });

    // $(".download_group_constraints").on("click", function () {
    //     var optimization_id = $("#opt_scenarios_new").val();
    //     var optimization_name = $('#opt_scenarios_new option:selected').text()
    //     document.location.href = "/download_group_constraints?optimization_id=" + optimization_id + '&filename=' + optimization_name
    // });

    $("#scenario_type").change(function () {
        if ($('option:selected', this).text() == 'Simulation') {
            $("#outcome_to_maximum_out").find('.selectpicker').attr('disabled', true);
            $('.selectpicker').selectpicker('refresh');
            $('#budget_value,#total_budget').attr('disabled', true);
        } else {
            $("#outcome_to_maximum_out").find('.selectpicker').removeAttr('disabled');
            $('.selectpicker').selectpicker('refresh');
            $('#budget_value,#total_budget').removeAttr('disabled');
        }
    });
    var period_type = $("#period_type").val();
    if (period_type === "quarter") {
        var period_start = $('#period_start').val();
        var period_end = $('#period_end').val();
    }
    else {
        var period_start = $("#monthddl1").val()
        var period_end = $("#monthddl2").val()
    }
    $("#period_start").change(function () {
        period_start = $('option:selected', this).val();
        for (var i = 1; i <= 4; i++) {
            if (i >= period_start) {
                $('#period_end  option[value=' + i + ']').removeAttr('disabled');
            } else {
                $('#period_end  option[value=' + i + ']').prop('disabled', true);
            }
        }
        $("#period_end").selectpicker("refresh");
        if (period_start == 4) {
            $('#add_group .group_constraints_period option').hide();
            $('#add_group .group_constraints_period option[value="Overall"]').show();
            $('#add_group .group_constraints_period option[value="4"]').show();
            $("#gc-period").selectpicker("refresh");
        } else {
            $('#add_group .group_constraints_period option').show();
            $("#gc-period").selectpicker("refresh");
        }

    });
    $("#monthddl1").change(function () {
        period_start = $('option:selected', this).val();
        for (var i = 1; i <= 12; i++) {
            if (i >= period_start) {
                $('#monthddl2  option[value=' + i + ']').removeAttr('disabled');
            } else {
                $('#monthddl2  option[value=' + i + ']').prop('disabled', true);
            }
        }
        $("#period_end").selectpicker("refresh");
    });
    $("#period_end").change(function () {
        period_start = $('#period_start').val();
        period_end = $('option:selected', this).val();
        group_cons_list(period_start, period_end);
        $("#gc-period").selectpicker("refresh");
    });
    $(document).on("change", "#opt_scenarios_1,#opt_scenarios_2", function () {

        var current_scenario = $(this).val();
        if (this.id == "opt_scenarios_1") {
            $("#opt_scenarios_2").find('option[value="' + current_scenario + '"]').hide();
            $("#opt_scenarios_2").selectpicker("refresh");
        }
        else {
            $("#opt_scenarios_1").find('option[value="' + current_scenario + '"]').hide();
            $("#opt_scenarios_1").selectpicker("refresh");
        }

    })

    function create_kpi_output_comparison(response) {
        $("#outcome_comparisons").html("")
        /*
        changes: Mayank Prakash on 09/28/2022
        added O_TOTALASSET_IN for KPI outcome calculation
        */
        var customer_names = {
            'O_EXASSET_IN': "Existing Assets In", 'O_NTFHH_CNT': "NTF HH Count",
            'O_NTFASSET_IN': "NTF Assets In", 'O_TOTALASSET_IN': "Total Assets In"
        }
        var scenario_one = $("#opt_scenarios_1").val();
        var scenario_one_name = $('option:selected', "#opt_scenarios_1").text();
        var scenario_two = $("#opt_scenarios_2").val();
        var scenario_two_name = $('option:selected', "#opt_scenarios_2").text();

        var base_data = response.filter(function (d) { return d["id"] == scenario_one });
        var Optimized_data = response.filter(function (d) { return d["id"] == scenario_two });
        var data = [];
        base_data.map(function (d) {
            d["BS-Base"] = parseInt(d["BaseAttribution"])
            d["BS-Marketing"] = parseInt(d["MarketingAttribution"])
            d["BS-Total"] = parseInt(d["Total"])
            var temp = Optimized_data.filter(function (o) { return o["Outcome"] == d["Outcome"] && o["Segment"] == d["Segment"] })
            d["OS-Base"] = parseInt(temp[0]["BaseAttribution"])
            d["OS-Marketing"] = parseInt(temp[0]["MarketingAttribution"])
            d["OS-Total"] = parseInt(temp[0]["Total"])
        });
        var outcomes = d3.map(response, function (d) { return d["Outcome"] }).keys();
        function totalTextFormatter(data) {
            return 'Total'
        }

        function totalNameFormatter(data) {
            return data.length
        }

        function totalPriceFormatter(data) {
            var field = this.field
            return cellformatter(data.map(function (row) {
                return +row[field]
            }).reduce(function (sum, i) {
                return sum + i
            }, 0))
        }

        function totalFormatter(data) {
            var field = this.field
            return cellNumberformatter(data.map(function (row) {
                return +row[field]
            }).reduce(function (sum, i) {
                return sum + i
            }, 0))
        }

        function cellStyle(value, row, index) {
            if (row['OS-Base'] > row['BS-Base']) {
                return { classes: 'green' }
            } else if (row['BS-Base'] == row['OS-Base']) {
                return { classes: 'equal' }
            } else {
                return { classes: 'danger' }
            }
        }
        function cellStyle2(value, row, index) {

            if (row['OS-Marketing'] > row['BS-Marketing']) {
                return { classes: 'green' }
            } else if (row['BS-Marketing'] == row['OS-Marketing']) {
                return { classes: 'equal' }
            } else {
                return { classes: 'danger' }
            }

        }
        function cellStyle3(value, row, index) {
            if (row['OS-Total'] > row['BS-Total']) {
                return { classes: 'green' }
            } else if (row['BS-Total'] == row['OS-Total']) {
                return { classes: 'equal' }
            } else {
                return { classes: 'danger' }
            }

        }
        function cellformatter(data) {
            return d3.format("$,.0f")(data)
        }
        function cellNumberformatter(data) {
            return d3.format(",.0f")(data)
        }

        outcomes.map(function (d) {
            $("#outcome_comparisons").append("<div class='card col-12'> <h5 class='card-title'>" + customer_names[d] + "</h5><table id=" + d + "></div></div>");
            var columns = {
                "spends": [
                    [{ field: "Segment", title: "Segment", rowspan: 2, footerFormatter: totalTextFormatter },
                    { field: "Base Scenario", title: scenario_one_name, colspan: 3, align: 'center' },
                    { field: "Optimized Scenario", title: scenario_two_name, colspan: 3, align: 'center' }],
                    [
                        { field: "BS-Base", title: "Base Attribution", falign: "right", formatter: cellformatter, footerFormatter: totalPriceFormatter },
                        { field: "BS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellformatter, footerFormatter: totalPriceFormatter },
                        { field: "BS-Total", title: "Total", falign: "right", formatter: cellformatter, footerFormatter: totalPriceFormatter },
                        { field: "OS-Base", title: "Base Attribution", falign: "right", formatter: cellformatter, cellStyle: cellStyle, footerFormatter: totalPriceFormatter },
                        { field: "OS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellformatter, cellStyle: cellStyle2, footerFormatter: totalPriceFormatter },
                        { field: "OS-Total", title: "Total", falign: "right", formatter: cellformatter, cellStyle: cellStyle3, footerFormatter: totalPriceFormatter },
                    ]
                ], "counts": [
                    [{ field: "Segment", title: "Segment", rowspan: 2, footerFormatter: totalTextFormatter },
                    { field: "Base Scenario", title: scenario_one_name, colspan: 3, align: 'center' },
                    { field: "Optimized Scenario", title: scenario_two_name, colspan: 3, align: 'center' }],
                    [
                        { field: "BS-Base", title: "Base Attribution", falign: "right", formatter: cellNumberformatter, footerFormatter: totalFormatter },
                        { field: "BS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellNumberformatter, footerFormatter: totalFormatter },
                        { field: "BS-Total", title: "Total", falign: "right", formatter: cellNumberformatter, footerFormatter: totalFormatter },
                        { field: "OS-Base", title: "Base Attribution", falign: "right", formatter: cellNumberformatter, cellStyle: cellStyle, footerFormatter: totalFormatter },
                        { field: "OS-Marketing", title: "Marketing Attribution", falign: "right", formatter: cellNumberformatter, cellStyle: cellStyle2, footerFormatter: totalFormatter },
                        { field: "OS-Total", title: "Total", falign: "right", formatter: cellNumberformatter, cellStyle: cellStyle3, footerFormatter: totalFormatter },
                    ]
                ]
            }

            $("#" + d).bootstrapTable('destroy').bootstrapTable({
                classes: "table table-hover table-bordered",
                showFooter: "true",
                data: base_data.filter(function (c) { return c["Outcome"] == d }),
                columns: d == "O_NTFHH_CNT" ? columns["counts"] : columns["spends"]
            })

        })
    }

    function group_cons_list(period_start, period_end) {
        $('#add_group .group_constraints_period option').hide();
        $('#add_group .group_constraints_period option[value="Overall"]').show();
        for (var i = parseInt(period_start); i <= parseInt(period_end); i++) {
            $('#add_group .group_constraints_period option[value=' + i + ']').show();
        }
        $("#gc-period").selectpicker("refresh");

    }
    $(document).ajaxError(function myErrorHandler(event, xhr, ajaxOptions, thrownError) {
        if (xhr.status == 303) {
            $("#error_message").html(xhr.responseText)
        }
        else if (xhr.status == 500) {
            if (Array.isArray(xhr.responseJSON.message)) {
                $("#error_message").html("<p>" + xhr.responseJSON.message[0] + "</p><p>" + xhr.responseJSON.message[1].toString() + "</p><p>" + xhr.responseJSON.message[2].toString() + "</p>");
            }
            else {
                $("#error_message").html(xhr.responseJSON.message);
            }
        }
        else if (xhr.status == 0) {
            $("#error_message").html('<p>Request submitted for processing. May take more than 15 mins...</p>')
        }
        else if (xhr.status == 502) {
            $("#error_message").html('<p>Optimization started and is running successfully. Please check "KPI Output" tab after sometime</p>')
        }
        $('#app_error').modal('show');
    });

});
function timeperiod() {
    MMOUtils.hideLoader();
    $.ajax({
        url: "/get_time_period",
        type: 'GET',
        dataType: "json",
        processData: false,
        contentType: false,
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        success: function (response) {
            $('#timePeriodInfo').html(
                `<p>${response.min_date} To ${response.max_date}</p>`
            );
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
}
function intialconfiguration() {
    MMOUtils.hideLoader();
    $(".preloader-progress").show();

    // Initialize progressTimer for tracking AJAX request progress
    var progress = $(".loading-progress").progressTimer({
        timeLimit: 60,
        onFinish: function () {
            // Callback function when the timer finishes
            $(".preloader-progress").hide();
        },
    });

    $.ajax({
        url: '/get_initial_config_list',
        type: 'GET',
        dataType: "json",
        processData: false,
        contentType: false,
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        beforeSend: function () {
            progress.progressTimer('start');
        },
        success: function (response) {
            // get the required response to update the select box
            var scenariosListdata = response.scenarios;
            var optimization_types = response.optimization_types;
            var optimization_scenarios = response.optimization_scenarios;
            var all_scenarios = response.all_scenarios;
            touchpoints_groups = response.touchpoint_groups;
            var outcome_maximize = response.outcome_maximum;
            $("#base_scenario").html();

            MMOUtils.buildDDlFromListWithNoSelect("#base_scenario", scenariosListdata, "");
            MMOUtils.buildDDlFromListWithNoSelect("#modalscenarioslist", scenariosListdata, "");
            MMOUtils.buildDDlFromListWithNoSelect("#opt_scenarios", optimization_scenarios, "");
            MMOUtils.buildDDlFromListWithNoSelect("#opt_scenarios_new", optimization_scenarios, "");
            MMOUtils.buildDDlFromListWithNoSelect("#opt_scenarios_1", all_scenarios, "");
            MMOUtils.buildDDlFromListWithNoSelect("#opt_scenarios_2", all_scenarios, "");
            MMOUtils.buildDDlFromListWithNoSelect("#touchpointGroups_2", touchpoints_groups, "");
            MMOUtils.buildDDlFromListWithNoSelect("#outcome_to_maximum", outcome_maximize, "");

            $("#base_scenario").selectpicker("refresh");
            $("#modalscenarioslist").selectpicker("refresh");
            $("#opt_scenarios").selectpicker("refresh");
            $("#touchpointGroups_2").selectpicker("refresh");
            $("#opt_scenarios_1").selectpicker("refresh");
            $("#opt_scenarios_2").selectpicker("refresh");
            $("#outcome_to_maximum").selectpicker("refresh");
            $("#opt_scenarios_new").selectpicker("refresh");

        },
        error: function (error) {
            MMOUtils.hideLoader();
        },
        complete: function () {
            // Hide preloader after the API call completes, whether it was successful or not
            progress.progressTimer('complete');
        }
    });
}
function updateOptions(periodType) {
    var options = '<option value="Select" selected>Select</option>';
    if (periodType === "month") {
        options += '<option value="1">Jan</option>';
        options += '<option value="2">Feb</option>';
        options += '<option value="3">Mar</option>';
        options += '<option value="4">Apr</option>';
        options += '<option value="5">May</option>';
        options += '<option value="6">Jun</option>';
        options += '<option value="7">Jul</option>';
        options += '<option value="8">Aug</option>';
        options += '<option value="9">Sep</option>';
        options += '<option value="10">Oct</option>';
        options += '<option value="11">Nov</option>';
        options += '<option value="12">Dec</option>';
        // options += '<option value="Overall" selected>Overall</option>';
    } else if (periodType === "quarter") {
        options += '<option value="1">Q1</option>';
        options += '<option value="2">Q2</option>';
        options += '<option value="3">Q3</option>';
        options += '<option value="4">Q4</option>';
        // options += '<option value="Overall" selected>Overall</option>';
    } else {
        // options += '<option value="Overall" selected>Overall</option>';
    }

    $("#gc-period").html(options);
    $("#gc-period").selectpicker('refresh');
}