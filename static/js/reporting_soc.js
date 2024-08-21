var ScenarioTree = {};
var metricLevelData = {
    "Overall-Change": {},
    "outcome2": {},
    "outcome1": {},
    "coutcome2": {},
    "coutcome1": {}
};

var HEADERS = {
    "qtrly": ["Q1", "Q2", "Q3", "Q4", "Total"],
    "monthly": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "Total"],
    "yearly": ["Annual", "Total"],
    "halfyearly": ["H1", "H2", "Total"]
};

var HEADERS_KEYS = {
    "qtrly": ["Q1", "Q2", "Q3", "Q4", "Total"],
    "monthly": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "DEC", "Total"],
    "yearly": ["Year", "Total"],
    "halfyearly": ["HalfYear-1", "HalfYear-2", "Total"]
};

// SUBHEADERS_NTFHH = [{
//     title: 'Spend',
//     editable: false,
//     custom: false,
//     key: 'spend'
// }, {
//     title: 'NTF - HH Count',
//     editable: false,
//     custom: false,
//     key: 'O_NTFHH_CNT'
// }];

SUBHEADERS_NTFAI = [{
    title: 'Spend($)',
    editable: false,
    custom: false,
    key: 'spend'
}, {
    title: 'Outcome1',
    editable: false,
    custom: false,
    key: 'outcome1'
}, {
    title: 'coutcome1($)',
    editable: false,
    custom: false,
    key: 'cpa'
}
];
SUBHEADERS_CHANGE = [{
    title: 'Spend(%)',
    editable: false,
    custom: false,
    key: 'spend'
}, {
    title: 'outcome1(%)',
    editable: false,
    custom: false,
    key: 'outcome1'
}, {
    title: 'coutcome1(%)',
    editable: false,
    custom: false,
    key: 'cpa'
}
];

SUBHEADERS_EXTAI = [{
    title: 'Spend($)',
    editable: false,
    custom: false,
    key: 'spend'
}, {
    title: 'Outcome2',
    editable: false,
    custom: false,
    key: 'outcome2'
}, {
    title: 'coutcome2($)',
    editable: false,
    custom: false,
    key: 'cpa'
}];
SUBHEADERS_CHANGE_SU = [{
    title: 'Spend(%)',
    editable: false,
    custom: false,
    key: 'spend'
}, {
    title: 'outcome2(%)',
    editable: false,
    custom: false,
    key: 'outcome2'
}, {
    title: 'coutcome2(%)',
    editable: false,
    custom: false,
    key: 'cpa'
}
];

// will need to move this tree config to a config file for easy editing
var HEADER_STRUCTURE = {
    /*"O_NTFHH_CNT": [{
        title: '2018',
        key: '2018_S1',
        subheaders: SUBHEADERS_NTFHH
    },
    {
        title: '2017',
        key: '2017_S2',
        subheaders: SUBHEADERS_NTFHH
    }
        /*,
                {
                    title: 'Overall Change',
                    key: 'overall',
                    subheaders: SUBHEADERS_NTFHH
                },
                {
                    title: '% Change',
                    key: 'pct',
                    subheaders: SUBHEADERS_NTFHH
                }*
    ],*/

    "outcome1": [{
        title: '2018',
        key: '2018_S1',
        subheaders: SUBHEADERS_NTFAI
    },
    {
        title: '2017',
        key: '2017_S2',
        subheaders: SUBHEADERS_NTFAI
    },
    /*,
            {
                title: 'Overall Change',
                key: 'overall',
                subheaders: SUBHEADERS_NTFAI
            },*/
    {
        title: 'Change',
        key: 'percent',
        subheaders: SUBHEADERS_CHANGE
    }
    ],

    "outcome2": [{
        title: '2018',
        key: '2018_S1',
        subheaders: SUBHEADERS_EXTAI
    },
    {
        title: '2017',
        key: '2017_S2',
        subheaders: SUBHEADERS_EXTAI
    },
    {
        title: 'Change',
        key: 'percent',
        subheaders: SUBHEADERS_CHANGE_SU
    }
    ],
    // "TOTAL_ASSET_IN": [{
    //     title: '2018',
    //     key: '2018_S1',
    //     subheaders: SUBHEADERS_TOTALASSET
    // },
    // {
    //     title: '2017',
    //     key: '2017_S2',
    //     subheaders: SUBHEADERS_TOTALASSET
    // }]
};

var ScenariosummaryBox = {};
var scenarioName1, scenarioName2;
var count = 4;
var summaryData = [{
    "name": "Scenario 1",
    "scenario2": 0,
    "scenario1": 40
}, {
    "name": "Scenario 2",
    "scenario2": 30,
    "scenario1": 40
}];

$(function () {
    document.addEventListener('click', function (event) {
        var dropdown = document.querySelector('.main-dropdown-menu');
        var maindropdown = document.querySelector('.maindropdown');

        if (!dropdown.contains(event.target) && !maindropdown.contains(event.target)) {
            $('.main-dropdown-menu').hide();
            $(".maindropdown").removeClass('active');

        }
    });
    MMOUtils.showLoader();
    DropdownTree = new MMOTreeDropDown({
        treeBodyNode: '.ddl'
    });
    timeperiod()
    ScenarioTree = new MMOTree({
        treeHeadNode: '.treeDataHeader',
        treeBodyNode: '.treeDatabody',
        headerStructure: HEADER_STRUCTURE,
        formatCellData: formatCellData
    });
    var period_type = $("#period_type").val();
    if (period_type == "year") {
        $(".scenariolabel").hide()
    }
    else {
        $(".scenariolabel").show()
    }
    getscenarioslist();

    ScenariosummaryBox = new summaryBox({});
    // get_soc_data(inputs);
    //$("body").on("change","#scenario1,#scenario2,#period_type,#quarterddl1,#quarterddl2,#halfyearddl1,#halfyearddl2",updateSOCData);
    $("#period_type").on("change", function () {
        var period_type = $(this).val();
        if (period_type == "year") {
            $(".quarterddl-item").hide();
            $(".halfyearddl-item").hide();
            $(".monthddl-item").hide();
            $(".scenariolabel").hide()
        }
        else if (period_type == "halfyear") {
            $(".quarterddl-item").hide();
            $(".halfyearddl-item").show();
            $(".monthddl-item").hide();
            $(".scenariolabel").show()
        }
        else if (period_type == "month") {
            $(".quarterddl-item").hide();
            $(".halfyearddl-item").hide();
            $(".monthddl-item").show();
            $(".scenariolabel").show()
        }
        else {
            $(".quarterddl-item").show();
            $(".halfyearddl-item").hide();
            $(".monthddl-item").hide();
            $(".scenariolabel").show()
        }
    })
    $("body").on("click", "#btn_compare_soc", updateSOCData);

    $("body").on("click", ".outcome-menu", outcomeChange);

    $("body").on("click", "a.toggle-btn", toggleContent);

    $("body").on("click", "#compareBarChartapplyBtn", selectedLevels);
    $("body").on("keyup", "#geolevelsearchBox", geolevelsearch);

    $("body").on("click", ".exportAsImage", function () {
        var period_type = $("#period_type").val();
        var activetab = $('a[data-toggle="tab"].active').text();
        var outcome = $("a.active.metricLink").text();
        var outcome_title = ""
        if (period_type == "year") {
            outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + ")"
        }
        else if (period_type == "halfyear") {
            outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + "-" + $("#halfyearddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#halfyearddl2 option:selected").text() + ")"
        }
        else if (period_type == "month") {
            outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + "-" + $("#monthddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#monthddl2 option:selected").text() + ")"
        }
        else {
            outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + "-" + $("#quarterddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#quarterddl2 option:selected").text() + ")"
        }

        var chartID = $(this).data("chart-name");
        var svg = d3.select('#' + chartID).select('svg');
        svg.insert('rect', ':first-child')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('fill', 'white');
        d3.select('#' + chartID).selectAll("path").attr("fill", "none");
        //fix no axes
        d3.select('#' + chartID).selectAll("path.domain").attr("stroke", "black");
        //fix no tick
        d3.select('#' + chartID).selectAll(".tick line").attr("stroke", "black");
        saveSvgAsPng($("#" + chartID).find('svg')[0], activetab + "-" + outcome_title + ".png");
    }),

        $(".downloadscenario").on("click", function () {
            var outcome = $("input[name='metric']:checked").val();
            var scenario1 = $("#scenario1").val();
            var scenario2 = $("#scenario2").val();
            var year1 = $("#scenario1 :selected").text();
            var year2 = $("#scenario2 :selected").text();
            var period_type = $("#period_type").val();
            var quarter1 = $("#quarterddl1").val()
            var quarter2 = $("#quarterddl2").val()
            var month1 = $("#monthddl1").val()
            var month2 = $("#monthddl2").val()
            var halfyear1 = $("#halfyearddl1").val()
            var halfyear2 = $("#halfyearddl2").val()
            var download_type = $(this).attr('download-type')
            if (download_type === 'csv') {
                document.location.href = "/download_reporting_soc?scenarios=[" + scenario1 + "," + scenario2 + "]&years=['" + year1 + "','" + year2 + "']&quarters=['" + quarter1 + "','" + quarter2 + "']&halfyears=['" + halfyear1 + "','" + halfyear2 + "']&months=['" + month1 + "','" + month2 + "']&outcome=" + outcome + "&period_type=" + period_type + "&download_type=csv"
            } else {
                document.location.href = "/download_reporting_soc?scenarios=[" + scenario1 + "," + scenario2 + "]&years=['" + year1 + "','" + year2 + "']&quarters=['" + quarter1 + "','" + quarter2 + "']&halfyears=['" + halfyear1 + "','" + halfyear2 + "']&months=['" + month1 + "','" + month2 + "']&outcome=" + outcome + "&period_type=" + period_type + "&download_type=excel"
            }
        })

});
function timeperiod() {
    MMOUtils.showLoader()
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
function updateSOCData() {
    MMOUtils.showLoader();
    var scenario1 = $("#scenario2").val()
    var scenario2 = $("#scenario1").val()
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl2").val()
    var quarter2 = $("#quarterddl1").val()
    var halfyear1 = $("#halfyearddl1").val()
    var halfyear2 = $("#halfyearddl2").val()
    var month1 = $("#monthddl2").val()
    var month2 = $("#monthddl1").val()
    var outcome = $("input[name='metric']:checked").val();
    var year1 = $("#scenario2 option:selected").text();
    var year2 = $("#scenario1 option:selected").text();

    var inputs = {}
    inputs.scenario_1 = scenario1
    inputs.scenario_2 = scenario2
    inputs.period_type = period_type
    inputs.quarter1 = quarter1
    inputs.quarter2 = quarter2
    inputs.halfyear1 = halfyear1
    inputs.halfyear2 = halfyear2
    inputs.month1 = month1
    inputs.month2 = month2
    inputs.year1 = year1
    inputs.year2 = year2

    inputs.outcome = outcome,
        inputs.required_control = true
    get_soc_summary(inputs);
    if (outcome == "Overall-Change") {
        // $("a.toggle-btn").toggleClass("active")
        $("#overallchange").prop("checked", true);
        $("#outcome1", "#outcome2").prop("checked", false);
    } else {
        if (outcome == "outcome2") {
            $("#outcome2").prop("checked", true);
            $("#outcome1", "#overallchange").prop("checked", false);
        }
        else if (outcome == "outcome1") {
            $("#outcome1").prop("checked", true);
            $("#outcome2", "#overallchange").prop("checked", false);
        }
    }
    if (outcome == "Overall-Change") {
        $("#Compare-metricTblBox").hide();
        $("#waterfallbtn").hide();
        $(".graphblock").hide();
    }
    else {
        $("#waterfallbtn").show();
        var viewtype = $("a.toggle-btn.active").attr("href");
        if (viewtype == '#graph') {
            selectedLevels();
            $("#Compare-graphs").show();
            $("#touchpoints_ddl").show();
            $("#Compare-metricTblBox").hide();
            if ($(".maindropdown").hasClass('active')) {
                $('.main-dropdown-menu').hide();
                $(".maindropdown").removeClass('active');
            }
        }
        else {
            get_soc_data(inputs);
            $("#Compare-graphs").hide();
            $("#Compare-metricTblBox").show();
            $("#touchpoints_ddl").hide();
        }

    }

}

function get_soc_data(inputs) {
    MMOUtils.showLoader();
    const queryString = $.param(inputs);
    $.ajax({
        url: "/get_spend_allocations?" + queryString,
        type: 'GET',
        dataType: "json",
        headers: {
            "cache-control": "no-cache"
        },
        success: function (response) {

            if (inputs.period_type == "year") {
                // response['headers']["O_NTFHH_CNT"] = response['headers']["O_NTFHH_CNT"].map(function (d) {
                //     d['subheaders'] = SUBHEADERS_NTFHH;
                //     return d
                // })
                response['headers']["outcome1"] = response['headers']["outcome1"].map(function (d) {
                    if (d['title'] == "Change") {
                        d['subheaders'] = SUBHEADERS_CHANGE;
                    }
                    else {
                        d['subheaders'] = SUBHEADERS_NTFAI;
                    }
                    return d
                })
                response['headers']["outcome2"] = response['headers']["outcome2"].map(function (d) {
                    if (d['title'] == "Change") {
                        d['subheaders'] = SUBHEADERS_CHANGE_SU;
                    }
                    else {
                        d['subheaders'] = SUBHEADERS_EXTAI;
                    }
                    return d
                })

                // response['headers']["TOTAL_ASSET_IN"] = response['headers']["TOTAL_ASSET_IN"].map(function (d) {
                //     d['subheaders'] = SUBHEADERS_TOTALASSET;
                //     return d
                // })

            }
            else if (inputs.period_type == "month") {
                response['headers']["outcome1"] = response['headers']["outcome1"]
                    .filter(function (d) {
                        return d.key.indexOf(inputs.month1 + "_" + inputs.year1) > -1 || d.key.indexOf(inputs.month2 + "_" + inputs.year2) > -1 || d.key.indexOf("percent") > -1
                    })
                    .map(function (d) {
                        if (d['title'] == "Change") {
                            d['subheaders'] = SUBHEADERS_CHANGE;
                        }
                        else {
                            d['subheaders'] = SUBHEADERS_NTFAI;
                        }
                        return d
                    })
                response['headers']["outcome2"] = response['headers']["outcome2"]
                    .filter(function (d) {
                        return d.key.indexOf(inputs.month1 + "_" + inputs.year1) > -1 || d.key.indexOf(inputs.month2 + "_" + inputs.year2) > -1 || d.key.indexOf("percent") > -1
                    })
                    .map(function (d) {
                        if (d['title'] == "Change") {
                            d['subheaders'] = SUBHEADERS_CHANGE_SU;
                        }
                        else {
                            d['subheaders'] = SUBHEADERS_EXTAI;
                        }
                        return d
                    })
            }
            else {
                response['headers']["outcome1"] = response['headers']["outcome1"]
                    .filter(function (d) {
                        return d.key.indexOf(inputs.quarter1 + "_" + inputs.year1) > -1 || d.key.indexOf(inputs.quarter2 + "_" + inputs.year2) > -1 || d.key.indexOf("percent") > -1
                    })
                    .map(function (d) {
                        if (d['title'] == "Change") {
                            d['subheaders'] = SUBHEADERS_CHANGE;
                        }
                        else {
                            d['subheaders'] = SUBHEADERS_NTFAI;
                        }
                        return d
                    })
                response['headers']["outcome2"] = response['headers']["outcome2"]
                    .filter(function (d) {
                        return d.key.indexOf(inputs.quarter1 + "_" + inputs.year1) > -1 || d.key.indexOf(inputs.quarter2 + "_" + inputs.year2) > -1 || d.key.indexOf("percent") > -1
                    })
                    .map(function (d) {
                        if (d['title'] == "Change") {
                            d['subheaders'] = SUBHEADERS_CHANGE_SU;
                        }
                        else {
                            d['subheaders'] = SUBHEADERS_EXTAI;
                        }
                        return d
                    })

            }
            ScenarioTree.headerStructure = response['headers'];

            ScenarioTree.refreshTable(response['spends'], inputs.outcome, 'spend');
            ScenarioTree.refreshTable(response['outcomes'], inputs.outcome, inputs.outcome);
            ScenarioTree.refreshTable(response['cpa'], inputs.outcome, 'cpa');
            setPctValues();
            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });

}

function get_soc_summary(inputs) {
    MMOUtils.showLoader()
    var viewtype = $("a.toggle-btn.active").attr("href");
    if (inputs.outcome == "Overall-Change") {
        $("#Compare-metricTxtBox").hide();
        $("#Compare-metricTblBox").hide();
        $("#waterfallbtn").hide();
        $(".view-type.toggle-btn")
            .prop("disabled", true)
            .css("cursor", "not-allowed");
    }
    else {
        $("#waterfallbtn").show();
        $("#Compare-metricTxtBox").show();
        $("#Compare-metricTblBox").show();
        $(".view-type.toggle-btn")
            .prop("disabled", false)
            .css("cursor", "pointer");
    }
    if (viewtype == "#graph" && inputs.outcome == "Overall-Change") {
        $("#Compare-graphs").hide()
    }
    const queryString = $.param(inputs);
    $.ajax({
        url: "/get_spend_allocations_summary?" + queryString,
        type: 'GET',
        dataType: "json",
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        success: function (response) {
            ScenariosummaryBox.comparesummaryBlocks(response, inputs.outcome, metricLevelData);
            MMOUtils.hideLoader();

        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
}

function outcomeChange() {

    // highlight only the selected menu item
    $(".outcome-menu").removeClass("active")
    $(this).addClass("active");

    // defines the key for the menu
    var headerKeyByMenu = {
        'menu_ntf_hh': 'ntf_hh',
        'menu_ntf_ai': 'ntf_ai',
        'menu_ext_ai': 'ext_ai'
    };

    if (this.id != 'menu_overall') {
        refreshData(headerKeyByMenu[this.id]);
    } else {
        refreshSummaryData();
    }
}

function selectedLevels() {
    MMOUtils.showLoader();
    var checkedItems = [];
    $.each($("input[class='geolevelItem']:checked"), function () {
        checkedItems.push($(this).attr("id"));
    });

    var scenario1 = $("#scenario1").val();
    var scenario2 = $("#scenario2").val();
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl1").val();
    var quarter2 = $("#quarterddl2").val();
    var month1 = $("#monthddl1").val();
    var month2 = $("#monthddl2").val();
    var outcome = $("input[name='metric']:checked").val();
    var halfyear1 = $("#halfyearddl1").val();
    var halfyear2 = $("#halfyearddl2").val();
    var year1 = $("#scenario1 option:selected").text();
    var year2 = $("#scenario2 option:selected").text();

    // Constructing the inputs object with query parameters
    var queryString = `scenario_1=${scenario1}&scenario_2=${scenario2}&year1=${year1}&year2=${year2}&period_type=${period_type}&quarter1=${quarter1}&quarter2=${quarter2}&halfyear1=${halfyear1}&halfyear2=${halfyear2}&month1=${month1}&month2=${month2}&outcome=${outcome}&required_control=true&nodes=${checkedItems.join(',')}`;

    $.ajax({
        url: "/get_soc_comarison_by_node?" + queryString,
        type: 'GET',
        dataType: "json",
        success: function (response) {
            $("#Compare-graphs").html("");
            var outcome = $("input[name='metric']:checked").val();
            if (outcome == "outcome1") {
                outcome = "outcome1"
            }
            else if (outcome == "outcome2") {
                outcome = "outcome2"
            }
            var htmlTemplate = '<div class="card pt-3"><h4 class="text-center">Spends</h4><div class="graph pt-0" id="spendComparison_box" style="height: 520px;width:100%">' + chart1 + '</div></div>';
            htmlTemplate += '<div class="card pt-3"><h4 class="text-center">' + outcome + '</h4><div class="graph pt-0" id="socComparison_box" style="height: 520px;width:100%">' + chart2 + '</div></div>'
            $("#Compare-graphs").append(htmlTemplate);

            var chart1 = bargraphGenerate("spendComparison", response);
            var chart2 = bargraphGenerate("socComparison", response);
            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });

    if ($(".maindropdown").hasClass('active')) {
        $('.main-dropdown-menu').hide();
        $(".maindropdown").removeClass('active');
    }
    else {
        $(".maindropdown").addClass('active');
        $('.main-dropdown-menu').show();
    }
}

function getscenarioslist() {
    MMOUtils.showLoader()
    $.ajax({
        url: '/get_reporting_allocations_list_SOC',
        type: 'GET',
        dataType: "json",
        processData: false,
        contentType: false,
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        success: function (response) {
            $("#scenario1").html();
            $("#scenario2").html();
            MMOUtils.buildDDlFromList("#scenario1", response);
            MMOUtils.buildDDlFromList("#scenario2", response);
            $("#scenario1").selectpicker("refresh");
            $("#scenario1").find('option[value="2"]').attr('selected', 'selected')
            $("#scenario1").selectpicker("refresh");
            $("#scenario2").selectpicker("refresh");
            $("#scenario2").find('option[value="1"]').attr('selected', 'selected')
            $("#scenario2").selectpicker("refresh");
            $("#overallchange").prop("checked", true);
            $("#outcome1", "#outcome2").prop("checked", false);

            var scenario1 = $("#scenario2").val()
            var scenario2 = $("#scenario1").val()
            var period_type = $("#period_type").val();
            var quarter1 = $("#quarterddl2").val()
            var quarter2 = $("#quarterddl1").val()
            var halfyear1 = $("#halfyearddl1").val()
            var halfyear2 = $("#halfyearddl2").val()
            var month1 = $("#monthddl2").val()
            var month2 = $("#monthddl1").val()
            var outcome = $("input[name='metric']:checked").val();
            var year1 = $("#scenario2 option:selected").text();
            var year2 = $("#scenario1 option:selected").text();

            var inputs = {}
            inputs.scenario_1 = scenario1
            inputs.scenario_2 = scenario2
            inputs.period_type = period_type
            inputs.quarter1 = quarter1
            inputs.quarter2 = quarter2
            inputs.halfyear1 = halfyear1
            inputs.halfyear2 = halfyear2
            inputs.month1 = month1
            inputs.month2 = month2
            inputs.year1 = year1
            inputs.year2 = year2

            inputs.outcome = outcome,
                inputs.required_control = true
            get_soc_summary(inputs);
            marginalreturnGeolevelTree();

        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
}
function marginalreturnGeolevelTree() {
    MMOUtils.showLoader()
    // fetch the data
    $.ajax({
        url: "/get_media_hierarchy_list",
        type: 'GET',
        dataType: "json",
        processData: false,
        contentType: false,
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        success: function (response) {
            var scenarioDetails = {};
            // get the required response to update the select box
            DropdownTree.rebuildTable(response);
            var outcome = $("input[name='metric']:checked").val();
            if (outcome == "Overall-Change") {
                $("#touchpoints_ddl").hide();
            }
            else {
                $("#touchpoints_ddl").show();
            }
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });

}

function toggleContent() {
    $("a.toggle-btn").removeClass("active");
    var viewtype = $(this).attr('href');
    marginalreturnGeolevelTree()
    if (viewtype == '#tabular') {
        var scenario1 = $('#scenario2').val()
        var scenario2 = $("#scenario1").val()
        var period_type = $("#period_type").val();
        var quarter1 = $("#quarterddl2").val()
        var quarter2 = $("#quarterddl1").val()
        var halfyear1 = $("#halfyearddl1").val()
        var halfyear2 = $("#halfyearddl2").val()
        var month1 = $("#monthddl2").val()
        var month2 = $("#monthddl1").val()
        var outcome = $("input[name='metric']:checked").val();
        var year1 = $("#scenario1 option:selected").text();
        var year2 = $("#scenario2 option:selected").text();
        var inputs = {}
        inputs.scenario_1 = scenario1
        inputs.scenario_2 = scenario2
        inputs.year1 = year1
        inputs.year2 = year2
        inputs.period_type = period_type
        inputs.quarter1 = quarter1
        inputs.quarter2 = quarter2
        inputs.halfyear1 = halfyear1
        inputs.halfyear2 = halfyear2
        inputs.month1 = month1
        inputs.month2 = month2
        inputs.outcome = outcome,
            inputs.required_control = true

        get_soc_data(inputs);
        $("#Compare-graphs").hide();
        $("#Compare-metricTblBox").show();
        $("#touchpoints_ddl").hide();
    }
    else {
        var outcome = $("input[name='metric']:checked").val();

        selectedLevels();
        $("#Compare-graphs").show();
        $("#touchpoints_ddl").show();
        $("#Compare-metricTblBox").hide();
        if ($(".maindropdown").hasClass('active')) {
            $('.main-dropdown-menu').hide();
            $(".maindropdown").removeClass('active');
        }
        if (outcome == "Overall-Change") {
            $("#touchpoints_ddl").hide();
        }
        else {
            $("#touchpoints_ddl").show();
        }
    }
    $(this).addClass("active");
}

$(".metricLink").click(function (e) {
    MMOUtils.showLoader();
    var scenario1 = $("#scenario2").val()
    var scenario2 = $("#scenario1").val()
    var period_type = $("#period_type").val();
    if (period_type == "year") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").hide();
    }
    else if (period_type == "halfyear") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").show();
        $(".monthddl-item").hide();
    }
    else if (period_type == "month") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").show();
    }
    else {
        $(".quarterddl-item").show();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").hide();
    }


    var quarter1 = $("#quarterddl2").val()
    var quarter2 = $("#quarterddl1").val()
    var halfyear1 = $("#halfyearddl1").val()
    var halfyear2 = $("#halfyearddl2").val()
    var month1 = $("#monthddl2").val()
    var month2 = $("#monthddl1").val()
    var outcome = $("input[name='metric']:checked").val();
    var year1 = $("#scenario2 option:selected").text();
    var year2 = $("#scenario1 option:selected").text();

    var inputs = {}
    inputs.scenario_1 = scenario1
    inputs.scenario_2 = scenario2
    inputs.period_type = period_type
    inputs.quarter1 = quarter1
    inputs.quarter2 = quarter2
    inputs.halfyear1 = halfyear1
    inputs.halfyear2 = halfyear2
    inputs.month1 = month1
    inputs.month2 = month2
    inputs.outcome = outcome,
        inputs.year1 = year1
    inputs.year2 = year2
    inputs.required_control = true

    get_soc_summary(inputs);

    if (outcome == "Overall-Change") {

        $("#Compare-metricTxtBox").hide();
        // $("#Compare-metricTblBox").hide();
        $("#waterfallbtn").hide();
        $(".graphblock").hide();
        $("#overallchange").prop("checked", true);
        $("#outcome1", "#outcome2").prop("checked", false);
        $("#touchpoints_ddl").hide();
        MMOUtils.hideLoader();
    } else {
        if (outcome == "outcome1") {
            $("#outcome1").prop("checked", true);
            $("#overallchange", "#outcome2").prop("checked", false);
        }
        else if (outcome == "outcome2") {
            $("#outcome2").prop("checked", true);
            $("#overallchange", "#outcome1").prop("checked", false);
        }
        $("#waterfallbtn").show();
        var viewtype = $("a.toggle-btn.active").attr("href");
        if (viewtype == '#graph') {
            selectedLevels();
            $("#Compare-graphs").show();
            $("#touchpoints_ddl").show();
            $("#Compare-metricTblBox").hide();
        }
        else {
            get_soc_data(inputs);
            $("#Compare-graphs").hide();
            $("#Compare-metricTblBox").show();
            $("#touchpoints_ddl").hide();
        }
    }



});

function refreshData(headerKey) {
    ScenarioTree.refreshTable({}, headerKey);
}

function refreshSummaryData() {

}

function formatCellData(cellData, subHeaderNeeded) {
    return MMOUtils.commaSeparatevalue(MMOUtils.round(MMOUtils.replaceComma(cellData), 0));
}

function setPctValues() {
    var nodeIds = ScenarioTree.getAllNodeIds();
    var rowCnt = nodeIds.length;
    var rootNodes = ScenarioTree.getRootNodes();

    var headers = ScenarioTree.getHeaders();

    var control_totals = getRootTotals(headers, rootNodes[0]);
    var media_totals = getRootTotals(headers, rootNodes[1]);

    var cellKeyValue;
    var cellKeyPct;
    var totalValue;
    var pctValue;
    // for each row...
    for (i = 0; i < rowCnt; i++) {
        // update the pct value for each header
        $.each(headers, function (j, h) {
            // get the appropriate total
            // TODO: determine a better check for control vs media
            if (nodeIds[i] < 93) {
                totalValue = control_totals[h.key]
            } else {
                totalValue = media_totals[h.key]
            }

            // get the cell value for the header and calculate the percent
            cellKeyValue = ScenarioTree.getCellId(i, h.key, 'total');
            pctValue = ScenarioTree.getCellData(cellKeyValue) / totalValue * 100;
            //pctValue = ScenarioTree.getCellData(cellKeyValue) / 1000000 * 100;

            // get the cell id and update the pct
            cellKeyPct = ScenarioTree.getCellId(i, h.key, 'pct');
            ScenarioTree.updateCell(cellKeyPct, pctValue);
        });
    }

    function getRootTotals(headers, rootNodeId) {
        var cellKey;
        var totals = {};

        $.each(headers, function (i, h) {
            cellKey = ScenarioTree.getCellId(rootNodeId, h.key, 'total');
            totals[h.key] = ScenarioTree.getCellData(cellKey);
        });

        return totals;
    }
}

$("#waterfallmodalBox").on('shown.bs.modal', function () {

    var tab = $('a[data-toggle="tab"].active').attr('href')
    var chart_id = ""
    var resp_key = ""
    if (tab == '#highLevelWC') {
        chart_id = "highlevelWaterfallChart";
        resp_key = "highlevel";
    }
    else if (tab == '#controlSplit') {
        chart_id = "controlWaterfallChart";
        resp_key = "controlsplit";
    }
    else if (tab == '#econSplit') {
        chart_id = "econWaterfallChart";
        resp_key = "econsplit";
    }
    else {
        chart_id = "mediaWaterfallChart";
        resp_key = "mediasplit";
    }

    var outcome = $("input[name='metric']:checked").val();
    var scenario1 = $("#scenario1").val()
    var scenario2 = $("#scenario2").val()
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl1").val()
    var quarter2 = $("#quarterddl2").val()
    var month1 = $("#monthddl1").val()
    var month2 = $("#monthddl2").val()
    var halfyear1 = $("#halfyearddl1").val()
    var halfyear2 = $("#halfyearddl2").val()
    var year1 = $("#scenario1 option:selected").text();
    var year2 = $("#scenario2 option:selected").text();

    var inputs = {}
    inputs.scenario_1 = scenario1
    inputs.scenario_2 = scenario2
    inputs.year1 = year1
    inputs.year2 = year2
    inputs.period_type = period_type
    inputs.quarter1 = quarter1
    inputs.quarter2 = quarter2
    inputs.halfyear1 = halfyear1
    inputs.halfyear2 = halfyear2
    inputs.month1 = month1
    inputs.month2 = month2
    inputs.outcome = outcome,
        inputs.required_control = true
    // var outcome_title = ""
    // if (period_type == "year") {
    //     outcome_title = $("a.active.metricLink").text() + " <span style='font-size:initial;'> (Period: " + $("#scenario1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + ")</span>"
    // }
    // else if (period_type == "halfyear") {
    //     outcome_title = $("a.active.metricLink").text() + " <span style='font-size:initial;'> (Period: " + $("#scenario1 option:selected").text() + "-" + $("#halfyearddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#halfyearddl2 option:selected").text() + ")</span>"
    // }
    // else if (period_type == "month") {
    //     outcome_title = $("a.active.metricLink").text() + " <span style='font-size:initial;'>  (Period: " + $("#scenario1 option:selected").text() + "-" + $("#monthddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#monthddl2 option:selected").text() + ")</span>"
    // }
    // else {
    //     outcome_title = $("a.active.metricLink").text() + " <span style='font-size:initial;'> (Period: " + $("#scenario1 option:selected").text() + "-" + $("#quarterddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#quarterddl2 option:selected").text() + ")</span>"
    // }

    // $("#outcome_title").html(outcome_title);
    const queryString = $.param(inputs);
    $.ajax({
        url: "/get_soc_wfc_data?" + queryString,
        type: 'GET',
        dataType: "json",
        headers: {
            "cache-control": "no-cache"
        },
        success: function (response) {
            customwaterfallChart(chart_id, response[resp_key], outcome);
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });
});

$('a[data-toggle="tab"]').bind('click', function (e) {
    e.preventDefault();

    var tab = $(this).attr("href");
    var chart_id = ""
    var resp_key = ""
    if (tab == '#highLevelWC') {
        chart_id = "highlevelWaterfallChart";
        resp_key = "highlevel";
    }
    else if (tab == '#controlSplit') {
        chart_id = "controlWaterfallChart";
        resp_key = "controlsplit";
    }
    else if (tab == '#econSplit') {
        chart_id = "econWaterfallChart";
        resp_key = "econsplit";
    }
    else {
        chart_id = "mediaWaterfallChart";
        resp_key = "mediasplit";
    }

    var outcome = $("input[name='metric']:checked").val();
    var scenario1 = $("#scenario1").val()
    var scenario2 = $("#scenario2").val()
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl1").val()
    var quarter2 = $("#quarterddl2").val()
    var halfyear1 = $("#halfyearddl1").val()
    var halfyear2 = $("#halfyearddl2").val()
    var month1 = $("#monthddl1").val()
    var month2 = $("#monthddl2").val()
    var year1 = $("#scenario1 option:selected").text();
    var year2 = $("#scenario2 option:selected").text();

    var inputs = {}
    inputs.scenario_1 = scenario1
    inputs.scenario_2 = scenario2
    inputs.year1 = year1
    inputs.year2 = year2
    inputs.period_type = period_type
    inputs.quarter1 = quarter1
    inputs.quarter2 = quarter2
    inputs.halfyear1 = halfyear1
    inputs.halfyear2 = halfyear2
    inputs.month1 = month1
    inputs.month2 = month2
    inputs.outcome = outcome,
        inputs.required_control = true

    // var outcome_title = ""
    // if (period_type == "year") {
    //     outcome_title = $("a.active.metricLink").text() + outcome + " <span style='font-size:initial;'> (Period: " + $("#scenario1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + ")</span>"
    // }
    // else if (period_type == "halfyear") {
    //     outcome_title = $("a.active.metricLink").text() + outcome + " <span style='font-size:initial;'> (Period: " + $("#scenario1 option:selected").text() + "-" + $("#halfyearddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#halfyearddl2 option:selected").text() + ")</span>"
    // }
    // else if (period_type == "month") {
    //     outcome_title = $("a.active.metricLink").text() + outcome + " <span style='font-size:initial;'>  (Period: " + $("#scenario1 option:selected").text() + "-" + $("#monthddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#monthddl2 option:selected").text() + ")</span>"
    // }
    // else {
    //     outcome_title = $("a.active.metricLink").text() + outcome + " <span style='font-size:initial;'> (Period: " + $("#scenario1 option:selected").text() + "-" + $("#quarterddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#quarterddl2 option:selected").text() + ")</span>"
    // }
    // $("#outcome_title").html(outcome_title);
    const queryString = $.param(inputs);
    $.ajax({
        url: "/get_soc_wfc_data?" + queryString,
        type: 'GET',
        dataType: "json",
        headers: {
            "cache-control": "no-cache"
        },
        success: function (response) {
            customwaterfallChart(chart_id, response[resp_key], outcome);
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });

})

function customwaterfallChart(appendAt, plotdata, outcome) {
    var margin = {
        top: 40,
        right: 10,
        bottom: 50,
        left: 10
    };

    var width = 1020,
        height = 360 + margin.top - margin.bottom,
        padding = 0.3;
    var yScalePadding = appendAt == "controlWaterfallChart" ? 30 : 0;
    var xAxisTranslate = appendAt == "controlWaterfallChart" ? (height + margin.top / 2) : height;
    var barPositionTranslateY = appendAt == "controlWaterfallChart" ? margin.top / 2 : 0;
    var period_type = $("#period_type").val();
    var outcome_title = ""
    if (outcome == "outcome1") {
        outcome = "outcome1"
    }
    else if (outcome == "outcome2") {
        outcome = "outcome2"
    }
    if (period_type == "year") {
        outcome_title = $("a.active.metricLink").text() + outcome + " (Period: " + $("#scenario2 option:selected").text() + " to " + $("#scenario1 option:selected").text() + ")"
    }
    else if (period_type == "halfyear") {
        outcome_title = $("a.active.metricLink").text() + outcome + " (Period: " + $("#scenario2 option:selected").text() + "-" + $("#halfyearddl1 option:selected").text() + " to " + $("#scenario1 option:selected").text() + "-" + $("#halfyearddl2 option:selected").text() + ")"
    }
    else if (period_type == "month") {
        outcome_title = $("a.active.metricLink").text() + outcome + " (Period: " + $("#scenario2 option:selected").text() + "-" + $("#monthddl2 option:selected").text() + " to " + $("#scenario1 option:selected").text() + "-" + $("#monthddl1 option:selected").text() + ")"
    }
    else {
        outcome_title = $("a.active.metricLink").text() + outcome + " (Period: " + $("#scenario2 option:selected").text() + "-" + $("#quarterddl2 option:selected").text() + " to " + $("#scenario1 option:selected").text() + "-" + $("#quarterddl1 option:selected").text() + ")"
    }


    var container = d3.select("#" + appendAt);
    var cntrwidth = $("#" + appendAt).width() * 0.95;
    var y = d3.scaleLinear()
        .rangeRound([height, yScalePadding]);

    var x = d3.scaleBand()
        .rangeRound([0, cntrwidth])
        .padding(padding);
    container.select("svg").remove();
    var wfchart = container.append("svg")
        .attr("width", cntrwidth + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("preserveAspectRatio", "none")
        .style("background", "#F3F4FE;")
        .classed("svg-content", true)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    var data = plotdata;
    x.domain(data.map(function (d) {
        return d.name;
    }));

    maxY = d3.max(data, function (d) {
        return d.end;
    });
    y.domain(d3.extent([d3.min(data, function (d) {
        return d.end;
    }), maxY, 0, maxY * 1.15]))

    wfchart.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + xAxisTranslate + ")")
        .call(d3.axisBottom(x))
        .selectAll(".tick text")
        .call(MMOUtils.wrap, 0.6 * x.bandwidth())
        .attr("dx", -25);

    //Create Title
    wfchart.append("text")
        .attr("x", cntrwidth / 2)
        .attr("y", -25)
        .attr("class", "chart-title")
        .style("text-anchor", "middle")
        .style("font-family", "sans-serif")
        .style("font-size", 14)
        .text(outcome_title);
    // Hiding y axis
    /*
    wfchart.append("g")
        .attr("class", "y axis yaxisBox")
        .call(d3.axisLeft(y)
            .tickFormat(function (d) {
                return d3.format(".2%")(d)
            }));
    */
    if (appendAt == "controlWaterfallChart_1") {//added _1 to existing  name
        var annotations = [];
        var groups = d3.map(data, function (d) { return d.group; }).keys();
        groups.map(function (group) {
            if (group != "") {
                var filter_data = data.filter(function (d) { return d['group'] == group })
                var total = d3.sum(filter_data.map(function (d) { return d.value }))
                var nodes = d3.map(filter_data, function (d) { return d.name; }).keys();
                annotations.push({
                    note: {
                        label: group + "(" + d3.format('.1%')(total) + ")",
                        lineType: "none",
                        //align: "middle",

                        wrap: 150 //custom text wrapping
                    },
                    className: "above",
                    subject: {
                        //height: height + margin.top,
                        //width: (x.bandwidth() / (1 - padding) - 25) * nodes.length
                        x1: x(nodes[0]),
                        x2: x(nodes[nodes.length - 1]) + 0.6 * x.bandwidth()
                    },
                    disable: ["connector"],
                    x: x(nodes[0]) + (0.6 * x.bandwidth()) / 2,
                    dx: (x(nodes[nodes.length - 1]) - x(nodes[0])) / 2,
                    data: { y: maxY * 1.1 }
                })
            }
        })


        const type = d3.annotationCustomType(
            d3.annotationXYThreshold,
            {
                "note": {
                    "lineType": "none",
                    "orientation": "top",
                    "align": "middle"
                }
            }
        )

        const makeAnnotations = d3.annotation()
            .type(type)
            .notePadding(10)
            .accessors({
                x: function (d) { return x(d.x) },
                y: function (d) { return y(d.y) }
            })
            .annotations(annotations)

        wfchart.append("g")
            .attr("class", "annotation-group")
            .style("font-family", "sans-serif")
            .call(makeAnnotations)
    }

    var bar = wfchart.selectAll(".bar")
        .data(data)
        .enter().append("g")
        .attr("class", function (d) {
            return "bar " + d.class;
        })
        .attr("transform", function (d) {
            return "translate(" + x(d.name) + "," + barPositionTranslateY + ")";
        });

    bar.append("rect")
        .attr("y", function (d) {
            return y(Math.max(d.start, d.end));
        })
        .attr("height", function (d) {
            return Math.abs(y(d.start) - y(d.end));
        })
        .attr("width", 0.6 * x.bandwidth())
        .attr("fill", function (d) {
            if (d.class == 'positive') {
                return "green";
            } else if (d.class == 'negative') {
                return "red";
            } else {
                return "#9E9E9E";
            }
        });
    bar.append("text")
        .attr("x", (0.6 * x.bandwidth()) / 2)
        .attr("y", function (d) {
            return y(Math.max(d.start, d.end)) - 5;
        })
        .text(function (d) {
            return d3.format('.1%')(d.value);
        })
        .attr("text-anchor", "middle")
        .attr("font-size", "0.8rem")
        .attr("font-weight", "bold");

    bar.filter(function (d) {
        return d.class != "total"
    }).append("line")
        .attr("class", "connector")
        .attr("x1", (0.6 * x.bandwidth()) + 5)
        .attr("y1", function (d) {
            return y(d.end);
        })
        .attr("x2", (0.6 * x.bandwidth()) / (1 - padding) - 5)
        .attr("y2", function (d) {
            return y(d.end);
        })
        .attr("stroke", "#424242")
        .attr("stroke-dasharray", 2);

}

function bargraphGenerate(bindto, data) {
    MMOUtils.showLoader()
    var keys = Object.keys(data[0]);
    var values = bindto == 'spendComparison' ? keys.filter(function (d) { return d.indexOf("Spend") > -1; }) :
        keys.filter(function (d) { return ((d.indexOf("Spend") == -1) && (d.indexOf("node_id") == -1) && (d.indexOf("node_name") == -1)); })
    // data.sort(function (x, y) { return d3.descending(x[values[0]], y[values[0]]); });
    var chart = c3.generate({
        bindto: '#' + bindto + '_box',
        size: {
            width: $('#' + bindto + '_box').width() * 0.95,
            height: formatlen(data.length)
        },
        padding: {
            left: 150,
            right: 25,
        },
        data: {
            json: data,
            keys: {
                value: values,
                x: "node_disp_name",
            },
            type: 'bar',
            order: 'desc',
            labels: {
                format: function (v, id, i, j) {
                    if (id) {
                        if (bindto == 'spendComparison') {
                            // Format for 'Spends' chart
                            if (Math.abs(v) >= 1e6) {
                                return "$" + d3.format('.1f')(v / 1e6) + "M";
                            } else if (Math.abs(v) >= 1e3) {
                                return "$" + d3.format('.1f')(v / 1e3) + "K";
                            } else if (v == 0) {
                                return "$0"; // Add a decimal to 0
                            }
                            else {
                                return "$" + d3.format(',s')(v).replace(/G/, "B");
                            }
                        }
                        else {

                            if (Math.abs(v) >= 1e6) {
                                return d3.format('.1f')(v / 1e6) + "M";
                            } else if (Math.abs(v) >= 1e3) {
                                return d3.format('.1f')(v / 1e3) + "K";
                            } else {
                                return d3.format('.1f')(v);
                            }

                        }
                    } else {
                        return "";
                    }
                },
            }
        },
        axis: {
            rotated: true,
            x: {
                type: "category"
            },
            y: {
                show: false,
                padding: {
                    top: 80,
                }
            }
        },
        color: {
            pattern: ['#9E9E9E', '#575757']

        },
        tooltip: {
            format: {
                value: function (v) {
                    if (bindto == 'spendComparison') {
                        // Format for 'Spends' chart
                        if (Math.abs(v) >= 1e6) {
                            return "$" + d3.format('.1f')(v / 1e6) + "M";
                        } else if (Math.abs(v) >= 1e3) {
                            return "$" + d3.format('.1f')(v / 1e3) + "K";
                        } else if (v == 0) {
                            return "$0"; // Add a decimal to 0
                        }
                        else {
                            return "$" + d3.format(',s')(v).replace(/G/, "B");
                        }
                    }
                    else {
                        if (Math.abs(v) >= 1e6) {
                            return d3.format('.1f')(v / 1e6) + "M";
                        } else if (Math.abs(v) >= 1e3) {
                            return d3.format('.1f')(v / 1e3) + "K";
                        }
                        else if (v == 0) {
                            return "0";
                        }
                        else {
                            return d3.format(',s')(v).replace(/G/, "B");
                        }
                    }
                }
            }
        },
        bar: {
            width: {
                ratio: 0.3
            }
        }
    });
    return chart;
}
function formatlen(datalength) {
    if (datalength <= 4) {
        return 400
    }
    else if (datalength <= 8) {
        return 600
    }
    else if (datalength <= 12) {
        return 800
    }
    else {
        return 1000
    }
}
// Reusable tree class
// to be moved to its own file later
MMOTreeDropDown = function (config) {
    // nodes where tree should be rendered
    // maybe we can merge the two into a single node
    // this.treeHeadNode = config.treeHeadNode;
    this.treeBodyNode = config.treeBodyNode;

    // subheaders under each main header
    // (currently same sub-headers repeat for each header)
    // this.subHeaders = config.subHeaders;

    this.resetTree = function () {
        // $(this.treeHeadNode).html("");
        $(this.treeBodyNode).html("");
    };

    this.rebuildTable = function (data) {
        // this.regenerateHead(headers);
        this.regenerateBody(data);
        // TODO check if this id needs to be parameterized
        $("table#dropdowntree").data("simple-tree-table").init();
    };



    this.regenerateBody = function (data) {
        var me = this;
        $(this.treeBodyNode).html('');

        var htmlTemplate = '';
        // for each row
        $.each(data, function (i, el) {
            if (el.node_id > 2000) {
                htmlTemplate += '<tr data-node-id="' + el.node_id + '" data-node-pid="' + el.parent_node_id + '">';
                htmlTemplate += '<td width="250" class=""> <input id="' + el.node_id + '" type="checkbox" class="geolevelItem"/> &nbsp;' + el.node_display_name + '</td>';
                htmlTemplate += '</tr>';
            }
        });
        $(this.treeBodyNode).append(htmlTemplate);
    };


    this.refreshTable = function (headers, data, nodeKeys, updateColumnKey) {
        //this.regenerateHead(headers);
        this.refreshBody(data, nodeKeys, updateColumnKey);
        // TODO check if this id needs to be parameterized
        //$("table#geolevelmarginalreturn_Tbltree").data("simple-tree-table").init();
    };

    this.refreshBody = function (data, nodeKeys, updateColumnKey) {
        // for each row
        $.each(data, function (i, el) {
            cellData = el.node_data;
            // for each of the headers find the column to update and update the field
            var elementId = '';
            $.each(nodeKeys, function (j, d) {
                elementId = d + "_" + MMOUtils.replaceHash(el.node_ref_name) + "_" + updateColumnKey + "_" + el.node_id
                $(elementId).val("--");
            });
        });
    };

};
function geolevelsearch() {
    var value = $(this).val().toLowerCase();
    $("#dropdowntree tr").filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
}
// download water fall data
$('.download-waterfall-data').on('click', function () {
    var chart_type = $(this).attr('data-download');
    var outcome = $("input[name='metric']:checked").val();
    var scenario1 = $("#scenario1").val()
    var scenario2 = $("#scenario2").val()
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl1").val()
    var quarter2 = $("#quarterddl2").val()
    var halfyear1 = $("#halfyearddl1").val()
    var halfyear2 = $("#halfyearddl2").val()
    var month1 = $("#monthddl1").val()
    var month2 = $("#monthddl2").val()
    var year1 = $("#scenario1 option:selected").text();
    var year2 = $("#scenario2 option:selected").text();
    var required_control = true

    var inputs = {}
    inputs.scenario_1 = scenario1
    inputs.scenario_2 = scenario2
    inputs.year1 = year1
    inputs.year2 = year2
    inputs.period_type = period_type
    inputs.quarter1 = quarter1
    inputs.quarter2 = quarter2
    inputs.halfyear1 = halfyear1
    inputs.halfyear2 = halfyear2
    inputs.month1 = month1
    inputs.month2 = month2
    inputs.outcome = outcome,
        inputs.required_control = required_control,
        inputs.chart_type = chart_type

    var period_type = $("#period_type").val();
    var active_tab = $('a[data-toggle="tab"].active').text();
    var outcome_title = ""
    var filename = ""
    if (period_type == "year") {
        outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + ")"
    }
    else if (period_type == "halfyear") {
        outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + "-" + $("#halfyearddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#halfyearddl2 option:selected").text() + ")"
    }
    else if (period_type == "month") {
        outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + "-" + $("#monthddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#monthddl2 option:selected").text() + ")"
    }
    else {
        outcome_title = $("a.active.metricLink").text() + " (Period: " + $("#scenario1 option:selected").text() + "-" + $("#quarterddl1 option:selected").text() + " to " + $("#scenario2 option:selected").text() + "-" + $("#quarterddl2 option:selected").text() + ")"
    }

    filename = active_tab + "-" + outcome_title + '.csv'
    document.location.href = '/download_waterfall_data?year1=' + year1
        + '&year2=' + year2 + '&period_type=' + period_type + '&quarter1=' + quarter1
        + '&quarter2=' + quarter2 + '&halfyear1=' + halfyear1 + '&halfyear2=' + halfyear2
        + '&outcome=' + outcome + '&required_control=' + required_control
        + '&chart_type=' + chart_type + "&filename=" + filename

})

$(document).ajaxError(function myErrorHandler(event, xhr, ajaxOptions, thrownError) {
    if (xhr.status == 303) {
        $("#error_message").html(xhr.responseText)
    }
    $('#app_error').modal('show');
})
$("#scenario1").on("change", function () {
    var selectedValue = $(this).val();
    localStorage.setItem('scenario2Value', selectedValue);
}
)

$("#scenario2").on("change", function () {
    var selectedValue = $(this).val();
    localStorage.setItem('scenario1Value', selectedValue);
}
)