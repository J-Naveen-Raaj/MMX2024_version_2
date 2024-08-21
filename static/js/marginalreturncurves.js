var ScenarioTree = {};
// will need to move this to a config file for easy editing
var HEADERS = {
  "qtrly": ["Q1", "Q2", "Q3", "Q4", "Total"],
  "monthly": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "Total"],
  "yearly": ["Annual", "Total"],
  "halfyearly": ["H1", "H2", "Total"]
};

var HEADERS_KEYS = {
  "qtrly": ["Q1", "Q2", "Q3", "Q4", "Total"],
  "monthly": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Total"],
  "yearly": ["Year", "Total"],
  "halfyearly": ["HalfYear-1", "HalfYear-2", "Total"]
};

var SCENARIO_DDLs = {
  "7": "Spend Plan 2022"
}

var DEFAULT_SCENARIO = 7;

$(function () {
  document.addEventListener('click', function (event) {
    var dropdown = document.querySelector('.main-dropdown-menu');
    var maindropdown = document.querySelector('.maindropdown');

    if (!dropdown.contains(event.target) && !maindropdown.contains(event.target)) {
      $('.main-dropdown-menu').hide();
      $(".maindropdown").removeClass('active');

    }
  });
  timeperiod()
  MMOUtils.hideLoader();
  // PageBodyEvents();
  $.ajax({
    url: '/get_scenario_list_mrc',
    type: 'GET',
    dataType: "json",
    processData: false,
    contentType: false,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-cache"
    },
    success: function (response) {
      //TODO
      // For now scenario list is hardcoded, later SCENARIO_DDLs need to be replaced with response
      MMOUtils.buildDDlFromList("#base_plan_ddl", response);

      var arr = [];
      for (var key in response) {
        if (response.hasOwnProperty(key)) {
          arr.push([key]);
        }
      }
      $("#base_plan_ddl").selectpicker("refresh");
      $("#base_plan_ddl").find('option[value="' + arr[0] + '"]').attr('selected', 'selected')
      $("#base_plan_ddl").selectpicker("refresh");
      MMOUtils.hideLoader();
      id = $("#base_plan_ddl").val()
      marginalreturndatanchartgenerate({ "nodes": [], "scenario_id": id });
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

  $("body").on("click", "#returncurveapplyBtn", selectedLevels);
  $("body").on("keyup", "#geolevelsearchBox", geolevelsearch);

});


function selectedLevels(e) {
  e.preventDefault();
  var checkedItems = [];
  var selectedNodes = {}
  var scenario_id = $("#base_plan_ddl").val();
  $.each($("input[class='geolevelItem']:checked"), function () {
    checkedItems.push($(this).attr("id"));
  });

  selectedNodes['nodes'] = checkedItems;
  selectedNodes["scenario_id"] = Number(scenario_id);

  marginalreturndatanchartgenerate(selectedNodes);

  if ($(".maindropdown").hasClass('active')) {
    $('.main-dropdown-menu').hide();
    $(".maindropdown").removeClass('active');
  }
  else {
    $(".maindropdown").addClass('active');
    $('.main-dropdown-menu').show();
  }
}

function geolevelsearch() {
  var value = $(this).val().toLowerCase();
  $("#geolevelmarginalreturn_Tbltree tr").filter(function () {
    $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
  });
}

function serializeNodes(nodes) {
  return nodes.join(',');
}

function serializeObject(obj) {
  const serializedNodes = obj.nodes ? `nodes=${serializeNodes(obj.nodes)}` : '';
  const serializedScenarioId = obj.scenario_id !== null ? `scenario_id=${obj.scenario_id}` : '';

  // Combine the parts with "&" and filter out empty strings
  const queryString = [serializedNodes, serializedScenarioId].filter(Boolean).join('&');

  return queryString;
}


function marginalreturndatanchartgenerate(selectedNodes) {
  MMOUtils.showLoader();
  const queryString = serializeObject(selectedNodes);
  // fetch the data
  $.ajax({
    url: '/get_marginal_return_curves?' + queryString,
    type: 'GET',
    dataType: "json",
    processData: false,
    contentType: false,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-cache"
    },
    success: function (response) {
      $("#returnCurvesMainBox").html("");
      $.each(response.results, function (bk, bv) {
        $.map(bv, function (v, i) {
          var filterData = $.map(v, function (a) {
            return a//a == "" ? null : a;
          });
          bv[i] = filterData;
        });

        var htmlTemplate = '';
        htmlTemplate += '<div class="graph-box px-0"><h4 class="text-right p-r-30">' + MMOUtils.replaceUnderscore(bk) + '</h4><div class="graph graph1 pt-0" id="' + bk + '_box" style="height: 520px;width:100%">' + metricLinegraph + '</div></div>'
        $("#returnCurvesMainBox").append(htmlTemplate);
        $('#' + bk + '_box').html("");
        var metricLinegraph = linegraphGenerate(bk, bv, response.delta[bk], response['base_spend_data']);
      });
      MMOUtils.hideLoader();
    },
    error: function (error) {
      MMOUtils.hideLoader();
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
      MMOUtils.hideLoader()
    },
    error: function (error) {
      MMOUtils.hideLoader();
    }
  });
}
function linegraphGenerate(bindto, returncurveData, delta, base_spend_data) {
  var allkeys = returncurveData.map(function (d) { return d[0] });
  var keys = allkeys.filter(function (d) { return d.indexOf('spend_change:') >= 0 })
  var xs = {};
  keys.map(function (d) { s = d.split(':'); xs[s[1]] = d })
  var currencyMapping = { "G": "Billion", "M": "Million", "k": "Thousand" }
  var yaxisPrefix = currencyMapping[d3.format('~s')(d3.max(returncurveData[1].slice(1, returncurveData[1].length))).substr(-1)];
  var xaxisPrefix = currencyMapping[d3.format('~s')(d3.max(returncurveData[0].slice(1, returncurveData[1].length))).substr(-1)];


  var chart = c3.generate({
    bindto: '#' + bindto + '_box',
    size: {
      width: $('#' + bindto + '_box').width() * 1.5,
      height: height_channels(returncurveData)
    },
    padding: {
      bottom: 20,
      right: 20
    },
    data: {
      xs: xs,
      columns: returncurveData,
      classes: delta,
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
          format: function (data) {
            var formattedValue;
            var magnitude = Math.floor(Math.log10(Math.abs(data)));

            if (magnitude >= 6) {
              formattedValue = d3.format('.0f')(data / 1e6) + 'M';
            } else if (magnitude >= 3) {
              formattedValue = d3.format('.0f')(data / 1e3) + 'K';
            } else {
              formattedValue = d3.format('.0f')(data);
            }

            return formattedValue;
          },
          count: 2,
          rotate: false,
          multiline: false
        },
        label: {
          text: 'Incremental Spend($ ' + xaxisPrefix + ')',
          position: 'outer-center'
        }
      },
      y: {
        show: true,
        label: {
          text: bindto.indexOf('Count') > 0 ? MMOUtils.replaceUnderscore(bindto) + "(in " + yaxisPrefix + ")" : "Change in " + MMOUtils.replaceUnderscore(bindto),
          position: 'outer-middle'
        },
        tick: {
          format: function (data) {
            var formattedValue;
            var magnitude = Math.floor(Math.log10(Math.abs(data)));

            if (magnitude >= 6) {
              formattedValue = d3.format('.0f')(data / 1e6) + 'M';
            } else if (magnitude >= 3) {
              formattedValue = d3.format('.0f')(data / 1e3) + 'K';
            } else {
              formattedValue = d3.format('.0f')(data);
            }

            return formattedValue;
          },
          count: 2,
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
    tooltip: {

      contents: function (d, defaultTitleFormat, defaultValueFormat, color) {
        var $$ = this, config = $$.config, CLASS = $$.CLASS,
          titleFormat = config.tooltip_format_title || defaultTitleFormat,
          nameFormat = config.tooltip_format_name || function (name) { return name; },
          valueFormat = config.tooltip_format_value || defaultValueFormat,
          text, i, title, value, name, bgcolor;
        const meta = config.data_classes;

        for (i = 0; i < d.length; i++) {
          if (!(d[i] && (d[i].value || d[i].value === 0))) { continue; }
          if (!text) {
            title = titleFormat ? titleFormat(d[i].x) : d[i].x;
            var base_spend = titleFormat ? titleFormat(base_spend_data[d[i].id]) : base_spend_data[d[i].id];
            text = "<table class='" + $$.CLASS.tooltip + "'>" + (title || title === 0 ? "<tr><th colspan='4'> Spend Change($): " + (title) + "</th></tr>" : "");
            text += "<tr class='" + $$.CLASS.tooltipName + "-header'>";
            if (bindto == "outcome1") {
              text += "<th class='name with-border'>Channel</th>";
              text += "<th class='name with-border'>Base Spend</th>";
              text += "<th class='name with-border'>outcome1 Value</th>";
              text += "<th class='name'>outcome1 Change</th>";
            }
            else {
              text += "<th class='name with-border'>Channel</th>";
              text += "<th class='name with-border'>Base Spend</th>";
              text += "<th class='name with-border'> outcome2 Value</th>";
              text += "<th class='name'>outcome2 Change</th>";
            }
            text += "</tr>";
          }
          const line = d[i].id;
          const properties = meta[line];
          const property = properties ? properties[properties.length - (d[i].index) - 1] : null;
          bgcolor = $$.levelColor ? $$.levelColor(d[i].value) : color(d[i].id);

          // get the base value from the chart data
          var touchpoint_data = chart.data().filter(function (individual_data) {
            return individual_data.id === d[i].id
          })
          var individual_touchpoint_base_value = touchpoint_data[0].values.filter(function (a) {
            if (a['x'] === 0) {
              return a
            }
          })
          // text += "<tr class='" + $$.CLASS.tooltipName + "-" + d[i].id + "'>";
          // text += "<td class='name' colspan='4'><span style='text-align:left;background-color:" + bgcolor + "'></span>" + d[i].id + "</td>";
          // //text += "<td class='name'>"+ d3.format(',s')(d[i].value).replace(/G/,"B") + "</td>";
          // text += "</tr>";
          text += "<tr class='" + $$.CLASS.tooltipName + "-" + d[i].id + "'>";
          text += "<td class='name'><span style='text-align:left;background-color:" + bgcolor + "'></span>" + d[i].id + " </td>";
          text += "<td class='name'>" + d3.format(',.2s')(base_spend_data[d[i].id]).replace(/G/, "B") + "</td>";
          text += "<td class='name'>" + formatValue(property) + "</td>";
          text += "<td class='name'>" + d3.format(',.2s')(d[i].value).replace(/G/, "B") + "</td></tr><tr>";

        }
        return text
      },

      format: {
        value: function (data) { return d3.format(',s')(data).replace(/G/, "B") }
      }

    },
    point: {
      r: 1
    },
    zoom: {
      enabled: false
    },
    grid: {
      x: {
        lines: [{ value: 0, text: 'you are here' }]
      }
    }
  });

  return chart;
}
function formatValue(value) {
  if (value >= 1e6) {
    return d3.format('.1f')(value / 1e6) + 'M';
  } else if (value >= 1e3) {
    return d3.format('.1f')(value / 1e3) + 'K';
  } else {
    return d3.format('.1f')(value);
  }
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
      var variableNodeIds = [];
      response.forEach(function (item) {
        if (item.level === "Variable") {
          variableNodeIds.push(item.node_id);
        }
      });
      ScenarioTree.rebuildTable(response, variableNodeIds);
      // hide the loader
      MMOUtils.hideLoader();
    },
    error: function (error) {
      MMOUtils.hideLoader();
    }
  });

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

  this.rebuildTable = function (data, nodes) {
    // this.regenerateHead(headers);
    this.regenerateBody(data, nodes);
    // TODO check if this id needs to be parameterized
    $("table#geolevelmarginalreturn_Tbltree").data("simple-tree-table").init();
  };



  this.regenerateBody = function (data, nodes) {
    var me = this;
    $(this.treeBodyNode).html('');

    var htmlTemplate = '';
    // for each row
    $.each(data, function (i, el) {
      if (el.node_id > 2000 && el.node_id < 4000) {
        if (nodes.includes(el.node_id)) {
          htmlTemplate += '<tr data-node-id="' + el.node_id + '" data-node-pid="' + el.parent_node_id + '">';
          htmlTemplate += '<td width="250" class=""> <input id="' + el.node_id + '" type="checkbox" class="geolevelItem"/> &nbsp;' + el.node_display_name + '</td>';
          htmlTemplate += '</tr>';
        } else {
          htmlTemplate += '<tr data-node-id="' + el.node_id + '" data-node-pid="' + el.parent_node_id + '">';
          htmlTemplate += '<td width="250" class="">' + el.node_display_name + '</td>';
          htmlTemplate += '</tr>';
        }
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

function multilineChart(bindto, data) {
  var glines
  var mouseG
  var tooltip

  var parseDate = d3.timeParse("%Y-%m")
  var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]

  var margin = { top: 20, right: 20, bottom: 20, left: 40 }
  var width = $('#' + bindto + '_box').width() * 0.95 - margin.left - margin.right
  var height = 400 - margin.top - margin.bottom

  var lineOpacity = 1
  var lineStroke = "2px"

  var axisPad = 6 // axis formatting
  var R = 6 //legend marker

  var category = d3.map(data, function (d) { return d.node_display_name; }).keys();
  // since Category B and E are really close to each other, assign them diverging colors
  var color = d3.scaleOrdinal()
    .domain(category)
    .range(["#2D4057", "#7C8DA4", "#B7433D", "#2E7576", "#EE811D"])


  var xScale = d3.scaleLinear()
    .domain(d3.extent(data, d => d.spend_change))
    .range([0, width])

  function roundToNearest10K(x) {
    return Math.round(x / 10000) * 10000
  }

  var yScale = d3.scaleLinear()
    .domain([0, roundToNearest10K(d3.max(data, d => d.value))])
    .range([height, 0]);

  var svg = d3.select("#" + bindto + "_box").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append('g')
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


  // CREATE AXES //
  // render axis first before lines so that lines will overlay the horizontal ticks
  var xAxis = d3.axisBottom(xScale).ticks(d3.timeYear.every(1)).tickSizeOuter(axisPad * 2).tickSizeInner(axisPad * 2)
  var yAxis = d3.axisLeft(yScale).ticks(10, "s").tickSize(-width) //horizontal ticks across svg width

  svg.append("g")
    .attr("class", "x axis")
    .attr("transform", `translate(0, ${height})`)
    .call(xAxis)

  svg.append("g")
    .attr("class", "y axis")
    .call(yAxis)
    .call(g => {
      g.selectAll("text")
        .style("text-anchor", "middle")
        .attr("x", -axisPad * 2)
        .attr('fill', '#A9A9A9')

      g.selectAll("line")
        .attr('stroke', '#A9A9A9')
        .attr('stroke-width', 0.7) // make horizontal tick thinner and lighter so that line paths can stand out
        .attr('opacity', 0.3)

      g.select(".domain").remove()

    })
    .append('text')
    .attr('x', 50)
    .attr("y", -10)
    .attr("fill", "#A9A9A9")
    .text("Dollars")


  // CREATE LEGEND //
  var svgLegend = svg.append('g')
    .attr('class', 'gLegend')
    .attr("transform", "translate(" + (width + 20) + "," + 0 + ")")

  var legend = svgLegend.selectAll('.legend')
    .data(category)
    .enter().append('g')
    .attr("class", "legend")
    .attr("transform", function (d, i) { return "translate(0," + i * 20 + ")" })

  legend.append("circle")
    .attr("class", "legend-node")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", R)
    .style("fill", d => color(d))

  legend.append("text")
    .attr("class", "legend-text")
    .attr("x", R * 2)
    .attr("y", R / 2)
    .style("fill", "#A9A9A9")
    .style("font-size", 12)
    .text(d => d)

  // line generator
  var line = d3.line()
    .x(d => xScale(d.spend_change))
    .y(d => yScale(d.value))

  renderChart() // inital chart render (set default to Bidding Exercise 1 data)

  // Update chart when radio button is selected


  function renderChart() {

    var res_nested = d3.nest() // necessary to nest data so that keys represent each vehicle category
      .key(d => d.node_display_name)
      .entries(data)

    // APPEND MULTIPLE LINES //
    var lines = svg.append('g')
      .attr('class', 'lines')

    glines = lines.selectAll('.line-group')
      .data(res_nested).enter()
      .append('g')
      .attr('class', 'line-group')

    glines
      .append('path')
      .attr('class', 'line')
      .attr('d', d => line(d.values))
      .style('stroke', (d, i) => color(i))
      .style('fill', 'none')
      .style('opacity', lineOpacity)
      .style('stroke-width', lineStroke)


    // APPEND CIRCLE MARKERS //
    //var gcircle = lines.selectAll("circle-group")
    //.data(res_nested).enter()
    //.append("g")
    //.attr('class', 'circle-group')

    //gcircle.selectAll("circle")
    //.data(d => d.values).enter()
    //.append("g")
    //.attr("class", "circle")
    //.append("circle")
    //.attr("cx", d => xScale(d.date))
    //.attr("cy", d => yScale(d.premium))
    //.attr("r", 2)

    // CREATE HOVER TOOLTIP WITH VERTICAL LINE //
    tooltip = d3.select("#chart").append("div")
      .attr('id', 'tooltip')
      .style('position', 'absolute')
      .style("background-color", "#D3D3D3")
      .style('padding', 6)
      .style('display', 'none')

    mouseG = svg.append("g")
      .attr("class", "mouse-over-effects");

    mouseG.append("path") // create vertical line to follow mouse
      .attr("class", "mouse-line")
      .style("stroke", "#A9A9A9")
      .style("stroke-width", lineStroke)
      .style("opacity", "0");

    var lines = document.getElementsByClassName('line');

    var mousePerLine = mouseG.selectAll('.mouse-per-line')
      .data(res_nested)
      .enter()
      .append("g")
      .attr("class", "mouse-per-line");

    mousePerLine.append("circle")
      .attr("r", 4)
      .style("stroke", function (d) {
        return color(d.key)
      })
      .style("fill", "none")
      .style("stroke-width", lineStroke)
      .style("opacity", "0");

    mouseG.append('svg:rect') // append a rect to catch mouse movements on canvas
      .attr('width', width)
      .attr('height', height)
      .attr('fill', 'none')
      .attr('pointer-events', 'all')
      .on('mouseout', function () { // on mouse out hide line, circles and text
        d3.select(".mouse-line")
          .style("opacity", "0");
        d3.selectAll(".mouse-per-line circle")
          .style("opacity", "0");
        d3.selectAll(".mouse-per-line text")
          .style("opacity", "0");
        d3.selectAll("#tooltip")
          .style('display', 'none')

      })
      .on('mouseover', function () { // on mouse in show line, circles and text
        d3.select(".mouse-line")
          .style("opacity", "1");
        d3.selectAll(".mouse-per-line circle")
          .style("opacity", "1");
        d3.selectAll("#tooltip")
          .style('display', 'block')
      })
      .on('mousemove', function () { // update tooltip content, line, circles and text when mouse moves
        var mouse = d3.mouse(this)

        d3.selectAll(".mouse-per-line")
          .attr("transform", function (d, i) {
            var xDate = xScale.invert(mouse[0]) // use 'invert' to get date corresponding to distance from mouse position relative to svg
            var bisect = d3.bisector(function (d) { return d.date; }).left // retrieve row index of date on parsed csv
            var idx = bisect(d.values, xDate);

            d3.select(".mouse-line")
              .attr("d", function () {
                var data = "M" + xScale(d.values[idx].spend_change) + "," + (height);
                data += " " + xScale(d.values[idx].spend_change) + "," + 0;
                return data;
              });
            return "translate(" + xScale(d.values[idx].spend_change) + "," + yScale(d.values[idx].value) + ")";

          });

        updateTooltipContent(mouse, res_nested)

      })

  }

  function updateTooltipContent(mouse, res_nested) {
    sortingObj = []
    res_nested.map(d => {
      var xDate = xScale.invert(mouse[0])
      var bisect = d3.bisector(function (d) { return d.spend_change; }).left
      var idx = bisect(d.values, xDate)
      sortingObj.push({ key: d.values[idx].node_display_name, value: d.values[idx].value })
    })

    sortingObj.sort(function (x, y) {
      return d3.descending(x.value, y.value);
    })

    var sortingArr = sortingObj.map(d => d.key)

    var res_nested1 = res_nested.slice().sort(function (a, b) {
      return sortingArr.indexOf(a.key) - sortingArr.indexOf(b.key) // rank vehicle category based on price of premium
    })

    tooltip.html(sortingObj[0].month + "-" + sortingObj[0].year + " (Bidding No:" + sortingObj[0].bidding_no + ')')
      .style('display', 'block')
      .style('left', d3.event.pageX + 20)
      .style('top', d3.event.pageY - 20)
      .style('font-size', 11.5)
      .selectAll()
      .data(res_nested1).enter() // for each vehicle category, list out name and price of premium
      .append('div')
      .style('color', d => {
        return color(d.key)
      })
      .style('font-size', 10)
      .html(d => {
        var xDate = xScale.invert(mouse[0])
        var bisect = d3.bisector(function (d) { return d.spend_change; }).left
        var idx = bisect(d.values, xDate)
        return d.key.substring(0, 3) + " " + d.key.slice(-1) + ": $" + d.values[idx].value.toString()
      })
  }


}
function height_channels(data) {
  if (data.length > 50) {
    return 900;
  }
  else {
    return 400;
  }
}

$(".download_marginal_curves").on("click", function () {
  var selectedNodes = [];
  var scenario_id = $("#base_plan_ddl").val();
  $.each($("input[class='geolevelItem']:checked"), function () {
    selectedNodes.push($(this).attr("id"));
  });

  // document.location.href = "/download_marginal_return_curves_data?nodes=" + JSON.stringify(selectedNodes)+ "&scenario_id=" + Number(scenario_id);

  document.location.href = "/download_marginal_return_curves_data?nodes=" + JSON.stringify(selectedNodes);
})
