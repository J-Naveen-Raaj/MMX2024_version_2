var ScenarioTree = {};
var NodeTree = {};
var NodeTree2 = {};
var NodeTreecompare = {};
var ScenariosummaryBox = {};
var scenarioName1, scenarioName2;
var count = 3;
var className = ".modalselectBox";
var DEFAULT_SCENARIO_ONE = 1;
var DEFAULT_SCENARIO_TWO = 2;
var defaultSelectedNode = 2003;
var scenario_1_selected = 1
var scenario_2_selected = 2
var metricLevelData = {
    "Overall-Change": {},
    "outcome2": {},
    "outcome1": {},
    "coutcome2": {},
    "coutcome1": {}
};


SUBHEADERS_NTFAI = [{
    title: 'Spend($)',
    editable: false,
    custom: false,
    key: 'spend'
},
{
    title: 'Outcome1',
    editable: false,
    custom: false,
    key: 'outcome1'
},
{
    title: 'coutcome1($)',
    editable: false,
    custom: false,
    key: 'cpa'
}
]
SUBHEADERS_CHANGE = [{
    title: 'Spend(%)',
    editable: false,
    custom: false,
    key: 'spend'
}, {
    title: 'Outcome1s(%)',
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
SUBHEADERS_CHANGE_SU = [{
    title: 'Spend(%)',
    editable: false,
    custom: false,
    key: 'spend'
}, {
    title: 'Outcome2s',
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
SUBHEADERS_EXTAI = [{
    title: 'Spend($)',
    editable: false,
    custom: false,
    key: 'spend'
},
{
    title: 'Outcome2s',
    editable: false,
    custom: false,
    key: 'outcome2'
},
{
    title: 'coutcome2($)',
    editable: false,
    custom: false,
    key: 'cpa'
}
]

var ScenariosummaryBox = {};
var scenarioName1, scenarioName2;
var count = 4;
var summaryData = [{
    "name": "Scenario 1",
    "scenario2": 0,
    "scenario1": 40
}, { "name": "Scenario 2", "scenario2": 30, "scenario1": 40 }];

// will need to move this tree config to a config file for easy editing

var HEADER_STRUCTURE = {

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
    ]
};

var ScenariosummaryBox = {};
var scenarioName1, scenarioName2;
var count = 4;
var summaryData = [{
    "name": "Scenario 1",
    "scenario2": 0,
    "scenario1": 40
},
{
    "name": "Scenario 2",
    "scenario2": 30,
    "scenario1": 40
}
];

$(function () {
    document.addEventListener('click', function (event) {
        var dropdowns = document.querySelectorAll('.main-dropdown-menu');
        var maindropdowns = document.querySelectorAll('.maindropdown');

        var clickedInsideDropdown = false;

        for (var i = 0; i < dropdowns.length; i++) {
            var dropdown = dropdowns[i];
            var maindropdown = maindropdowns[i];

            if (dropdown.contains(event.target) || maindropdown.contains(event.target)) {
                clickedInsideDropdown = true;
            }
        }

        if (!clickedInsideDropdown) {
            $('.main-dropdown-menu').hide();
            $(".maindropdown").removeClass('active');
        }
    });
    timeperiod()
    $(".downloadoutcome").show();

    $('a.outcome-comparison').on('click', function () {
        if ($(this).attr('href') === '#outcome_comparison') {
            $(".downloadoutcome").show();
        } else {
            $(".downloadoutcome").hide();
        }
    });
    // MMOUtils.hideLoader();
    ScenariosummaryBox = new summaryBox({
        summarydataBox: '.summaryBox'
    });
    NodeTreecompare = new MMOTreeDropdown({
        treeBodyNode: '.ddl'
    });

    ScenarioTree = new MMOTree({
        treeHeadNode: '.treeDataHeader',
        treeBodyNode: '.treeDatabody',
        headerStructure: HEADER_STRUCTURE,
        formatCellData: formatCellData,
        comparision: true
    });

    MMOUtils.showLoader();
    // $("#Compare-metricTxtBox").hide();
    $(".view-type.toggle-btn")
        .prop("disabled", true)
        .css("cursor", "not-allowed");

    scenariolist(true);

    $("body").on("click", "a.toggle-btn", toggleContent);
    $("body").on("click", "#duetoanalysisapplyBtn", selectedLevels);
    $("body").on("click", "#compareBarChartapplyBtn", selectedLevelsroa)
    $("body").on("click", "#compareBarChartapplyBtncompare", selectedLevelsgraph) //similar to soc reporting for to graphs add your function
    $("body").on("keyup", "#geolevelsearchBox", geolevelsearch);
    $("body").on("keyup", "#geolevelsearchBox2", geolevelsearch);
    $("body").on("keyup", "#geolevelsearchBox3", geolevelsearch3);
    // $("body").on("click", "a.outcome-comparison[href='#kpiOutputComparison']", function () {
    //     scenariolist()
    // });
    $("body").on("click", "a.outcome-comparison[href='#outcome_comparison']", function () {
        var period_type = $("#period_type").val();
        if (period_type == "quarter") {
            $(".quarterddl-item").show()
            $(".monthddl-item").hide()
        }
        else if (period_type == "month") {
            $(".quarterddl-item").hide()
            $(".monthddl-item").show()
        }
        else {
            $(".quarterddl-item").hide()
            $(".monthddl-item").hide()
        }
    });
    $("body").on("click", "a.outcome-comparison[href='#duetoanalysis']", function () {
        var period_type = $("#period_type1").val();
        if (period_type == "quarter") {
            $(".quarterddl-item").show()
            $(".monthddl-item").hide()
        }
        else if (period_type == "month") {
            $(".quarterddl-item").hide()
            $(".monthddl-item").show()
        }
        else {
            $(".quarterddl-item").hide()
            $(".monthddl-item").hide()
        }
        if (period_type == "year") {
            $(".scenariolabel").hide();
        }
        else {
            $(".scenariolabel").show();
        }
        marginalreturnGeolevelTree()
        NodeTree = new MMOTreeDropdown({
            treeBodyNode: '.treeDatabodyddl',
        });

        var selectedNodes = { node: defaultSelectedNode }
        $.each($("input[class='geolevelItem']:checked"), function () {
            selectedNodes['node'] = $(this).attr("id");
            $("#node_name").html($(this).data('node-name'));
        });
        setTimeout(function () {
            dueToAnalysisChartgenerate(selectedNodes);
        }, 500);
    });
    $("body").on("click", "#compareBtn2", function () {
        marginalreturnGeolevelTree()
        NodeTree = new MMOTreeDropdown({
            treeBodyNode: '.treeDatabodyddl',
        });

        var selectedNodes = { node: defaultSelectedNode }
        $.each($("input[class='geolevelItem']:checked"), function () {
            selectedNodes['node'] = $(this).attr("id");
            $("#node_name").html($(this).data('node-name'));
        });
        dueToAnalysisChartgenerate(selectedNodes);
    });
    // $("body").on("click", "a.outcome-comparison[href='#spendvsoutcome']", function () {
    //     marginalreturnGeolevelTree2()
    //     NodeTree2 = new MMOTreeDropdown({
    //         // treeHeadNode: '.treeDataHeader',
    //         treeBodyNode: '.spendddl',
    //         // these are specific to the screen
    //         // subHeaders: SUBHEADERS
    //     });

    //     var selectedNodes = { node: defaultSelectedNode }
    //     $.each($("input[class='geolevelItem']:checked"), function () {
    //         selectedNodes['node'] = $(this).attr("id");
    //         $("#node_name").html($(this).data('node-name'));
    //     });

    //     get_romi_cpa_data();
    // });
    $("body").on("change", "#scenario1,#scenario2,#period_type1,#quarterddl1,#quarterddl2,#monthddl1,#monthddl2", selectedScenarios);
    $("body").on("click", ".geolevelItem", function () {
        if ($(".horizontal-menu a.active").attr("href") === '#duetoanalysis') {
            $('.geolevelItem').not(this).prop('checked', false);
        }
    });
});
function scenariolist(onLoad = false) {
    MMOUtils.showLoader()
    $.ajax({
        url: '/getScenarioList',
        type: 'GET',
        dataType: "json",
        processData: false,
        contentType: false,
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
        success: function (response) {
            var scenariosListdata = response;
            $("#selectscnrio_one").html();
            $("#selectscnrio_two").html();
            for (key in scenariosListdata) {
                if (scenariosListdata[key] == 'Base 2021') {
                    DEFAULT_SCENARIO_ONE = key
                    scenario_1_selected = key
                }
                else if (scenariosListdata[key] == 'Base 2022') {
                    DEFAULT_SCENARIO_TWO = key
                    scenario_2_selected = key
                }
            }
            MMOUtils.buildDDlFromList("#selectscnrio_one", scenariosListdata, "");
            MMOUtils.buildDDlFromList("#selectscnrio_two", scenariosListdata, "");
            // MMOUtils.buildDDlFromList("#opt_scenarios_1", scenariosListdata, "");
            // MMOUtils.buildDDlFromList("#opt_scenarios_2", scenariosListdata, "");
            MMOUtils.buildDDlFromList("#selectscnrio_2", scenariosListdata, "");
            MMOUtils.buildDDlFromList("#selectscnrio_1", scenariosListdata, "");
            MMOUtils.buildDDlFromList("#selectscnrio_3", scenariosListdata, "");
            MMOUtils.buildDDlFromList("#selectscnrio_4", scenariosListdata, "");


            $("#selectscnrio_one").val(scenario_2_selected);
            $("#selectscnrio_two").val(scenario_1_selected);
            // $('#opt_scenarios_1').val(scenario_1_selected);
            // $('#opt_scenarios_2').val(scenario_2_selected);
            $("#selectscnrio_1").val(scenario_1_selected);
            $("#selectscnrio_2").val(scenario_2_selected);
            $("#selectscnrio_3").val(DEFAULT_SCENARIO_ONE);
            $("#selectscnrio_4").val(DEFAULT_SCENARIO_TWO);

            var scenario1 = $("#selectscnrio_one").val();
            var scenario2 = $("#selectscnrio_two").val();


            $("#selectscnrio_two").find('option[value="' + scenario1 + '"]').hide();
            $("#selectscnrio_one").find('option[value="' + scenario2 + '"]').hide();

            $("#selectscnrio_one").selectpicker("refresh");
            $("#selectscnrio_two").selectpicker("refresh");
            // $("#opt_scenarios_1").selectpicker("refresh");
            // $("#opt_scenarios_2").selectpicker("refresh");
            $("#selectscnrio_1").selectpicker("refresh");
            $("#selectscnrio_2").selectpicker("refresh");
            $("#selectscnrio_3").selectpicker("refresh");
            $("#selectscnrio_4").selectpicker("refresh");
            MMOUtils.hideLoader();
            if (onLoad) {
                PageBodyEvents();
            }

        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
}
$("#selectscnrio_one").on("change", function () {
    scenario_2_selected = $(this).val();
    $("#selectscnrio_2").val(scenario_2_selected);
    $("#selectscnrio_2").find('option[value="' + scenario_2_selected + '"]').hide();
    $("#selectscnrio_2").selectpicker("refresh");
}
)

$("#selectscnrio_two").on("change", function () {
    scenario_1_selected = $(this).val();
    $("#selectscnrio_1").val(scenario_1_selected);
    $("#selectscnrio_1").find('option[value="' + scenario_1_selected + '"]').hide();
    $("#selectscnrio_1").selectpicker("refresh");
}
)
function selectedLevelsgraph() {
    MMOUtils.showLoader();
    var checkedItems = [];
    var selectedNodes = {}
    $.each($("input[class='geolevelItem']:checked"), function () {
        checkedItems.push($(this).attr("id"));
    });

    selectedNodes['nodes'] = checkedItems;

    var scenario1 = $("#selectscnrio_one").val()
    var scenario2 = $("#selectscnrio_two").val()
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl7").val()
    var quarter2 = $("#quarterddl7").val()
    var month1 = $("#monthddl7").val()
    var month2 = $("#monthddl7").val()
    var outcome = $("input[name='metric']:checked").val();
    var halfyear1 = $("#halfyearddl1").val()
    var halfyear2 = $("#halfyearddl2").val()
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
    inputs.outcome = outcome
    inputs.required_control = true
    inputs.nodes = checkedItems
    var queryString = `scenario_1=${scenario1}&scenario_2=${scenario2}&period_type=${period_type}&quarter1=${quarter1}&quarter2=${quarter2}&halfyear1=${halfyear1}&halfyear2=${halfyear2}&month1=${month1}&month2=${month2}&outcome=${outcome}&required_control=true&nodes=${checkedItems.join(',')}`;

    $.ajax({
        url: "/get_scenario_comarison_by_node?" + queryString,
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
            MMOUtils.hideLoader()
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
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
                                return "$ " + d3.format('.1f')(v / 1e6) + "M";
                            } else if (Math.abs(v) >= 1e3) {
                                return "$ " + d3.format('.1f')(v / 1e3) + "K";
                            } else if (v == 0) {
                                return "$ 0"; // Add a decimal to 0
                            }
                            else {
                                return "$ " + d3.format(',s')(v).replace(/G/, "B");
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
                }

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
                ratio: 0.4
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
        return 2000
    }
}
function selectedScenarios(e) {
    e.preventDefault();
    var period_type = $("#period_type1").val();
    if (period_type == "year") {
        $(".quarterddl-item").hide();
        $(".monthddl-item").hide();
        $(".scenariolabel").hide();
    }
    else if (period_type == "month") {
        $(".quarterddl-item").hide();
        $(".monthddl-item").show()
        $(".scenariolabel").show();
    }
    else {
        $(".quarterddl-item").show();
        $(".monthddl-item").hide()
        $(".scenariolabel").show();
    }
    var selectedNodes = { node: defaultSelectedNode }
    $.each($("input[class='geolevelItem']:checked"), function () {
        selectedNodes['node'] = $(this).attr("id");
        $("#node_name").html($(this).data('node-name'));
    });

    dueToAnalysisChartgenerate(selectedNodes);
}
function dueToAnalysisChartgenerate(selectedNodes) {
    MMOUtils.showLoader();
    var scenario1 = $("#selectscnrio_1").val();
    var scenario2 = $("#selectscnrio_2").val();
    var period_type = $("#period_type1").val();
    var year1 = $("#selectscnrio_1 option:selected").text();
    var year2 = $("#selectscnrio_2 option:selected").text();
    var quarter1 = $("#quarterddl1").val()
    var quarter2 = $("#quarterddl2").val()
    var month1 = $("#monthddl1").val()
    var month2 = $("#monthddl2").val()
    if (period_type == "year") {
        period_1 = $("#scenario1 option:selected").text();
        period_2 = $("#scenario2 option:selected").text();
    }
    else if (period_type == "month") {
        period_1 = month1;
        period_2 = month2;
    }
    else {
        period_1 = quarter1;
        period_2 = quarter2;
    }
    var inputs = {
        "scenario_1": scenario1,
        "scenario_2": scenario2,
        "period_type": period_type,
        "year_1": year1,
        "year_2": year2,
        "period_1": period_1,
        "period_2": period_2,
        "node": selectedNodes['node']
    }
    const queryString = $.param(inputs);
    $.ajax({
        url: '/get_comparision_due_to_analysis?' + queryString,
        type: 'GET',
        dataType: "json",
        success: function (response) {
            $("#DueToAnalysisMainBox").html("");
            outcomes = Object.keys(response)
            outcomes.map(function (d) {
                var htmlTemplate = '';
                htmlTemplate += '<div class="graph-box px-0"><h4 class="text-center">' + MMOUtils.replaceUnderscore(d) + '</h4><div class="graph graph1 pt-0" id="' + d + '_box" style="height: 520px;width:100%"></div></div>'
                $("#DueToAnalysisMainBox").append(htmlTemplate);
                $('#' + d + '_box').html("");
                customwaterfallChart(d + "_box", response[d]);
            })

            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
}

function customwaterfallChart(appendAt, plotdata) {
    var margin = {
        top: 50,
        right: $('#' + appendAt).width() * .02,
        bottom: 30,
        left: $('#' + appendAt).width() * .13
    };
    var width = $('#' + appendAt).width() * 0.85,
        height = 360 - margin.top - margin.bottom,
        padding = 0.3;

    var container = d3.select("#" + appendAt);
    var cntrwidth = width
    var y = d3.scaleLinear()
        .rangeRound([height, 0]);

    var x = d3.scaleBand()
        .rangeRound([0, cntrwidth])
        .padding(0.1);
    container.select("svg").remove();
    var wfchart = container.append("svg")
        .attr("width", cntrwidth + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("preserveAspectRatio", "none")
        // .attr("id", appendAt)
        .classed("svg-content", true)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    var data = plotdata;
    x.domain(data.map(function (d) {
        return d.name;
    }));

    y.domain([d3.min(data, function (d) {
        return d.start;
    }), d3.max(data, function (d) {
        return d.end;
    })])

    wfchart.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x))
        .selectAll(".tick text")
        .call(MMOUtils.wrap, x.bandwidth());


    // wfchart.append("g")
    //     .attr("class", "y axis yaxisBox")
    //     .call(d3.axisLeft(y)
    //         .tickFormat(function (d) {
    //             return d3.format(".2s")(d).replace(/G/, "B")
    //         }));

    var bar = wfchart.selectAll(".bar")
        .data(data)
        .enter().append("g")
        .attr("class", function (d) {
            return "bar " + d.class;
        })
        .attr("transform", function (d) {
            return "translate(" + x(d.name) + ",0)";
        });

    bar.append("rect")
        .attr("y", function (d) {
            return y(Math.max(d.start, d.end));
        })
        .attr("height", function (d) {
            return Math.abs(y(d.start) - y(d.end));
        })
        .attr("width", 0.8 * x.bandwidth())
        .attr("fill", function (d) {
            if (d.class == 'positive') {
                return "#00AA93";
            } else if (d.class == 'negative') {
                return "#c00000";
            } else {
                return "#98A4AE";
            }
        });
    bar.append("text")
        .attr("x", x.bandwidth() / 2)
        .attr("y", function (d) {
            return y(Math.max(d.start, d.end)) - 5;
        })
        .text(function (d) {
            return d3.format('.2s')(d.value).replace(/G/, "B");
        })
        .attr("text-anchor", "middle")
        .attr("font-size", "0.8rem")
        .attr("font-weight", "bold");
    bar.filter(function (d) {
        return d.class != "total"
    }).append("line")
        .attr("class", "connector")
        .attr("x1", x.bandwidth() + 0)
        .attr("y1", function (d) {
            return y(d.end);
        })
        .attr("x2", x.bandwidth() / (1 - padding) - 20)
        .attr("y2", function (d) {
            return y(d.end);
        })
        .attr("stroke", "#424242")
        .attr("stroke-dasharray", 2);

}
function marginalreturnGeolevelTree() {
    MMOUtils.showLoader();

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
            NodeTree.rebuildTable(response);

            $("#" + defaultSelectedNode).prop('checked', true);
            // hide the loader
            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });

}
function marginalreturnGeolevelTree2() {

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
            NodeTree2.rebuildTable(response);
            // $("#touchpoints_ddl").hide();
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });

}
function marginalreturnGeolevelTreecompare() {
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
            NodeTreecompare.rebuildTable(response);
            // $("#touchpoints_ddl").hide();
            MMOUtils.hideLoader()
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });

}
function load_all_dropdown_values() {
    scenario1 = $("#selectscnrio_3").val()
    scenario2 = $("#selectscnrio_4").val()
    period_type = $("#period_type2").val();
    quarter1 = $("#quarterddl3").val()
    quarter2 = $("#quarterddl4").val()
    month1 = $("#monthddl3").val()
    month2 = $("#monthddl4").val()
}
$("#period_type2").on("change", function () {
    var period_type = $(this).val();
    if (period_type == "year") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").hide()
    }
    else if (period_type == "month") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").show()
    }
    else {
        $(".quarterddl-item").show();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").hide()
    }
})
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
    d3.select('#' + chartID).selectAll("path").attr("fill", "none");
    //fix no axes
    d3.select('#' + chartID).selectAll("path.domain").attr("stroke", "black");
    //fix no tick
    d3.select('#' + chartID).selectAll(".tick line").attr("stroke", "black");
    saveSvgAsPng($("#" + chartID).find('svg')[0], chart_name + ".png");
})
function selectedLevelsroa() {

    // get_romi_cpa_data()
    if ($(".maindropdown").hasClass('active')) {
        $('.main-dropdown-menu').hide();
        $(".maindropdown").removeClass('active');
    }
    else {
        $(".maindropdown").addClass('active');
        $('.main-dropdown-menu').show();
    }
}


function PageBodyEvents() {
    var period_type = $("#period_type").val();
    var period = $("#quarterddl7").val();
    var month = $("#monthddl7").val();
    var Stringparams = `scenario_1=${DEFAULT_SCENARIO_ONE}&scenario_2=${DEFAULT_SCENARIO_TWO}&period_type=${period_type}&quarter=${period}&month=${month}&outcome="Overall-Change"&required_control=false`
    $(".preloader-progress").show()
    MMOUtils.hideLoader()
    var progress = $(".loading-progress").progressTimer({
        onFinish: function () {
            // Callback function when the timer finishes
            $(".preloader-progress").hide()
        },
    });
    // Ajax call to the API
    var startTime = new Date().getTime();
    $.ajax({
        url: "/get_spend_comparison_summary?" + Stringparams,
        type: 'GET',
        dataType: "json",
        success: function (response) {
            var endTime = new Date().getTime();
            var timeTaken = (endTime - startTime) / 1000;
            $("#overallchange").prop("checked", true);
            $("#outcome1", "#outcome2").prop("checked", false);
            // MMOUtils.hideLoader();
            ScenariosummaryBox.comparesummaryBlocks(response, "Overall-Change", metricLevelData);
            progress.progressTimer('setTime', timeTaken);
            progress.progressTimer('complete');
        },
        error: function (error) {
            MMOUtils.hideLoader();
            progress.progressTimer('error', {
                errorText: 'ERROR!',
                onFinish: function () {
                    alert('There was an error processing your information!');
                }
            });
            $("#romiCpaModalLabel").text("Error");
            $(".modal-header").addClass("btn-danger").removeClass("btn-success");
            $(".modal-body").text(error.responseText);
            return $("#romiCpaModal").modal('show');
        }
    });
    var initialMetrictype = "Overall-Change";

    $(".compareBtn").on("click", function () {

        /****** Need to Be uncomment */
        MMOUtils.showLoader();
        var viewtype = $("a.toggle-btn.active").attr('href');
        if (viewtype == '#tabular') {
            $("#metrcisBox").show();
            $("#Compare-metricTxtBox").show();
            $("#Compare-metricTblBox").show();

            var scenario1 = $("#selectscnrio_two").val();
            var scenario2 = $("#selectscnrio_one").val();
            var selcetMetric = $("input[name='metric']:checked").val();
            var period_type = $("#period_type").val();
            var period = $("#quarterddl7").val();
            var month = $("#monthddl7").val();
            if (period_type == "quarter") {
                $(".quarterddl-item").show()
                $(".monthddl-item").hide()
            }
            else if (period_type == "month") {
                $(".quarterddl-item").hide()
                $(".monthddl-item").show()
            }
            else {
                $(".quarterddl-item").hide()
                $(".monthddl-item").hide()
            }
            var Stringparams = `scenario_1=${scenario1}&scenario_2=${scenario2}&period_type=${period_type}&quarter=${period}&month=${month}&outcome=${selcetMetric}&required_control=false`
            $.ajax({
                url: "/get_spend_comparison_summary?" + Stringparams,
                type: 'GET',
                dataType: "json",
                success: function (response) {
                    ScenariosummaryBox.comparesummaryBlocks(response, selcetMetric, metricLevelData);
                    if (selcetMetric == "Overall-Change") {
                        // $("#Compare-metricTxtBox").hide();
                        $(".view-type.toggle-btn")
                            .prop("disabled", true)
                            .css("cursor", "not-allowed");
                        $("#Compare-metricTblBox").hide();
                        MMOUtils.hideLoader();
                    } else {
                        $("#Compare-metricTblBox").show();
                        $("#Compare-metricTxtBox").show();
                        $(".view-type.toggle-btn")
                            .prop("disabled", false)
                            .css("cursor", "pointer");
                        get_spend_comparison(scenario1, scenario2, period_type, selcetMetric, period, month)

                    }
                },
                error: function (xhr, errorThrown) {
                    if (xhr.status === 400) {
                        MMOUtils.hideLoader();
                        $("#romiCpaModalLabel").text("Error");
                        $(".modal-header").addClass("btn-danger").removeClass("btn-success");
                        $(".modal-body").text(xhr.responseJSON.error);
                        return $("#romiCpaModal").modal('show');
                    }
                }
            });
        }
        else {
            $("#Compare-graphs").show();
            selectedLevelsgraph()
            $("#Compare-metricTblBox").hide();
            $("#touchpoints_ddl2").show();
            marginalreturnGeolevelTreecompare()
            $("#comparesummaryHolder").hide();
        }

    })

    // $(".download_kpi_output_comparison_file").on("click", function () {
    //     var scenario_one = $("#opt_scenarios_1").val();
    //     var scenario_two = $("#opt_scenarios_2").val();
    //     document.location.href = "/download_kpi_output_comparison?scenario_one=" + scenario_one + "&scenario_two=" + scenario_two
    // });

    $("#period_type,#quarterddl7,#monthddl7").on("change", function () {

        /****** Need to Be uncomment */
        MMOUtils.showLoader();
        $("#metrcisBox").show();
        $("#Compare-metricTxtBox").show();
        // $("#Compare-metricTblBox").show();

        var scenario1 = $("#selectscnrio_two").val();
        var scenario2 = $("#selectscnrio_one").val();
        var selcetMetric = $("input[name='metric']:checked").val();
        var period_type = $("#period_type").val();
        var period = $("#quarterddl7").val();
        var month = $("#monthddl7").val();
        if (period_type == "quarter") {
            $(".quarterddl-item").show()
            $(".monthddl-item").hide()
        }
        else if (period_type == "month") {
            $(".quarterddl-item").hide()
            $(".monthddl-item").show()
        }
        else {
            $(".quarterddl-item").hide()
            $(".monthddl-item").hide()
        }
        var viewtype = $("a.toggle-btn.active").attr('href');
        var Stringparams = `scenario_1=${scenario1}&scenario_2=${scenario2}&period_type=${period_type}&quarter=${period}&month=${month}&outcome=${selcetMetric}&required_control=false`
        if (viewtype == '#tabular') {
            $("#Compare-metricTblBox").show();
            $("#comparesummaryHolder").show();
            $("#touchpoints_ddl2").hide();
            $("#Compare-graphs").hide();
            $.ajax({
                url: "/get_spend_comparison_summary?" + Stringparams,
                type: 'GET',
                dataType: "json",
                success: function (response) {
                    var viewtype = $("a.toggle-btn.active").attr('href');
                    ScenariosummaryBox.comparesummaryBlocks(response, selcetMetric, metricLevelData);
                    if (selcetMetric == "Overall-Change") {
                        // $("#Compare-metricTxtBox").hide();
                        $("#Compare-metricTblBox").hide();
                        $(".view-type.toggle-btn")
                            .prop("disabled", true)
                            .css("cursor", "not-allowed");
                        MMOUtils.hideLoader();
                    } else {
                        $("#Compare-metricTxtBox").show();
                        $("#Compare-metricTblBox").show();
                        $(".view-type.toggle-btn")
                            .prop("disabled", false)
                            .css("cursor", "pointer");
                        get_spend_comparison(scenario1, scenario2, period_type, selcetMetric, period, month)
                    }
                },
                error: function (error) {
                    MMOUtils.hideLoader();
                    $("#romiCpaModalLabel").text("Error");
                    $(".modal-header").addClass("btn-danger").removeClass("btn-success");
                    $(".modal-body").text(error.responseText);
                    return $("#romiCpaModal").modal('show');
                }
            });
        }
        else {
            $("#Compare-graphs").show();
            selectedLevelsgraph()
            $("#Compare-metricTblBox").hide();
            $("#touchpoints_ddl2").show();
            // marginalreturnGeolevelTreecompare()
            $("#comparesummaryHolder").hide();
        }

    })

    $(document).on("click", "a.graphicon", function () {
        var datanodeid = $(this).data('parentid');
        var childname = $(this).parent('td').text();
        $("#scenarioComparisonGraph").modal('show');
        $(".geolevelTxtinmodal").html(childname);
        if (!$(this).hasClass('active')) {
            $(this).addClass('active');
        }
    });

    $(document).on("dblclick", "table#geolevelcompare_Tbltree tbody.comparetreeDatabody tr.has-comparison-data", function () {
        var datanodeid = $(this).data('node-id');
        var childname = $(this).find('td:first-child').text();
        $("#scenarioComparisonGraph").modal('show');
        $(".geolevelTxtinmodal").html(childname);
        if (!$(this).hasClass('active')) {
            $(this).addClass('active');
        }
    });

    $(".metricLink").click(function (e) {
        e.preventDefault();
        MMOUtils.showLoader();
        if ($(".horizontal-menu .metricLink").hasClass("active")) {
            $(".horizontal-menu .metricLink").removeClass("active");
        }
        $(this).addClass("active");
        var selcetMetric = $("input[name='metric']:checked").val();
        var scenario1 = $("#selectscnrio_two").val();
        var scenario2 = $("#selectscnrio_one").val();
        var period_type = $("#period_type").val();
        var period = $("#quarterddl7").val();
        var month = $("#monthddl7").val();
        if (period_type == "quarter") {
            $(".quarterddl-item").show()
            $(".monthddl-item").hide()
        }
        else if (period_type == "month") {
            $(".quarterddl-item").hide()
            $(".monthddl-item").show()
        }
        else {
            $(".quarterddl-item").hide()
            $(".monthddl-item").hide()
        }
        var Stringparams = `scenario_1=${scenario1}&scenario_2=${scenario2}&period_type=${period_type}&quarter=${period}&month=${month}&outcome="outcome2"&required_control=false`
        $.ajax({
            url: "/get_spend_comparison_summary?" + Stringparams,
            type: 'GET',
            dataType: "json",
            success: function (response) {
                ScenariosummaryBox.comparesummaryBlocks(response, selcetMetric, metricLevelData);
                if (selcetMetric == "Overall-Change") {
                    $("#overallchange").prop("checked", true);
                    $("#outcome1", "#outcome2").prop("checked", false);
                    // $("#Compare-metricTxtBox").hide();
                    $("#Compare-metricTblBox").hide();
                    $("#comparesummaryHolder").show();
                    $("#Compare-graphs").hide();
                    $(".view-type.toggle-btn")
                        .prop("disabled", true)
                        .css("cursor", "not-allowed");
                    $("#touchpoints_ddl2").hide();

                    MMOUtils.hideLoader();
                } else {
                    if (selcetMetric == "outcome2") {
                        $("#outcome2").prop("checked", true);
                        $("#outcome1", "#overallchange").prop("checked", false);
                    }
                    else if (selcetMetric == "outcome1") {
                        $("#outcome1").prop("checked", true);
                        $("#outcome2", "#overallchange").prop("checked", false);
                    }
                    $("#Compare-metricTblBox").show();
                    $("#Compare-metricTxtBox").show();
                    $(".view-type.toggle-btn")
                        .prop("disabled", false)
                        .css("cursor", "pointer");
                    var viewtype = $("a.toggle-btn.active").attr('href');
                    if (viewtype == '#tabular') {
                        get_spend_comparison(scenario1, scenario2, period_type, selcetMetric, period, month)
                    }
                    else {
                        $("#Compare-graphs").show();
                        selectedLevelsgraph()
                        $("#Compare-metricTblBox").hide();
                        $("#comparesummaryHolder").hide();
                        if ($(".maindropdown").hasClass('active')) {
                            $('.main-dropdown-menu').hide();
                            $(".maindropdown").removeClass('active');
                        }
                    }
                }
            },
            error: function (error) {
                MMOUtils.hideLoader();
                $("#romiCpaModalLabel").text("Error");
                $(".modal-header").addClass("btn-danger").removeClass("btn-success");
                $(".modal-body").text(error.responseText);
                return $("#romiCpaModal").modal('show');
            }
        });
    });


    $(".downloadscenario").on("click", function () {
        var outcome = $("input[name='metric']:checked").val();
        var scenario1 = $("#selectscnrio_two").val();
        var scenario2 = $("#selectscnrio_one").val();
        var period_type = $("#period_type").val();
        var download_type = $(this).attr('download-type')
        MMOUtils.showLoader();
        if (download_type === 'csv') {
            $.fileDownload("/download_scenario_comparisons?scenarios=[" + scenario1 + "," + scenario2 + "]&outcome=" + outcome + "&period_type=" + period_type + "&download_type=csv", {
                httpMethod: 'GET',
                successCallback: function (data) {
                    MMOUtils.hideLoader();
                },
                failCallback: function (data) {
                    MMOUtils.hideLoader();
                }
            })
        } else {
            $.fileDownload("/download_scenario_comparisons?scenarios=[" + scenario1 + "," + scenario2 + "]&outcome=" + outcome + "&period_type=" + period_type + "&download_type=excel", {
                httpMethod: 'GET',
                successCallback: function (data) {
                    MMOUtils.hideLoader();
                },
                failCallback: function (data) {
                    MMOUtils.hideLoader();
                }
            })
        }
    })

}
// $('#btn_compare_romi_cpa').on('click', get_romi_cpa_data)

function get_spend_comparison(scenario1, scenario2, period_type, selcetMetric, period, month) {
    var queryString = `scenario_1=${scenario1}&scenario_2=${scenario2}&period_type=${period_type}&outcome=${selcetMetric}&quarter=${period}&month=${month}&required_control=true`;
    $.ajax({
        url: "/get_spend_comparison?" + queryString,
        type: 'GET',
        dataType: "json",
        success: function (response) {
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

            ScenarioTree.headerStructure = response['headers'];
            ScenarioTree.refreshTable(response['spends'], selcetMetric, 'spend');
            ScenarioTree.refreshTable(response['outcomes'], selcetMetric, selcetMetric);
            ScenarioTree.refreshTable(response['cpa'], selcetMetric, 'cpa');
            //setPctValues();
            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });
}


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

function hideSelectedValuesInComboBoxes() {

    for (var i = 1; i <= 6; i++) {
        var curntselectedVal = $("#modalscenarioslistBox_" + i).val();
        $(".modalselectBox").not("#modalscenarioslistBox_" + i).find('option[value="' + curntselectedVal + '"]').hide();
        $(".modalselectBox").not("#modalscenarioslistBox_" + i).selectpicker("refresh");
    }
}

$("#addscenario").on('shown.bs.modal', function () {
    MMOUtils.showLoader();

    $.ajax({
        url: '/getScenarioList',
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
            var scenariosListdata = response;
            $("#modalscenarioslistBox_1").html();
            $("#modalscenarioslistBox_2").html();

            MMOUtils.buildDDlFromList("#modalscenarioslistBox_1", scenariosListdata, "");
            MMOUtils.buildDDlFromList("#modalscenarioslistBox_2", scenariosListdata, "");

            var scenario1 = $("#selectscnrio_one").val();
            var scenario2 = $("#selectscnrio_two").val();

            $("#modalscenarioslistBox_1").val(scenario1);
            $("#modalscenarioslistBox_2").val(scenario2);

            $("#modalscenarioslistBox_1").selectpicker("refresh");
            $("#modalscenarioslistBox_2").selectpicker("refresh");
            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });

});


$("#addcomparescenarioBtn").on("click", function () {
    MMOUtils.showLoader();
    $("#addComparesionsBox").show();
    if (count <= 6) {
        var htmlTemplate = '<div class="card"><div class="card-body"><div class="row"><div class="col-sm-6 mx-auto"> <select class="selectpicker modalselectBox" data-style="form-control outline-style mmo-select" id="modalscenarioslistBox_' + count + '"></select></div></div></div></div>'
        $("#addComparesionsBox").append(htmlTemplate);
        var dynamic_selectIDval = "modalscenarioslistBox_" + count;
        $(".selectpicker").selectpicker("refresh");


        $.ajax({
            url: '/getScenarioList',
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
                var scenariosListdata = response;

                var scenario1 = $("#selectscnrio_one").val();
                var scenario2 = $("#selectscnrio_two").val();

                $("#modalscenarioslistBox_1").val(scenario1);
                $("#modalscenarioslistBox_2").val(scenario2);

                MMOUtils.buildDDlFromList("#" + dynamic_selectIDval, scenariosListdata, "");
                hideSelectedValuesInComboBoxes();
                MMOUtils.hideLoader();

            },
            error: function (error) {
                MMOUtils.hideLoader();
            }
        });
        count += 1;
    }



});



$(document).on("change", ".modalselectBox", function () {
    var modal_chosenID = $(this).attr("id");
    var modal_curntVal = $(this).val();
    if (modal_curntVal != "") {
        $(".modalselectBox option").each(function () {
            $(".modalselectBox").not("#" + modal_chosenID).find('option[value="' + $(this).val() + '"]').show();
        });
        hideSelectedValuesInComboBoxes();
    }

});

$(document).on("change", ".compareselectBox", function () {
    var comparescnrio_selectID = $(this).attr("id");
    var comparescnrio_curntVal = $(this).val();
    if ((comparescnrio_selectID == "selectscnrio_one") || (comparescnrio_selectID == "selectscnrio_two")) {
        if (comparescnrio_curntVal === "") {
            $(".compareselectBox option").each(function () {
                $(".compareselectBox").not("#" + comparescnrio_selectID).find('option[value="' + $(this).val() + '"]').show();
            });
            // $(".compareselectBox").not("#" + comparescnrio_selectID).find('option[value="' + comparescnrio_curntVal + '"]').hide();
            $(".compareselectBox").not("#" + comparescnrio_selectID).selectpicker("refresh");
        }
    }

    if (comparescnrio_curntVal != "") {
        $(".compareselectBox option").each(function () {
            $(".compareselectBox").not("#" + comparescnrio_selectID).find('option[value="' + $(this).val() + '"]').show();
        });
        $(".compareselectBox").not("#" + comparescnrio_selectID).find('option[value="' + comparescnrio_curntVal + '"]').hide();
        $(".compareselectBox").not("#" + comparescnrio_selectID).selectpicker("refresh");
    }
});
$(document).on("change", ".comparedueselectBox", function () {
    var comparescnrio_selectID = $(this).attr("id");
    var comparescnrio_curntVal = $(this).val();
    if ((comparescnrio_selectID == "selectscnrio_1") || (comparescnrio_selectID == "selectscnrio_2")) {
        if (comparescnrio_curntVal === "") {
            $(".comparedueselectBox option").each(function () {
                $(".comparedueselectBox").not("#" + comparescnrio_selectID).find('option[value="' + $(this).val() + '"]').show();
            });
            // $(".comparedueselectBox").not("#" + comparescnrio_selectID).find('option[value="' + comparescnrio_curntVal + '"]').hide();
            $(".comparedueselectBox").not("#" + comparescnrio_selectID).selectpicker("refresh");
        }
    }

    if (comparescnrio_curntVal != "") {
        $(".comparedueselectBox option").each(function () {
            $(".comparedueselectBox").not("#" + comparescnrio_selectID).find('option[value="' + $(this).val() + '"]').show();
        });
        $(".comparedueselectBox").not("#" + comparescnrio_selectID).find('option[value="' + comparescnrio_curntVal + '"]').hide();
        $(".comparedueselectBox").not("#" + comparescnrio_selectID).selectpicker("refresh");
    }
});

// $(document).on("change", ".kpi_select_box", function () {
//     var comparescnrio_selectID = $(this).attr("id");
//     var comparescnrio_curntVal = $(this).val();
//     if ((comparescnrio_selectID == "opt_scenarios_1") || (comparescnrio_selectID == "opt_scenarios_2")) {
//         if (comparescnrio_curntVal === "") {
//             $(".kpi_select_box option").each(function () {
//                 $(".kpi_select_box").not("#" + comparescnrio_selectID).find('option[value="' + $(this).val() + '"]').show();
//             });
//             // $(".kpi_select_box").not("#" + comparescnrio_selectID).find('option[value="' + comparescnrio_curntVal + '"]').hide();
//             $(".kpi_select_box").not("#" + comparescnrio_selectID).selectpicker("refresh");
//         }
//     }

//     if (comparescnrio_curntVal != "") {
//         $(".kpi_select_box option").each(function () {
//             $(".kpi_select_box").not("#" + comparescnrio_selectID).find('option[value="' + $(this).val() + '"]').show();
//         });
//         $(".kpi_select_box").not("#" + comparescnrio_selectID).find('option[value="' + comparescnrio_curntVal + '"]').hide();
//         $(".kpi_select_box").not("#" + comparescnrio_selectID).selectpicker("refresh");
//     }
// });

$(document).on("click", "#comparescenariosdownloadBtn", function () {
    var selectedscenarios = [];
    // var i = 0;
    $(".modalselectBox  option:selected").each(function () {
        if ($(this).val() != "") {
            selectedscenarios.push($(this).val());
        }

    });
    var outcome = $("input[name='metric']:checked").val();
    var period_type = $("#period_type").val();
    //     document.location.href = "/download_scenario_comparisons?scenarios="+selectedscenarios+"&outcome="+outcome+"&period_type="+period_type+"&download_type=csv"
    MMOUtils.showLoader();
    $.fileDownload("/download_scenario_comparisons?scenarios=" + selectedscenarios + "&outcome=" + outcome + "&period_type=" + period_type + "&download_type=csv", {
        httpMethod: 'GET',
        successCallback: function (data) {
            MMOUtils.hideLoader();
        },
        failCallback: function (data) {
            MMOUtils.hideLoader();
        }
    })
});
function toggleContent() {
    marginalreturnGeolevelTreecompare()
    var viewtype = $(this).attr('href');
    $("a.toggle-btn").removeClass("active");
    var viewtype = $(this).attr('href');
    if (viewtype == '#tabular') {
        $("#Compare-metricTblBox").show();
        $("#comparesummaryHolder").show();
        $("#touchpoints_ddl2").hide();
        $("#Compare-graphs").hide();
        var selcetMetric = $("input[name='metric']:checked").val();
        var scenario1 = $("#selectscnrio_two").val();
        var scenario2 = $("#selectscnrio_one").val();
        var period_type = $("#period_type").val();
        var period = $("#quarterddl7").val();
        var month = $("#monthddl7").val();
        get_spend_comparison(scenario1, scenario2, period_type, selcetMetric, period, month)

    }
    else {
        $("#Compare-graphs").show();
        selectedLevelsgraph()
        $("#Compare-metricTblBox").hide();
        $("#touchpoints_ddl2").show();
        $("#comparesummaryHolder").hide();
    }
    $(this).addClass("active");
}
MMOTreeDropdown = function (config) {
    // nodes where tree should be rendered
    // maybe we can merge the two into a single node
    // this.treeHeadNode = config.treeHeadNode;
    this.treeBodyNode = config.treeBodyNode;

    // // subheaders under each main header
    // // (currently same sub-headers repeat for each header)
    // // this.subHeaders = config.subHeaders;

    this.resetTree = function () {
        // $(this.treeHeadNode).html("");
        $(this.treeBodyNode).html("");
    };

    this.rebuildTable = function (data) {
        // this.regenerateHead(headers);
        this.regenerateBody(data);
        // TODO check if this id needs to be parameterized
        $("table#geolevelmarginalreturn_Tbltree").data("simple-tree-table").init();
        // $("table#dropdowntree").data("simple-tree-table").init();
        $("table#dropdowntree2").data("simple-tree-table").init();
    };



    this.regenerateBody = function (data) {
        var me = this;
        $(this.treeBodyNode).html('');

        var htmlTemplate = '';
        // for each row
        $.each(data, function (i, el) {
            if (el.node_id > 2000) {
                htmlTemplate += '<tr data-node-id="' + el.node_id + '" data-node-pid="' + el.parent_node_id + '">';
                htmlTemplate += '<td width="250" class=""> <input id="' + el.node_id + '" type="checkbox" class="geolevelItem" data-node-name="' + el.node_display_name + '"/> &nbsp;' + el.node_display_name + '</td>';
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
    $("#geolevelmarginalreturn_Tbltree tr").filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
}
function geolevelsearch3() {
    var value = $(this).val().toLowerCase();
    $("#dropdowntree2 tr").filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
}
function selectedLevels(e) {
    e.preventDefault();
    var selectedNodes = {}
    $.each($("input[class='geolevelItem']:checked"), function () {
        selectedNodes['node'] = $(this).attr("id");
        $("#node_name").html($(this).data('node-name'));
    });

    dueToAnalysisChartgenerate(selectedNodes);

    if ($(".maindropdown").hasClass('active')) {
        $('.main-dropdown-menu').hide();
        $(".maindropdown").removeClass('active');
    }
    else {
        $(".maindropdown").addClass('active');
        $('.main-dropdown-menu').show();
    }
}


function generate_charts_roa(xdata, spenddata, ftbdata, sudata) {
    var chart = c3.generate({
        bindto: '#chart',
        data: {
            x: "Year",
            columns: [xdata, spenddata, ftbdata, sudata],
            types: {
                Spend: 'bar',
                "coutcome1": 'line',
                "coutcome2": 'line'
            },
            axes: {
                Spend: 'y',
                "coutcome1": 'y2',
                "coutcome2": 'y2'
            },
            labels: {
                format: {
                    Spend: function (value) {
                        return "$" + (value / 1000000).toFixed(1) + "M";
                    }, // Format for the Spend values
                    "coutcome1": function (value) {
                        return "$" + (value).toFixed(0);
                    }, // Format for the NTF Asset Media ROMI values
                    "coutcome2": function (value) {
                        return "$" + (value).toFixed(0);
                    } // Format for the Ext Asset Media ROMI values
                }
            }
        },
        axis: {
            x: {
                type: 'category'
            },
            y: {
                label: {
                    text: 'Spend',
                    position: 'outer-middle'
                },
                tick: {
                    format: function (d) {
                        return "";
                    }
                }
            },
            y2: {
                show: false,
                label: {
                    text: 'ROMI',
                    position: 'outer-middle'
                }
            }
        },
        color: {
            pattern: ['#9E9E9E', '#000000', '#f7901e']
        },
        title: {
            text: text_formater()
        },

    });
}
function text_formater() {
    chart_name = "coutcome2 & coutcome1"
    var from_year = scenario1;
    var to_year = scenario2;
    if (period_type == "year") {
        chart_name += " (" + from_year + " to " + to_year + " )"
        return chart_name
    }
    else if (period_type == "month") {
        return chart_name += " (" + from_year + " - " + month1 + " to " + to_year + " - " + month2 + " )"
    }
    else {
        return chart_name += " (" + from_year + " - Q" + quarter1 + " to " + to_year + " - Q" + quarter2 + " )"
    }
}
$("[data-hide]").on("click", function () {
    $('#romiCpaModal').modal('hide');
});