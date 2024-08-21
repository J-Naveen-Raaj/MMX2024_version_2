var ScenarioTree = {};
// will need to move this to a config file for easy editing
var defaultSelectedNode = 2003;
var outcomes = {

}

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

$(function () {
    // PageBodyEvents();

    var period_type = $("#period_type").val();
    if (period_type == "year") {
        $(".scenariolabel").hide()
    }
    else {
        $(".scenariolabel").show()
    }
    timeperiod()
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
            $("#scenario1").find('option[value="1"]').attr('selected', 'selected')
            $("#scenario1").selectpicker("refresh");
            $("#scenario2").selectpicker("refresh");
            $("#scenario2").find('option[value="2"]').attr('selected', 'selected')
            $("#scenario2").selectpicker("refresh");
            var storedValue1 = localStorage.getItem('scenario1Value');
            if (storedValue1) {
                $('#scenario1').val(storedValue1);
                $("#scenario1").find('option[value="' + storedValue1 + '"]').hide();
                $("#scenario1").selectpicker("refresh");
            }

            var storedValue2 = localStorage.getItem('scenario2Value');
            if (storedValue2) {
                $('#scenario2').val(storedValue2);
                $("#scenario2").find('option[value="' + storedValue2 + '"]').hide();
                $("#scenario2").selectpicker("refresh");
            }
            dueToAnalysisChartgenerate({ "node": defaultSelectedNode });
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });

    marginalreturnGeolevelTree();

    // Initialize the tree with the required nodes
    ScenarioTree = new MMOTree({
        // treeHeadNode: '.treeDataHeader',
        treeBodyNode: '.treeDatabody',
        // these are specific to the screen
        // subHeaders: SUBHEADERS
    });

    $("body").on("click", '.geolevelItem', function () {
        $('.geolevelItem').not(this).prop('checked', false);
    });

    $("body").on("click", "#duetoanalysisapplyBtn", selectedLevels);

    $("body").on("change", "#scenario1,#scenario2,#period_type,#quarterddl1,#quarterddl2,#monthddl1,#monthddl2", selectedScenarios);

    $("body").on("keyup", "#geolevelsearchBox", geolevelsearch);
    document.addEventListener('click', function (event) {
        var dropdown = document.querySelector('.main-dropdown-menu');
        var maindropdown = document.querySelector('.maindropdown');

        if (!dropdown.contains(event.target) && !maindropdown.contains(event.target)) {
            $('.main-dropdown-menu').hide();
            $(".maindropdown").removeClass('active');

        }
    });

});


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

function selectedScenarios(e) {
    e.preventDefault();
    var period_type = $("#period_type").val();
    if (period_type == "year") {
        $(".quarterddl-item").hide();
        $(".monthddl-item").hide();
        $(".scenariolabel").hide()
    }
    else if (period_type == "month") {
        $(".quarterddl-item").hide();
        $(".monthddl-item").show()
        $(".scenariolabel").show()
    }
    else {
        $(".quarterddl-item").show();
        $(".monthddl-item").hide()
        $(".scenariolabel").show()
    }
    var selectedNodes = { node: defaultSelectedNode }
    $.each($("input[class='geolevelItem']:checked"), function () {
        selectedNodes['node'] = $(this).attr("id");
        $("#node_name").html($(this).data('node-name'));
    });

    dueToAnalysisChartgenerate(selectedNodes);
}

function geolevelsearch() {
    var value = $(this).val().toLowerCase();
    $("#geolevelmarginalreturn_Tbltree tr").filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
}

function dueToAnalysisChartgenerate(selectedNodes) {
    MMOUtils.showLoader();
    var scenario1 = $("#scenario1").val();
    var scenario2 = $("#scenario2").val();
    var period_type = $("#period_type").val();
    var quarter1 = $("#quarterddl1").val()
    var quarter2 = $("#quarterddl2").val()
    var month1 = $("#monthddl1").val()
    var month2 = $("#monthddl2").val()
    var period_1 = $("#scenario1 option:selected").val();
    var period_2 = $("#scenario2 option:selected").val();

    year1 = $("#scenario1 option:selected").text();
    year2 = $("#scenario2 option:selected").text();

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
    // fetch the data
    $.ajax({
        url: 'get_reporting_due_to_analysis?' + queryString,
        type: 'GET',
        dataType: "json",
        headers: {
            "content-type": "application/json",
            "cache-control": "no-cache"
        },
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
            $("#duetoModalLabel").text("Error");
            $(".modal-header").addClass("btn-danger").removeClass("btn-success");
            $(".modal-body").text("No data for current selection");
            return $("#duetoModal").modal('show');
        }
    });

}
$("[data-hide]").on("click", function () {
    $('#duetoModal').modal('hide');
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
function linegraphGenerate(bindto, returncurveData) {

    var allkeys = returncurveData.map(function (d) { return d[0] });
    var keys = allkeys.filter(function (d) { return d.indexOf(':') >= 0 })
    var xs = {};
    keys.map(function (d) { s = d.split(':'); xs[s[1]] = d })

    return c3.generate({
        bindto: '#' + bindto + '_box',
        size: {
            width: $('#' + bindto + '_box').width() * 0.95,
            height: 400
        },
        padding: {
            right: 25
        },
        data: {
            xs: xs,
            columns: returncurveData,
            type: 'line'
        },
        line: {
            connect: {
                Null: true
            },
        },
        axis: {
            x: {
                type: 'linear',
                tick: {
                    format: d3.format('s'),
                    count: 2,
                    rotate: false,
                    multiline: false
                },
                label: {
                    text: 'Incremental Spend',
                    position: 'outer-center'
                }
            },
            y: {
                show: true,
                label: {
                    text: MMOUtils.replaceUnderscore(bindto.toUpperCase()),
                    position: 'outer-middle'
                },
                tick: {
                    format: function (data) { return d3.format(',s')(data).replace(/G/, "B") },
                    outer: false
                }
            }

        },
        grid: {
            x: {
                show: false,
            },
            y: {
                show: true,
            }

        },
        legend: {
            show: true,
            position: 'bottom'
        },

        point: {
            r: 1
        },
        zoom: {
            enabled: false
        }
    });
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
            ScenarioTree.rebuildTable(response);

            $("#" + defaultSelectedNode).prop('checked', true);
            // hide the loader
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
        .attr("width", 0.6 * x.bandwidth())
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

MMOTree = function (config) {
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
        $("table#geolevelmarginalreturn_Tbltree").data("simple-tree-table").init();
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
$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});