var ScenarioTree = {};
var DEFAULT_SCENARIO_ONE = 4;
// will need to move this tree config to a config file for easy editing
var SUBHEADERSSPENDS = [{
	title: 'Total($)'
	, editable: false
	, custom: false
	, key: 'total',
	roundoff: 0
}, {
	title: 'Allocation(%)'
	, editable: false
	, custom: false
	, key: 'pct',
	roundoff: 1
}];

var SUBHEADERS = [{
	title: 'Total'
	, editable: false
	, custom: false
	, key: 'total',
	roundoff: 0
}
	, {
	title: 'Attribution(%)'
	, editable: false
	, custom: false
	, key: 'pct',
	roundoff: 1
}
	, {
	title: 'Efficiency'
	, editable: false
	, custom: false
	, key: 'efficiency',
	roundoff: 1
}
	, {
	title: 'coutcome2($)'
	, editable: false
	, custom: false
	, key: 'roi',
	roundoff: 0
}
];

var SUBHEADERSHHCOUNT = [{
	title: 'Total'
	, editable: false
	, custom: false
	, key: 'total',
	roundoff: 0
}
	, {
	title: 'Attribution(%)'
	, editable: false
	, custom: false
	, key: 'pct',
	roundoff: 1
}
	, {
	title: 'Efficiency'
	, editable: false
	, custom: false
	, key: 'efficiency',
	roundoff: 1
}
	, {
	title: 'coutcome1($)'
	, editable: false
	, custom: false
	, key: 'roi',
	roundoff: 0
}
];


var HEADER_STRUCTURE = {
	"default": [
		{
			title: 'Spend'
			, key: 'spend_value'
			, subheaders: SUBHEADERSSPENDS
		},
		{
			title: 'Otcome2',
			key: 'outcome2',
			subheaders: SUBHEADERS
		},
		{
			title: 'Outcome1',
			key: 'outcome1',
			subheaders: SUBHEADERSHHCOUNT
		},
	]
};

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
	ScenarioTree = new MMOTree({
		//tableNode: {'id': "table#geolevel_Tbltree", 'class': "simple-tree-table"},
		treeHeadNode: '.treeDataHeader',
		treeBodyNode: '.treeDatabody',
		headerStructure: HEADER_STRUCTURE,
		formatCellData: formatCellData
	});
	timeperiod()
	$.ajax({
		url: '/get_reporting_allocations_list',
		type: 'GET',
		dataType: "json",
		processData: false,
		contentType: false,
		headers: {
			"content-type": "application/json",
			"cache-control": "no-cache"
		},
		success: function (response) {
			$("#allocation_year").html();
			MMOUtils.buildDDlFromList("#allocation_year", response);
			$("#allocation_year").selectpicker("refresh");
			var arr = [];
			for (var key in response) {
				if (response.hasOwnProperty(key)) {
					arr.push([key, response[key]]);
				}
			}
			$("#allocation_year").find('option[value="' + arr[0][1] + '"]').attr('selected', 'selected')
			$("#allocation_year").selectpicker("refresh");
			var inputs = {}
			inputs.allocation_year = $("#allocation_year").val();
			inputs.period_type = 'year'
			inputs.quarter = '1'
			inputs.level = $("#level_drop_down").val();
			inputs.month = '1'
			get_allocation_data(inputs);

		},
		error: function (error) {
			MMOUtils.hideLoader();
		}
	});
	function geolevelsearch() {
		var value = $(this).val().toLowerCase();
		$("#dropdowntree tr").filter(function () {
			$(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
		});
	}
	// var inputs = {}
	// inputs.allocation_year = $("#allocation_year").val();
	// inputs.period_type = 'year'
	// inputs.quarter = ''
	// inputs.level = $("#level_drop_down").val();
	// inputs.month = ''
	$("body").on("click", "a.toggle-btn", toggleContent);
	//Load default allocation data
	// get_allocation_data(inputs);
	marginalreturnGeolevelTree();
	$("body").on("click", "#compareBarChartapplyBtn", selectedLevels)
	$("body").on("keyup", "#geolevelsearchBox", geolevelsearch);
	$("body").on("change", "#allocation_year,#period_type,#quarterddl,#level_drop_down,#monthddl", function () {
		MMOUtils.showLoader();
		var allocation_year = $("#allocation_year").val()
		var period_type = $("#period_type").val();
		if (period_type === "quarter") {
			$("#monthddl-item").hide();
			$("#quarterddl-item").show();
		} else if (period_type === "year") {
			$("#monthddl-item").hide();
			$("#quarterddl-item").hide();
		}
		else {
			$("#monthddl-item").show();
			$("#quarterddl-item").hide();
		}
		// period_type == "year" ? $("#quarterddl-item").hide() : $("#quarterddl-item").show()
		var quarter = $("#quarterddl").val()
		var level = $("#level_drop_down").val()
		var month = $("#monthddl").val()
		var inputs = {}
		inputs.allocation_year = allocation_year
		inputs.period_type = period_type
		inputs.quarter = quarter
		inputs.level = level
		inputs.month = month
		var viewtype = $("a.toggle-btn.active").attr('href');
		if (viewtype != '#tabular') {
			selectedLevels()
			// marginalreturnGeolevelTree()
			$("#touchpoints_ddl").show();
		}
		else {
			$("#touchpoints_ddl").hide();
			get_allocation_data(inputs);
		}
	},
	)
	$("body").on("change", "#level_drop_down", function () {
		MMOUtils.showLoader();
		var allocation_year = $("#allocation_year").val()
		var period_type = $("#period_type").val();
		if (period_type === "quarter") {
			$("#monthddl-item").hide();
			$("#quarterddl-item").show();
		} else if (period_type === "year") {
			$("#monthddl-item").hide();
			$("#quarterddl-item").hide();
		}
		else {
			$("#monthddl-item").show();
			$("#quarterddl-item").hide();
		}
		// period_type == "year" ? $("#quarterddl-item").hide() : $("#quarterddl-item").show()
		var quarter = $("#quarterddl").val()
		var level = $("#level_drop_down").val()
		var month = $("#monthddl").val()
		var inputs = {}
		inputs.allocation_year = allocation_year
		inputs.period_type = period_type
		inputs.quarter = quarter
		inputs.level = level
		inputs.month = month
		var viewtype = $("a.toggle-btn.active").attr('href');
		if (viewtype != '#tabular') {
			selectedLevels()
			marginalreturnGeolevelTree()
			$("#touchpoints_ddl").show();
		}
		else {
			$("#touchpoints_ddl").hide();
			get_allocation_data(inputs);
		}
	},
	)

	$(".downloadscenario").on("click", function () {
		var year = $("#allocation_year").val()
		var period_type = $("#period_type").val();
		var quarter = $("#quarterddl").val()
		var month = $("#monthddl").val()

		document.location.href = "/download_reporting_allocations?period_type=" + period_type + "&year=" + year + "&quarter=" + quarter + "&month=" + month + "&download_type=csv"
	})

	$(".download_excel").on("click", function () {
		var year = $("#allocation_year").val()
		var period_type = $("#period_type").val();
		var quarter = $("#quarterddl").val()

		document.location.href = "/download_reporting_allocations?period_type=" + period_type + "&year=" + year + "&quarter=" + quarter + "&download_type=excel"
	})

});

function formatCellData(cellData, roundoff) {
	fmtcellData = cellData == "NA" || cellData == "" ? "" : MMOUtils.commaSeparatevalue(MMOUtils.round(MMOUtils.replaceComma(cellData), roundoff).toFixed(roundoff))
	return fmtcellData;
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
			if (nodeIds[i] > 4000) {
				totalValue = control_totals[h.key]
			}
			else {
				totalValue = media_totals[h.key]
			}

			// get the cell value for the header and calculate the percent
			cellKeyValue = ScenarioTree.getCellId(nodeIds[i], h.key, 'total');
			pctValue = ScenarioTree.getCellData(cellKeyValue) / totalValue * 100;
			//pctValue = ScenarioTree.getCellData(cellKeyValue) / 1000000 * 100;

			// get the cell id and update the pct
			cellKeyPct = ScenarioTree.getCellId(nodeIds[i], h.key, 'pct');
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

function get_allocation_data(inputs) {
	const queryString = $.param(inputs);

	$.ajax({
		url: "/get_reporting_allocations?" + queryString,
		type: 'GET',
		dataType: "json",
		headers: {
			"content-type": "application/json",
			"cache-control": "no-cache"
		},
		success: function (response) {
			$("#touchpoints_ddl").hide();
			if (response['allocation'].length == 0) {
				ScenarioTree.resetTree();
				$('#app_error').modal('show');
			}
			else {
				// Initialize the tree again as the trees structure changes
				ScenarioTree = new MMOTree({
					treeHeadNode: '.treeDataHeader',
					treeBodyNode: '.treeDatabody',
					headerStructure: HEADER_STRUCTURE,
					formatCellData: formatCellData
				});
				ScenarioTree.refreshTable(response['allocation'], 'default', 'total');
				ScenarioTree.refreshTable(response["attribution"], 'default', 'pct');
				ScenarioTree.refreshTable(response["efficiency"], 'default', 'efficiency');
				ScenarioTree.refreshTable(response["metric"], 'default', 'roi');
			}
			MMOUtils.hideLoader();
		},
		error: function (error) {
			ScenarioTree.resetTree();
			MMOUtils.hideLoader();
		}
	});

}

$(document).ajaxError(function myErrorHandler(event, xhr, ajaxOptions, thrownError) {
	if (xhr.status == 303) {
		$("#error_message").html("<p>" + xhr.responseText + "</p>")
	}
	$('#app_error').modal('show');
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
function toggleContent() {
	marginalreturnGeolevelTree()
	var level = $("#level_drop_down").val()
	$("a.toggle-btn").removeClass("active");
	var viewtype = $(this).attr('href');
	if (viewtype == '#tabular') {
		$("#Compare-graphs").hide();
		$("#Compare-metricTblBox").show();
		$("#touchpoints_ddl").hide();
	}
	else {
		$("#Compare-graphs").show();
		selectedLevels()
		if (level != "Level 1") {
			$("#touchpoints_ddl").show();
		}
		$("#Compare-metricTblBox").hide();
	}
	$(this).addClass("active");
}

function selectedLevels() {
	MMOUtils.showLoader();
	var checkedItems = [];
	var selectedNodes = {}
	$.each($("input[class='geolevelItem']:checked"), function () {
		checkedItems.push($(this).attr("id"));
	});

	selectedNodes['nodes'] = checkedItems;

	var allocation_year = $("#allocation_year").val()
	var period_type = $("#period_type").val();
	// period_type == "year" ? $("#quarterddl-item").hide() : $("#quarterddl-item").show()
	if (period_type === "quarter") {
		$("#monthddl-item").hide();
		$("#quarterddl-item").show();
	} else if (period_type === "year") {
		$("#monthddl-item").hide();
		$("#quarterddl-item").hide();
	}
	else {
		$("#monthddl-item").show();
		$("#quarterddl-item").hide();
	}
	var quarter = $("#quarterddl").val()
	var level = $("#level_drop_down").val()
	var month = $("#monthddl").val()
	var inputs = {}
	inputs.allocation_year = allocation_year
	inputs.period_type = period_type
	inputs.quarter = quarter
	inputs.nodes = checkedItems
	inputs.level = level
	inputs.month = month
	// marginalreturnGeolevelTree()
	graphallocation_data(inputs)
	if ($(".maindropdown").hasClass('active')) {
		$('.main-dropdown-menu').hide();
		$(".maindropdown").removeClass('active');
	}
	else {
		$(".maindropdown").addClass('active');
		$('.main-dropdown-menu').show();
	}
}

function marginalreturnGeolevelTree() {

	// fetch the data
	var level = $("#level_drop_down").val()
	var inputs = {}
	inputs.level = level
	$.ajax({
		url: "/get_media_hierarchy_list",
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
			var scenarioDetails = {};
			// get the required response to update the select box
			DropdownTree.rebuildTable(response);
			if (inputs.level == "Level 1") {
				$("#touchpoints_ddl").hide();
			}
		},
		error: function (error) {
		}
	});

}
function timeperiod() {
	MMOUtils.hideLoader()
	$(".preloader-progress").show()
	var progress = $(".loading-progress").progressTimer({
		timeLimit: 20,
		onFinish: function () {
			$(".preloader-progress").hide()
		},
	});
	var startTime = new Date().getTime();
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
			var endTime = new Date().getTime();
			var timeTaken = (endTime - startTime) / 1000;
			$('#timePeriodInfo').html(
				`<p>${response.min_date} To ${response.max_date}</p>`
			);
			progress.progressTimer('setTime', timeTaken);
			progress.progressTimer('complete');

		},
		error: function (error) {
			progress.progressTimer('error', {
				errorText: 'ERROR!',
				onFinish: function () {
					alert('There was an error processing your information!');
				}
			});
		}
	});
}
function serializeNodes(nodes) {
	return nodes.join(',');
}

function serializeObject(obj) {
	const serializedNodes = obj.nodes ? `nodes=${serializeNodes(obj.nodes)}` : '';
	queryArray = []
	for (key in obj) {
		if (key != 'nodes') {
			queryArray.push(`${key}=${obj[key]}`)
		}
	}
	if (obj.nodes.length > 0) {
		queryArray.push(serializedNodes)
	}
	const queryString = queryArray.filter(Boolean).join('&');
	return queryString;
}


function graphallocation_data(inputs) {
	const queryString = serializeObject(inputs);
	MMOUtils.showLoader();
	var viewtype = $("a.toggle-btn.active").attr('href');
	if (viewtype == '#graph') {
		if (inputs.level == "Level 1") {
			$("#touchpoints_ddl").hide();
		}
		else {
			$("#touchpoints_ddl").show();
		}
	}

	$.ajax({
		url: "/get_reporting_allocations_graph?" + queryString,
		type: 'GET',
		dataType: "json",
		headers: {
			"content-type": "application/json",
			"cache-control": "no-cache"
		},
		success: function (response) {
			if (inputs.level == "Level 1") {
				$("#touchpoints_ddl").hide();
			}
			else {
				$("#touchpoints_ddl").show();
			}
			// if (response['allocation'].length == 0) {
			// 	ScenarioTree.resetTree();
			// 	$('#app_error').modal('show');
			// }
			// else {
			// 	ScenarioTree.refreshTable(response['allocation'], 'default', 'total');
			// 	ScenarioTree.refreshTable(response["attribution"], 'default', 'pct');
			// 	ScenarioTree.refreshTable(response["efficiency"], 'default', 'efficiency');
			// 	ScenarioTree.refreshTable(response["metric"], 'default', 'roi');
			// } why we have added this? question
			$("#Compare-graphs").html("");
			// var outcome = $("a.active.metricLink").text();
			var htmlTemplate = '<div class="card pt-3"><h4 class="text-center">Spend</h4><div class="graph pt-0" id="spendComparison_box" style="height: 520px;width:100%">' + chart1 + '</div></div>';
			htmlTemplate += '<div class="card pt-3"><h4 class="text-center">outcome2 & outcome1</h4><div class="graph pt-0" id="socComparison_box" style="height: 520px;width:100%">' + chart2 + '</div></div>'
			$("#Compare-graphs").append(htmlTemplate);

			var chart1 = bargraphGenerate("spendComparison", response);
			var chart2 = bargraphGenerate("socComparison", response);
			// var chart4 = comboLineChartGenerate(chartId4, allocationData, attributionData, 'ntf_hh');

			if ($(".maindropdown").hasClass('active')) {
				$('.main-dropdown-menu').hide();
				$(".maindropdown").removeClass('active');
			}
			MMOUtils.hideLoader();
		},
		error: function (error) {
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
							if (id.indexOf("Count") > 0) {
								if (Math.abs(v) >= 1e6) {
									return d3.format('.1f')(v / 1e6) + "M";
								} else if (Math.abs(v) >= 1e3) {
									return d3.format('.1f')(v / 1e3) + "K";
								} else if (v == 0) {
									return "0"; // Add a decimal to 0
								}
								else {
									return d3.format(',s')(v).replace(/G/, "B");
								}
							} else {
								if (Math.abs(v) >= 1e6) {
									return d3.format('.1f')(v / 1e6) + "M";
								} else if (Math.abs(v) >= 1e3) {
									return d3.format('.1f')(v / 1e3) + "K";
								}
								else if (v == 0) {
									return "0"; // Add a decimal to 0
								}
								else {
									return d3.format(',s')(v).replace(/G/, "B");
								}
							}
						}
					} else {
						return "";
					}
				}

			},
			order: null,
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
function getYAxisLabel(data_field) {
	switch (data_field) {
		case 'spend_value':
			return 'Allocation Spend';
		case 'ntf_assets':
			return 'Allocation #outcome2';
		case 'ntf_hh':
			return 'Allocation coutcome1';
		case 'ext_ai':
			return 'Allocation #outcome1';
		default:
			return 'Y Label';
	}
}

function height_channels(data) {
	if (data.length > 50) {
		return 600;
	}
	else {
		return 200;
	}
}
function getformatLabel(data_field) {
	switch (data_field) {
		case 'spend_value':
			return d3.format("$.2s");
		default:
			return d3.format(".2s")
	}
}