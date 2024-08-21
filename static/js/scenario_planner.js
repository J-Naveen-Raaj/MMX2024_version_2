var ScenarioTree = {};
var ScenarioSummeryBox = {};
var scnriospendval = 0;
var quarters = ['Q1', 'Q2', 'Q3', 'Q4']
var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// will need to move this tree config to a config file for easy editing
var SUBHEADERS = [{
	title: 'Current($)',
	editable: false,
	custom: false,
	key: 'current'
}, {
	title: 'New($)',
	editable: true,
	custom: false,
	key: 'new'
}, {
	title: 'Change($)',
	editable: false,
	custom: true,
	key: 'delta'
}];

var TOTAL_SUBHEADERS = [{
	title: 'Current($)',
	editable: false,
	custom: false,
	key: 'current'
}, {
	title: 'New($)',
	editable: false,
	custom: false,
	key: 'new'
}, {
	title: 'Change($)',
	editable: false,
	custom: true,
	key: 'delta'
}];

var HEADER_STRUCTURE = {
	"yearly": [{
		title: 'Annual',
		key: 'Year',
		subheaders: SUBHEADERS
	}],
	"halfyearly": [{
		title: 'H1',
		key: 'H1',
		subheaders: SUBHEADERS
	},
	{
		title: 'H2',
		key: 'H2',
		subheaders: SUBHEADERS
	},
	{
		title: 'Total',
		key: 'Total',
		subheaders: TOTAL_SUBHEADERS
	}
	],
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
		subheaders: TOTAL_SUBHEADERS
	}
	],
	"monthly": [{
		title: 'January',
		key: 'Jan',
		subheaders: SUBHEADERS
	},
	{
		title: 'February',
		key: 'Feb',
		subheaders: SUBHEADERS
	},
	{
		title: 'March',
		key: 'Mar',
		subheaders: SUBHEADERS
	},
	{
		title: 'April',
		key: 'Apr',
		subheaders: SUBHEADERS
	},
	{
		title: 'May',
		key: 'May',
		subheaders: SUBHEADERS
	},
	{
		title: 'June',
		key: 'Jun',
		subheaders: SUBHEADERS
	},
	{
		title: 'July',
		key: 'Jul',
		subheaders: SUBHEADERS
	},
	{
		title: 'August',
		key: 'Aug',
		subheaders: SUBHEADERS
	},
	{
		title: 'September',
		key: 'Sep',
		subheaders: SUBHEADERS
	},
	{
		title: 'October',
		key: 'Oct',
		subheaders: SUBHEADERS
	},
	{
		title: 'November',
		key: 'Nov',
		subheaders: SUBHEADERS
	},
	{
		title: 'December',
		key: 'Dec',
		subheaders: SUBHEADERS
	},
	{
		title: 'Total',
		key: 'Total',
		subheaders: TOTAL_SUBHEADERS
	}
	]
};

var METRICTYPES = [{
	title: 'Overall Change',
	key: 'Overall-Change'
}, {
	title: 'NTF-Assets-IN',
	key: 'NTF-Assets-IN'
}, {
	title: 'Existing-Assets-in',
	key: 'Existing-Assets-in'
},
{
	title: 'NTF-HH-Count',
	key: 'NTF-HH-Count'

}
];

var summeryData = [{
	"name": "Current Scenario",
	"ChangeType": 1,
	"Current Value": 0,
	"Change": 0
},
{
	"name": "New Scenario",
	"Current Value": 0,
	"ChangeType": 1,
	"Change": 0
}
];


$(function () {
	timeperiod()

	MMOUtils.hideLoader();
	PageBodyEvents();

	// Initialize the tree with the required nodes
	ScenarioTree = new MMOTree({
		//tableNode: {'id': "table#geolevel_Tbltree", 'class': "simple-tree-table"},
		treeHeadNode: '.treeDataHeader',
		treeBodyNode: '.treeDatabody',
		headerStructure: HEADER_STRUCTURE,
		formatCellData: formatCellData,
		changeHandler: updateField,
		planner: true
		//getCustomFieldValue: getCustomFieldValue;
	});
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
			MMOUtils.hideLoader()
		},
		error: function (error) {
			MMOUtils.hideLoader();
		}
	});
}
function formatCellData(cellData, roundoff) {
	return MMOUtils.commaSeparatevalue(MMOUtils.round(MMOUtils.replaceComma(cellData), 0));
}

function updateField(e) {
	e.preventDefault();
	e.stopPropagation();
	MMOUtils.showLoader();
	var fieldName = this.name;
	var fieldValue = MMOUtils.replaceComma(this.value);
	var fieldId = this.id;
	var fieldNameParts = fieldName.split('_');

	//var fieldIdPrefix = fieldId

	// the payload for the request
	var updateInputs = {
		scenario_name: $("#selectScenario").val(),
		node_id: fieldNameParts[1],
		period_name: fieldNameParts[2],
		period_type: fieldNameParts[2],
		new_val: fieldValue,
	}

	// make the ajax call to update the session
	const queryString = $.param(updateInputs);
	$.ajax({
		url: '/changenodespend?' + queryString,
		type: 'GET',
		dataType: "json",
		headers: {
			"content-type": "application/json",
			"cache-control": "no-cache"
		},
		success: function (response) {
			var responseData = response.fmt_data;
			// need to update the reformatted value only if update succeeds
			//ScenarioTree.updateCell(fieldId, fieldValue);
			// update the delta
			//setDeltaValue(ScenarioTree.findHeader(fieldNameParts[2]), fieldNameParts[1]);
			var slectscenariSpend = response.summary;

			summeryData[1]["Current Value"] = slectscenariSpend
			summeryData[1]["Change"] = slectscenariSpend;

			summaryChartnDatablocks(summeryData);

			periodType = $("#whatif_Level").val();
			ScenarioTree.refreshTable(responseData, periodType, "new");
			setDeltaValues();
			var nodeIds = [...new Set(ScenarioTree.getAllNodeIds())];
			var calculated_new_spend = 0;
			var node_id = '';
			var change_in_spend_percent = 0
			$.each(nodeIds, function (index, value) {
				if (periodType == "yearly") {
					node_id = 'row_' + value + '_Year_new';
					calculated_new_spend += +ScenarioTree.getCellData(node_id);
				}
				else if (periodType == "qtrly") {
					for (let i = 0; i < quarters.length; i++) {
						node_id = 'row_' + value + '_' + quarters[i] + '_new';
						calculated_new_spend += +ScenarioTree.getCellData(node_id);
					}
				}
				else if (periodType == "monthly") {
					for (let i = 0; i < months.length; i++) {
						node_id = 'row_' + value + '_' + months[i] + '_new';
						calculated_new_spend += +ScenarioTree.getCellData(node_id);
					}
				}
			})
			var rounded_change_in_spend = ((calculated_new_spend - scnriospendval) / scnriospendval) * 100;
			change_in_spend_percent = rounded_change_in_spend.toFixed(2)
			$('#calculated_spend').text(d3.formatPrefix("$.1", MMOUtils.round(calculated_new_spend, 0))(MMOUtils.round(calculated_new_spend, 0)))
			// set the bar charts to the changed scenario spend for comparison
			summeryData[0]["Current Value"] = scnriospendval
			summeryData[0]["Change"] = scnriospendval;
			// change the default name if its changed
			summeryData[0]["name"] = $("#selectScenario option:selected").text() === 'Select'
				? 'Actuals 2020' : $("#selectScenario option:selected").text();
			summeryData[1]["Current Value"] = calculated_new_spend;
			summeryData[1]["Change"] = calculated_new_spend;
			summeryData[1]["name"] = 'Scenario Spend';
			summaryChartnDatablocks(summeryData);
			$('#chnginspnd').text(change_in_spend_percent);
			MMOUtils.hideLoader();
		},
		error: function (error) {
			// if update fails the change should not reflect in the UI
			ScenarioTree.updateCell(fieldId, ScenarioTree.getCellData(fieldId));
			MMOUtils.hideLoader();
		}
	});
}

function setDeltaValues(elementId, subheaderKey) {
	var nodeIds = ScenarioTree.getAllNodeIds();
	var rowCnt = nodeIds.length;
	var headers = ScenarioTree.getHeaders();

	// TODO: potential bug... Works for now.
	// this is technically not correct, i need not be the the same as node_id...
	for (i = 0; i < rowCnt; i++) {
		$.each(headers, function (j, h) {
			setDeltaValue(h, nodeIds[i]);
		});
	}
}

function setDeltaValue(h, i) {
	var currentValId;
	var newValId;
	var deltaValId;
	currentValId = ScenarioTree.getCellId(i, h.key, 'current');
	newValId = ScenarioTree.getCellId(i, h.key, 'new');
	deltaValId = ScenarioTree.getCellId(i, h.key, 'delta');
	ScenarioTree.updateCell(deltaValId, ScenarioTree.getCellData(newValId) - ScenarioTree.getCellData(currentValId));
}

function PageBodyEvents() {
	$(".preloader-progress").show()
	var progress = $(".loading-progress").progressTimer({
		timeLimit: 20,
		onFinish: function () {
			// Callback function when the timer finishes
			$(".preloader-progress").hide()
		},
	});
	// Ajax call to the API
	var startTime = new Date().getTime();
	$.ajax({
		url: "/userscenario/1?scenario_name=&period_type=",
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
			if (response.message) {
				var scenariosListdata = response.scenario_list;
				$("#selectScenario").html();
				MMOUtils.buildDDlFromList("#selectScenario", scenariosListdata);
				$("#selectScenario").selectpicker("refresh");
			}
			else {
				var scenariosListdata = response.scenario_list;
				var summary = response.summary;

				summeryData[0]["Current Value"] = summary.curntspend;
				summeryData[0]["name"] = response.scenario_name;
				summeryData[0]["Change"] = 0;

				summeryData[1]["name"] = "Scenario Spend";
				summeryData[1]["Current Value"] = summary.curntspend;
				summeryData[1]["Change"] = 0;

				summaryChartnDatablocks(summeryData);
				$("#selectScenario").html();
				MMOUtils.buildDDlFromList("#selectScenario", scenariosListdata);
				$("#selectScenario").selectpicker("refresh");
				//change the value for setting the default scenario name
				$("#selectScenario").find('option[value="5"]').attr('selected', 'selected')
				$("#selectScenario").selectpicker("refresh");

				// display the default scenario on the LHS of the table
				periodType = $("#whatif_Level").val();
				response.spendDetaildata.sort(function (a, b) {
					node1 = a.node_disp_name.toLowerCase();
					node2 = b.node_disp_name.toLowerCase();
					return (node1 < node2) ? -1 : (node1 > node2) ? 1 : 0;
				});
				ScenarioTree = new MMOTree({
					//tableNode: {'id': "table#geolevel_Tbltree", 'class': "simple-tree-table"},
					treeHeadNode: '.treeDataHeader',
					treeBodyNode: '.treeDatabody',
					headerStructure: HEADER_STRUCTURE,
					formatCellData: formatCellData,
					changeHandler: updateField,
					planner: true
					//getCustomFieldValue: getCustomFieldValue;
				});
				ScenarioTree.refreshTable(response.spendDetaildata, periodType, 'current');
				ScenarioTree.refreshTable(response.spendDetaildata, periodType, 'new');
			}
			var endTime = new Date().getTime();
			var timeTaken = (endTime - startTime) / 1000;
			$(".comparison-main-content").hide()
			$(".analysissummeryBox").hide()
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
		}
	});

	// register the listeners for events
	$("body").on("change", "#selectScenario", scenarioChange);
	$("body").on("change", "#whatif_Level", levelChange);
	$("body").on("click", "#save_scenario_btn", saveScenario);

	$("#importSampleData").on("click", function () {
		var period_type = $("#whatif_Level").val();
		var scenario_id = $("#selectScenario").val();
		$.ajax({
			url: "/download_scenario_planning_report?period_type=" + period_type + "&scenario_id=" + scenario_id,
			type: 'GET',
			success: function () {
				document.location.href = "/download_scenario_planning_report?period_type=" + period_type + "&scenario_id=" + scenario_id;

			},
			error: function (xhr, textStatus, errorThrown) {
				$("#plannererrorLabel").text("Error");
				$(".modal-header").addClass("btn-danger").removeClass("btn-success");
				$(".modal-body").text("No data for current selection");
				return $("#plannererror").modal('show');
			}
		});
	})
}

function scenarioChange() {
	// fetch the data and refresh the tree
	updateScenarioDetails($(this).val(), $("#whatif_Level").val());
	//setDeltaValues();
}

// new scenario name change
$("#savescnrip").on("keyup", function () {
	var scenario_name = $(this).val()
	if (scenario_name.trim() !== null && undefined !== scenario_name.trim()
		&& scenario_name.trim() !== "") {
		$("#save_scenario_btn").removeAttr('disabled')
	} else {
		$("#save_scenario_btn").attr('disabled', true)
	}
})

function levelChange() {
	$(".comparison-main-content").show();
	// fetch the data and refresh the tree
	var level = $(this).val()
	var selectedScenario = $("#selectScenario").val();

	// get the scenario details
	if (level == 'weekly') {
		$(".comparison-main-content").hide();
	}
	else if (level == 'qtrly') {
		$(".comparison-main-content").addClass('quaterlevel')
	}
	else if (level == 'monthly') {
		$(".comparison-main-content").removeClass('quaterlevel')
		$(".comparison-main-content").addClass('monthlevel')
	}
	else {
		$(".comparison-main-content").removeClass('quaterlevel')
		$(".comparison-main-content").removeClass('monthlevel')
	}
	updateScenarioDetails($("#selectScenario").val(), level);
	//setDeltaValues();
}

function updateScenarioDetails(scenarioName, periodType) {
	$('#chnginspnd').text("0")
	MMOUtils.showLoader();
	summeryData[0]["Change"] = 0;
	summeryData[0]["name"] = "";
	// fetch the data
	$.ajax({
		url: '/userscenario/1?scenario_name=' + scenarioName + '&period_type=' + periodType,
		type: 'GET',
		dataType: "json",
		processData: false,
		contentType: false,
		headers: {
			"content-type": "application/json",
			"cache-control": "no-cache"
		},
		success: function (response) {
			if (response.message) {
				$(".comparison-main-content").hide()
				$(".analysissummeryBox").hide()
				$(".preloader").hide();
				$("#plannererrorLabel").text("Error");
				$(".modal-header").addClass("btn-danger").removeClass("btn-success");
				$(".modal-body").text("please select scenario");
				return $("#plannererror").modal('show');
			}
			else {
				if (periodType == "weekly") {
					$(".comparison-main-content").hide()
				}
				else { $(".comparison-main-content").show() }
				$(".analysissummeryBox").show()
				var scenarioDetails = {};
				if (response == null) {
					MMOUtils.hideLoader();
					$('#app_error').modal('show');
				}
				else {
					// get the required response to update the select box
					scenarioDetails.spendDetails = response.spendDetaildata;
					scenarioDetails.summaryData = response.summary;
					scenarioDetails.scenarioName = response.scenario_name;

					var slectscenariSpend = response.spendDetaildata[0].node_data.Total;
					var curntScenarioText = $("#selectScenario option:selected").text();


					summeryData[0]["Current Value"] = scenarioDetails.summaryData["scnriospend"];
					summeryData[0]["Change"] = scenarioDetails.summaryData["scnriospend"];
					summeryData[0]["name"] = curntScenarioText === 'Select' ? 'Actuals 2020' : curntScenarioText;
					summeryData[1]["Current Value"] = scenarioDetails.summaryData["scnriospend"];
					summeryData[1]["Change"] = scenarioDetails.summaryData["scnriospend"];
					summeryData[1]["name"] = "Scenario Spend";
					summaryChartnDatablocks(summeryData);
					// console.log(111111)
					// scenarioDetails.spendDetails = scenarioDetails.spendDetails.sort(function (a, b) {
					// 	return b.node_data.Total - a.node_data.Total;
					// });
					ScenarioTree = new MMOTree({
						//tableNode: {'id': "table#geolevel_Tbltree", 'class': "simple-tree-table"},
						treeHeadNode: '.treeDataHeader',
						treeBodyNode: '.treeDatabody',
						headerStructure: HEADER_STRUCTURE,
						formatCellData: formatCellData,
						changeHandler: updateField,
						planner: true
						//getCustomFieldValue: getCustomFieldValue;
					});
					ScenarioTree.refreshTable(scenarioDetails.spendDetails, periodType, 'current');
					ScenarioTree.refreshTable(scenarioDetails.spendDetails, periodType, 'new');

					setDeltaValues();
					// hide the loader
					MMOUtils.hideLoader();
				}
			}
		},
		error: function (error) {
			MMOUtils.hideLoader();
		}
	});
}


function saveScenario() {
	MMOUtils.showLoader();
	var savescenarioFormdata = {};
	var scenariosubmitfrmData = $("#levelip_form").serializeArray();
	var curntScenarioText = $("#selectScenario option:selected").text();
	savescenarioFormdata["current_scenario_name"] = curntScenarioText;
	$.map(scenariosubmitfrmData, function (d) {
		d.name.indexOf("new") > 0 == true || d.name == "scenarioName" ? savescenarioFormdata[d.name] = d.value : "";
	});

	var same_scenario_name_repeat = false;

	$("#selectScenario > option").each(function () {
		var scenario_name = $('#savescnrip').val()
		if ($(this).text().toLowerCase().trim() === scenario_name.toLowerCase().trim()) {
			same_scenario_name_repeat = true;
			MMOUtils.hideLoader();
		}
	});

	if (same_scenario_name_repeat) {
		$('#scenarioPlannerModal').modal('show');
		$('#status_message').text('The scenario name already exists.Please change the name and save again.');
	} else {
		var period_type = $("#whatif_Level").val();
		savescenarioFormdata["period_type"] = period_type
		$.ajax({
			type: "POST",
			contentType: "application/json; charset=utf-8",
			url: "/userscenario/1",
			data: JSON.stringify(savescenarioFormdata),
			success: function (saveresp) {
				var scenariosListdata = saveresp.scenario_list;
				var current_scenario = $("#selectScenario").val();
				MMOUtils.buildDDlFromList("#selectScenario", scenariosListdata);
				$("#selectScenario").selectpicker("refresh");
				$("#selectScenario").val(current_scenario);
				$('#savescnrip').val("")
				$(".preloader").hide();
				$("#flashTxt").show().fadeOut(1500, function () { });
				location.reload(true);
				MMOUtils.hideLoader();
			},
			error: function (error) {
				MMOUtils.hideLoader();
			},
			dataType: "json"
		});
	}
	// MMOUtils.hideLoader();

}

summaryChartnDatablocks = function (summeryData) {

	$(".analysissummeryBox").html("");

	var curntScenarioText = $("#selectScenario option:selected").text();
	var curntspendval = summeryData[0]['Current Value'];
	scnriospendval = summeryData[1]['Current Value'];
	//change the below name if the default year is changed
	var scenarioTxt = curntScenarioText.length == 0 ? "Actuals 2020" : curntScenarioText;
	var SpendChange = d3.format("$,s")(scnriospendval == 0 ? 0 : (scnriospendval - curntspendval))
	var changeinpercent = MMOUtils.round(MMOUtils.percentCal(curntspendval, scnriospendval), 1);

	var htmlTemplate = '';

	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">Change in Spend</div></div><div class="stat-desc"><div id="progressstacked">' + progressStackedBars + '</div></div></div>';
	//	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t500 text-normal">'+summeryData[0]['name']+' Spend</div></div><div class="stat-desc center"><div class="row"><div class="col-12"><h2 id="curntspnd" class="green spendTxt">' + d3.formatPrefix("$.1",MMOUtils.round(curntspendval, 0))(MMOUtils.round(curntspendval, 0)) + '</h2> <input type="hidden" name="curntspend" id="Hiddn_curntspnd" value=""></div></div></div></div>';
	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">' + scenarioTxt + ' Spend</div></div><div class="stat-desc"><div class="row"><div class="col-12"><h2 id="scnriospnd" class="green spendTxt">' + d3.formatPrefix("$.1", MMOUtils.round(curntspendval, 0))(MMOUtils.round(curntspendval, 0)) + '</h2> <input type="hidden" name="scenriospend" id="Hiddn_scnriospnd" value=""></div></div></div></div>';
	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">Scenario Spend</div></div><div class="stat-desc"><div class="row"><div class="col-12"><h2 id="calculated_spend" class="green spendTxt">' + d3.formatPrefix("$.1", MMOUtils.round(scnriospendval, 0))(MMOUtils.round(scnriospendval, 0)) + '</h2> <input type="hidden" name="scenriospend" id="Hiddn_scnriospnd" value=""></div></div></div></div>';
	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">% Change in Spend</div></div><div class="stat-desc"><div class="row"><div class="col-12"><h2 id="chnginspnd" class="blue spendTxt black">' + "0" + '</h2> <input type="hidden" name="changinspend" id="Hiddn_chnginspnd" value=""></div></div></div></div>';

	$(".analysissummeryBox").append(htmlTemplate);

	summeryData[1]["ChangeType"] = Math.sign(scnriospendval - curntspendval)
	summeryData[1]["Change"] = scnriospendval == 0 ? 0 : Math.abs(scnriospendval - curntspendval);
	var progressStackedBars = progressStackedgraphGenerate(summeryData);

};
summaryChartnDatablocks1 = function (summeryData, summary, calculated_new_spend) {

	$(".analysissummeryBox").html("");

	var curntScenarioText = $("#selectScenario option:selected").text();
	var curntspendval = summeryData[0]['Current Value'];
	scnriospendval = summeryData[1]['Current Value'];
	//change the below name if the default year is changed
	var scenarioTxt = curntScenarioText.length == 0 ? "Actuals 2020" : curntScenarioText;
	var SpendChange = d3.format("$,s")(scnriospendval == 0 ? 0 : (scnriospendval - curntspendval))
	var changeinpercent = MMOUtils.round(MMOUtils.percentCal(curntspendval, scnriospendval), 1);

	var htmlTemplate = '';

	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">Change in Spend</div></div><div class="stat-desc"><div id="progressstacked">' + progressStackedBars + '</div></div></div>';
	//	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t500 text-normal">'+summeryData[0]['name']+' Spend</div></div><div class="stat-desc center"><div class="row"><div class="col-12"><h2 id="curntspnd" class="green spendTxt">' + d3.formatPrefix("$.1",MMOUtils.round(curntspendval, 0))(MMOUtils.round(curntspendval, 0)) + '</h2> <input type="hidden" name="curntspend" id="Hiddn_curntspnd" value=""></div></div></div></div>';
	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">' + scenarioTxt + ' Spend</div></div><div class="stat-desc"><div class="row"><div class="col-12"><h2 id="scnriospnd" class="green spendTxt">' + d3.formatPrefix("$.1", MMOUtils.round(summary, 0))(MMOUtils.round(summary, 0)) + '</h2> <input type="hidden" name="scenriospend" id="Hiddn_scnriospnd" value=""></div></div></div></div>';
	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">Scenario Spend</div></div><div class="stat-desc"><div class="row"><div class="col-12"><h2 id="calculated_spend" class="green spendTxt">' + d3.formatPrefix("$.1", MMOUtils.round(scnriospendval, 0))(MMOUtils.round(scnriospendval, 0)) + '</h2> <input type="hidden" name="scenriospend" id="Hiddn_scnriospnd" value=""></div></div></div></div>';
	htmlTemplate += '<div class="card stat-data"><div class="stat-heading"><div class="t800 text-normal">% Change in Spend</div></div><div class="stat-desc"><div class="row"><div class="col-12"><h2 id="chnginspnd" class="blue spendTxt">' + "0" + '</h2> <input type="hidden" name="changinspend" id="Hiddn_chnginspnd" value=""></div></div></div></div>';

	$(".analysissummeryBox").append(htmlTemplate);

	summeryData[1]["ChangeType"] = Math.sign(scnriospendval - curntspendval)
	summeryData[1]["Change"] = scnriospendval == 0 ? 0 : Math.abs(scnriospendval - curntspendval);
	var progressStackedBars = progressStackedgraphGenerate(summeryData);

};

var uploadButton = $(".browseBtn");
var fileInfo = $(".fileInfo");
var fileInput = $("#importScenario");

uploadButton.on("click", (e) => {
	e.preventDefault();
	fileInput.click();
});



fileInput.on("change", () => {
	var filename = fileInput.val().split(/(\\|\/)/g).pop();
	var truncated = filename.length > 50 ? filename.substr(filename.length - 50) : filename;
	fileInfo.html(truncated);
});

$("#import").on("click", function (e) {
	e.preventDefault();
	$(".preloader").show();
	var formData = new FormData();
	var file = $('#importScenario')[0].files[0];
	var currentipfieldName = file.name;
	var currentdynamicVal = this.value;
	var period_type = $("#whatif_Level").val();
	var currentID = this.id;
	var curntscenarioId = $("#selectScenario").val();
	var changeObj = {};
	changeObj[currentipfieldName] = currentdynamicVal;
	changeObj.scenario_id = curntscenarioId;
	formData.append('file', file);
	formData.append('scenario_id', curntscenarioId);
	formData.append('period_type', period_type)
	$.ajax({
		url: "/importSpendScenario",
		type: "POST",
		data: formData,
		processData: false,
		contentType: false,
		dataType: "json",
		success: function (data) {
			if (data && data.error) {
				$(".preloader").hide();
				$('#scenarioPlannerModal').modal('show');
				$('#status_message').text(data.error);
			} else {
				if (period_type == "weekly") {
					sum = data.sum
					data = data.output
				}
				var slectscenariSpend = d3.sum(data, function (d) { return d.node_data.Total });
				var curntScenarioText = currentipfieldName;

				summeryData[1]["Current Value"] = slectscenariSpend
				summeryData[1]["Change"] = slectscenariSpend;
				summeryData[1]["name"] = 'Scenario Spend';
				summaryChartnDatablocks(summeryData);

				ScenarioTree.refreshTable(data, period_type, 'new');

				setDeltaValues();
				var nodeIds = [...new Set(ScenarioTree.getAllNodeIds())];
				var calculated_new_spend = 0;
				var node_id = '';
				var change_in_spend_percent = 0
				$.each(nodeIds, function (index, value) {
					if (period_type == "yearly") {
						node_id = 'row_' + value + '_Year_new';
						calculated_new_spend += +ScenarioTree.getCellData(node_id);
					}
					else if (period_type == "qtrly") {
						for (let i = 0; i < quarters.length; i++) {
							node_id = 'row_' + value + '_' + quarters[i] + '_new';
							calculated_new_spend += +ScenarioTree.getCellData(node_id);
						}
					}
					else if (period_type == "monthly") {
						for (let i = 0; i < months.length; i++) {
							node_id = 'row_' + value + '_' + months[i] + '_new';
							calculated_new_spend += +ScenarioTree.getCellData(node_id);
						}
					}
				})
				if (period_type == "weekly") {
					calculated_new_spend += sum
				}
				var curntspendval1 = summeryData[0]['Current Value'];
				var rounded_change_in_spend = ((calculated_new_spend - curntspendval1) / curntspendval1) * 100;
				change_in_spend_percent = rounded_change_in_spend.toFixed(2)
				$('#calculated_spend').text(d3.formatPrefix("$.1", MMOUtils.round(calculated_new_spend, 0))(MMOUtils.round(calculated_new_spend, 0)))
				$('#chnginspnd').text(change_in_spend_percent);

				$(".preloader").hide();
			}
		},
		error: function (xhr, status, error) {
			if (xhr.status === 400) {
				$(".preloader").hide();
				$("#plannererrorLabel").text("Error");
				$(".modal-header").addClass("btn-danger").removeClass("btn-success");
				$(".modal-body").text("Invalid request. please check your file and try again");
				return $("#plannererror").modal('show');
			}
		}
	});
});



function progressStackedgraphGenerate(summeryData) {

	return c3.generate({
		bindto: '#progressstacked',
		data: {
			json: summeryData,
			keys: {
				x: "name",
				value: ["Current Value"]
			},
			groups: [
				["Current Value"]
			],
			order: null,
			type: 'bar',
			labels: {
				format: function (v, id, i, j) { return "$ " + d3.formatPrefix(".1", v)(v).replace(/G/, "B") }
			},
			color: function (inColor, data) {
				var colors = ['#9E9E9E', '#9E9E9E']
				if (data.index !== undefined) {
					return colors[data.index];
				}

				return inColor;
			}

		},
		size: {
			width: d3.max([$(".card.stat-data").width(), 254]),
			height: 50
		},
		bar: {
			width: 8,
			space: 0.25
		},
		axis: {
			rotated: true,
			x: {
				type: 'category',
				show: true,
				tick: {
					culling: false,
					outer: false
				}
			},
			y: {
				show: false,
			}
		},
		bar: {
			width: {
				ratio: 0.5
			}
		},
		legend: {
			show: false,
		},

		tooltip: {
			position: function () {
				return {
					right: 0,
					bottom: 0
				};
			},
			format: {
				value: function (data, i, j, k) {
					return d3.formatPrefix(".1", data)(data).replace(/G/, "B")
				}
			}
		}
	});
}
$("[data-hide]").on("click", function () {
	$('#plannererror').modal('hide');
});
