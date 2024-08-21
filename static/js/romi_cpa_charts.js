var scenario_to_year = { 1: 2016, 2: 2017, 3: 2018, 4: 2019, 5: 2020, 6: 2021, 7: 2022 }
var scenario1 = ""
var scenario2 = ""
var period_type = ""
var quarter1 = ""
var quarter2 = ""
var halfyear1 = ""
var halfyear2 = ""
var chart_name = "";
var chart_name2 = "";
var month1 = "";
var month2 = "";

// dynamically form chart data as key is different for all types of outcomes
var chart_data_json = {
    json: "",
    keys: {
        value: []
    },
    axes: {

    },
    types: {
        spend: 'bar'
    },
    labels: {
        format: {
            spend: function (d) {
                return "$" + (d / 1000000).toFixed(1) + "M"
            }
        }

    },
    names: {

    }
}

// function used in json for generating the chart label
var label_format = function (d) {
    return "$" + Math.round(d)
}


// called when the page loads for the first time
$(function () {
    document.addEventListener('click', function (event) {
        var dropdown = document.querySelector('.main-dropdown-menu');
        var maindropdown = document.querySelector('.maindropdown');

        if (!dropdown.contains(event.target) && !maindropdown.contains(event.target)) {
            $('.main-dropdown-menu').hide();
            $(".maindropdown").removeClass('active');

        }
    });
    DropdownTree = new MMOTreeDropDown({
        treeBodyNode: '.ddl'
    });
    var period_type = $("#period_type").val();
    if (period_type == "year") {
        $(".scenariolabel").hide()
    }
    else {
        $(".scenariolabel").show()
    }
    timeperiod()
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
            get_romi_cpa_data();

        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
    marginalreturnGeolevelTree();
    $("body").on("click", "#compareBarChartapplyBtn", selectedLevels)
})
$("body").on("keyup", "#geolevelsearchBox", geolevelsearch);

// click on export image button
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
    saveSvgAsPng($("#" + chartID).find('svg')[0], chart_name + ".png");
})

function selectedLevels() {

    get_romi_cpa_data()
    if ($(".maindropdown").hasClass('active')) {
        $('.main-dropdown-menu').hide();
        $(".maindropdown").removeClass('active');
    }
    else {
        $(".maindropdown").addClass('active');
        $('.main-dropdown-menu').show();
    }
}

//function to get all the selected dropdown values
function load_all_dropdown_values() {
    scenario1 = $("#scenario1").val()
    scenario2 = $("#scenario2").val()
    period_type = $("#period_type").val();
    quarter1 = $("#quarterddl1").val()
    quarter2 = $("#quarterddl2").val()
    halfyear1 = $("#halfyearddl1").val()
    halfyear2 = $("#halfyearddl2").val()
    month1 = $("#monthddl1").val()
    month2 = $("#monthddl2").val()
}


$("#period_type").on("change", function () {
    var period_type = $(this).val();
    if (period_type == "year") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").hide()
        $(".scenariolabel").hide()
    }
    else if (period_type == "month") {
        $(".quarterddl-item").hide();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").show()
        $(".scenariolabel").show()
    }
    else {
        $(".quarterddl-item").show();
        $(".halfyearddl-item").hide();
        $(".monthddl-item").hide()
        $(".scenariolabel").show()
    }
})

// compare button click
$('#btn_compare_romi_cpa').on('click', get_romi_cpa_data)

function get_romi_cpa_data() {
    MMOUtils.showLoader();
    var checkedItems = [];
    $.each($("input[class='geolevelItem']:checked"), function () {
        checkedItems.push($(this).attr("id"));
    });

    load_all_dropdown_values();
    var scenario1 = $("#scenario1").val()
    var scenario2 = $("#scenario2").val()
    var from_year = $("#scenario1 option:selected").text();
    var to_year = $("#scenario2 option:selected").text();
    if ((to_year < from_year) || ((from_year === to_year) && ((quarter1 > quarter2) || (halfyear1 > halfyear2)))) {
        MMOUtils.hideLoader()
        $("#romiCpaModalLabel").text("Error");
        $(".modal-header").addClass("btn-danger").removeClass("btn-success");
        $(".modal-body").text("Please select a valid range from the drop downs.");
        return $("#romiCpaModal").modal('show');
    }


    MMOUtils.showLoader();
    // Constructing the inputs object with query parameters
    var queryString = `scenario_1=${scenario1}&scenario_2=${scenario2}&period_type=${period_type}&from_quarter=${quarter1}&to_quarter=${quarter2}&from_month=${month1}&to_month=${month2}&from_year=${from_year}&to_year=${to_year}&nodes=${checkedItems.join(',')}`;

    $.ajax({
        url: "/get_romi_cpa_data?" + queryString,
        type: 'GET',
        dataType: "json",
        success: function (response) {
            // $("#touchpoints_ddl").show();
            MMOUtils.hideLoader();
            // var chart_data = get_data_for_selected_chart(response);
            var xData = ["Year"];
            var spendData = ["Spend"];
            var ftbdata = ["coutcome1"];
            var sudata = ["coutcome2"];
            var ftbsdata = ["outcome1"];
            var signupdata = ["outcome2"]
            if (period_type == "year") {
                yearlydata = response.year
                yearlydata.forEach(function (item) {
                    xData.push(item.year);
                });
            }
            else if (period_type == "quarter") {
                yearlydata = response.quarter
                yearlydata.forEach(function (item) {
                    xData.push(item.year + " Q" + item.quarter);
                });
            }
            else if (period_type == "month") {
                yearlydata = response.month
                yearlydata.forEach(function (item) {
                    var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                    var monthName = monthNames[item.month - 1]; // Convert month number to name
                    xData.push(item.year + monthName);
                });

            }
            yearlydata.forEach(function (item) {
                spendData.push(item.spend);
                ftbdata.push(item.coutcome1);
                sudata.push(item.coutcome2);
                ftbsdata.push(item.outcome1);
                signupdata.push(item.outcome2)
            });
            generate_bar_chart(xData, spendData)
            generate_charts_roa(xData, signupdata, ftbsdata)
            generate_line_chart(xData, sudata, ftbdata)
            if ($(".maindropdown").hasClass('active')) {
                $('.main-dropdown-menu').hide();
                $(".maindropdown").removeClass('active');
            }
        },
        error: function (error) {
            MMOUtils.hideLoader();
            $("#romiCpaModalLabel").text("Error");
            $(".modal-header").addClass("btn-danger").removeClass("btn-success");
            $(".modal-body").text("Error occurred while fetching the data");
            return $("#romiCpaModal").modal('show');
        }
    });
}

function generate_charts_roa(xdata, ftbdata, sudata) {
    var chart = c3.generate({
        bindto: '#bar_chart',
        data: {
            x: "Year",
            columns: [xdata, ftbdata, sudata],
            type: 'bar',
            labels: {
                format: {
                    Spend: function (value) {
                        return "$" + (value / 1000000).toFixed(1) + "M";
                    }, // Format for the Spend values
                    "outcome1": function (value) {
                        if (Math.abs(value) >= 1e6) {
                            return d3.format('.1f')(value / 1e6) + "M";
                        } else if (Math.abs(value) >= 1e3) {
                            return d3.format('.1f')(value / 1e3) + "K";
                        } else if (value == 0) {
                            return "0"; // Add a decimal to 0
                        }
                        else {
                            return d3.format(',s')(value).replace(/G/, "B");
                        }
                    },
                    "outcome2": function (value) {
                        if (Math.abs(value) >= 1e6) {
                            return d3.format('.1f')(value / 1e6) + "M";
                        } else if (Math.abs(value) >= 1e3) {
                            return d3.format('.1f')(value / 1e3) + "K";
                        } else if (value == 0) {
                            return "0"; // Add a decimal to 0
                        }
                        else {
                            return d3.format(',s')(value).replace(/G/, "B");
                        }
                    }
                }
            }
        },
        axis: {
            x: {
                type: 'category'
            },
            y: {
                show: true,
                label: {
                    text: 'Outcome',
                    position: 'outer-middle'
                },
                tick: {
                    outer: false,
                    format: function (d) {
                        return ""; // Empty string to hide tick values
                    }
                }
            }
        },
        color: {
            pattern: ['#9E9E9E', '#575757']
        },
        size: {
            width: 1000, // Set the width here
            height: 200
        },
        legend: {
            position: 'right' // Change legend position to the right
        },
        tooltip: {
            format: {
                value: function (data) { return d3.format(',s')(data).replace(/G/, "B") }
            }
        },
        bar: {
            width: {
                ratio: 0.3
            }
        }

    });
}
function generate_bar_chart(xdata, spenddata) {
    var chart = c3.generate({
        bindto: '#chart',
        data: {
            x: "Year",
            columns: [xdata, spenddata],
            type: 'bar',
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
                show: true,
                label: {
                    text: 'Spend',
                    position: 'outer-middle'
                },
                tick: {
                    outer: false,
                    // format: function (d) {
                    //     return "$" + d / 1000000 + "M";
                    // }
                    format: function (d) {
                        return ""; // Empty string to hide tick values
                    }
                }
            }
        },
        color: {
            pattern: ['#575757']
        },
        // title: {
        //     text: text_formater()
        // },
        size: {
            width: 1000, // Set the width here
            height: 200
        },
        legend: {
            position: 'right' // Change legend position to the right
        },
        tooltip: {
            format: {
                value: function (data) { return d3.format('$,s')(data).replace(/G/, "B") }
            }
        },
        bar: {
            width: {
                ratio: 0.3
            }
        }
    });
}

function generate_line_chart(xdata, sudata, ftbdata) {
    var chart = c3.generate({
        bindto: '#line_chart',
        data: {
            x: "Year",
            columns: [xdata, sudata, ftbdata,],
            types: {
                "coutcome2": 'line',
                "coutcome1": 'line',
            },
            labels: {
                format: {
                    Spend: function (value) {
                        return "$" + (value / 1000000).toFixed(1) + "M";
                    }, // Format for the Spend values
                    "coutcome2": function (value) {
                        return "$" + (value).toFixed(0);
                    },
                    "coutcome1": function (value) {
                        return "$" + (value).toFixed(0);
                    },
                }
            }
        },
        axis: {
            x: {
                type: 'category',
            },
            y: {
                show: true,
                label: {
                    text: 'coutcome1 & coutcome2',
                    position: 'outer-middle'
                },
                tick: {
                    outer: false,
                    format: function (d) {
                        return ""; // Empty string to hide tick values
                    }
                }
            },
        },
        color: {
            pattern: ['#000000', '#f7901e']
        },
        // title: {
        //     text: text_formater()
        // },
        size: {
            width: 1000,
            height: 210
        },
        legend: {
            position: 'right' // Change legend position to the right
        },
        tooltip: {
            format: {
                value: function (data) {
                    if (data >= 1e9) {
                        return d3.format(',.2f')(data / 1e9) + 'B';
                    } else if (data >= 1e6) {
                        return d3.format(',.2f')(data / 1e6) + 'M';
                    } else {
                        return d3.format(',.2f')(data);
                    }
                }
            }
        }
    });
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
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    });
}
function text_formater() {
    var chart_name = "coutcome1 & coutcome2"
    var from_year = scenario_to_year[+scenario1];
    var to_year = scenario_to_year[+scenario2]
    if (period_type === "year") {
        chart_name += " (" + from_year + " to " + to_year + " )"
    }
    else if (period_type === "month") {
        chart_name += " (" + from_year + " - " + month1 + " to " + to_year + " - " + month2 + " )"
    }
    else {
        chart_name += " (" + from_year + " - Q" + quarter1 + " to " + to_year + " - Q" + quarter2 + " )"
    }
    return chart_name
}

// hide modal
$("[data-hide]").on("click", function () {
    $('#romiCpaModal').modal('hide');
});

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
            if (el.node_id > 2000 && el.node_id < 4000) {
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
            // $("#touchpoints_ddl").hide();
        },
        error: function (error) {
            MMOUtils.hideLoader()
        }
    });

}

