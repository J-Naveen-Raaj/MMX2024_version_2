summaryBox = function () {

    this.comparesummaryBlocks = function (scenariospendData, metric_type, metricLevelData, is_reverse) {
        $.each(scenariospendData, function (ak, av) {
            if (ak.indexOf('coutcome1') > -1) {
                metricLevelData["coutcome1"]["scenario1_spend"] = scenariospendData.s1_coutcome1;
                metricLevelData["coutcome1"]["scenario2_spend"] = scenariospendData.s2_coutcome1;
                metricLevelData["coutcome1"]["Delta-Change"] = MMOUtils.differenceCal(scenariospendData.s2_coutcome1, scenariospendData.s1_coutcome1);
                metricLevelData["coutcome1"]["Percentage-Change"] = MMOUtils.percentCalWithFixedDigit(scenariospendData.s1_coutcome1, scenariospendData.s2_coutcome1);
            }
            else if (ak.indexOf('coutcome2') > -1) {
                metricLevelData["coutcome2"]["scenario1_spend"] = scenariospendData.s1_coutcome2;
                metricLevelData["coutcome2"]["scenario2_spend"] = scenariospendData.s2_coutcome2;
                metricLevelData["coutcome2"]["Delta-Change"] = MMOUtils.differenceCal(scenariospendData.s2_coutcome2, scenariospendData.s1_coutcome2);
                metricLevelData["coutcome2"]["Percentage-Change"] = MMOUtils.percentCalWithFixedDigit(scenariospendData.s1_coutcome2, scenariospendData.s2_coutcome2);
            }
            else if (ak.indexOf('outcome1') > -1) {
                metricLevelData["outcome1"]["scenario1_spend"] = scenariospendData.s1_outcome1;
                metricLevelData["outcome1"]["scenario2_spend"] = scenariospendData.s2_outcome1;
                metricLevelData["outcome1"]["Delta-Change"] = MMOUtils.differenceCal(scenariospendData.s2_outcome1, scenariospendData.s1_outcome1);
                metricLevelData["outcome1"]["Percentage-Change"] = MMOUtils.percentCalWithFixedDigit(scenariospendData.s1_outcome1, scenariospendData.s2_outcome1);
            }
            else if (ak.indexOf('outcome2') > -1) {
                metricLevelData["outcome2"]["scenario1_spend"] = scenariospendData.s1_outcome2;
                metricLevelData["outcome2"]["scenario2_spend"] = scenariospendData.s2_outcome2;
                metricLevelData["outcome2"]["Delta-Change"] = MMOUtils.differenceCal(scenariospendData.s2_outcome2, scenariospendData.s1_outcome2);
                metricLevelData["outcome2"]["Percentage-Change"] = MMOUtils.percentCalWithFixedDigit(scenariospendData.s1_outcome2, scenariospendData.s2_outcome2);
            }
            else {
                metricLevelData["Overall-Change"]["scenario1_name"] = scenariospendData.s1_name;
                metricLevelData["Overall-Change"]["scenario2_name"] = scenariospendData.s2_name;
                metricLevelData["Overall-Change"]["scenario1_spend"] = scenariospendData.s1_spends;
                metricLevelData["Overall-Change"]["scenario2_spend"] = scenariospendData.s2_spends;
                metricLevelData["Overall-Change"]["Delta-Change"] = MMOUtils.differenceCal(scenariospendData.s2_spends, scenariospendData.s1_spends);
                metricLevelData["Overall-Change"]["Percentage-Change"] = MMOUtils.percentCalWithFixedDigit(scenariospendData.s1_spends, scenariospendData.s2_spends);
            }

        });

        var metricskeys = Object.keys(metricLevelData["Overall-Change"]);
        scenarioName1 = metricLevelData["Overall-Change"]["scenario1_name"];
        scenarioName2 = metricLevelData["Overall-Change"]["scenario2_name"];

        if (metric_type == "Overall-Change") {
            $("#SOCmetricTxtBox").hide();
            $("#SOCmetricTblBox").hide();
            //$("#Compare-metricTxtBox").hide();
            $("#comparesummaryHolder").empty();
            ScenariosummaryBox.blockgenerate(metricLevelData);
        } else if (metric_type == "outcome1") {
            $("#SOCmetricTxtBox").show();
            $("#SOCmetricTblBox").show();
            $("#comparesummaryHolder").empty();
            var selectedMetrics = {}
            selectedMetrics["Overall-Change"] = metricLevelData["Overall-Change"];
            selectedMetrics[metric_type] = metricLevelData[metric_type];
            selectedMetrics["coutcome1"] = metricLevelData["coutcome1"];
            ScenariosummaryBox.blockgenerate(selectedMetrics);
        }
        else {
            $("#SOCmetricTxtBox").show();
            $("#SOCmetricTblBox").show();
            $("#comparesummaryHolder").empty();
            var selectedMetrics = {}
            selectedMetrics["Overall-Change"] = metricLevelData["Overall-Change"];
            selectedMetrics[metric_type] = metricLevelData[metric_type];
            selectedMetrics["coutcome2"] = metricLevelData["coutcome2"];
            ScenariosummaryBox.blockgenerate(selectedMetrics);
        }

    }

    this.blockgenerate = function (metricLevelData) {
        $.each(metricLevelData, function (mk, mv) {
            sc1 = truncateString(scenarioName1, 10, '...')
            sc2 = truncateString(scenarioName2, 10, '... ')
            summaryData[0]["name"] = sc1;
            summaryData[0]["Current Value"] = metricLevelData[mk].scenario1_spend;
            summaryData[0]["Change"] = 0;
            summaryData[0]["ChangeType"] = "";
            summaryData[1]["name"] = sc2;
            summaryData[1]["Current Value"] = metricLevelData[mk].scenario2_spend;
            summaryData[1]["Change"] = Math.abs(metricLevelData[mk].scenario2_spend - metricLevelData[mk].scenario1_spend);
            summaryData[1]["ChangeType"] = Math.sign(metricLevelData[mk].scenario2_spend - metricLevelData[mk].scenario1_spend);
            var prefix = '$';
            var metricText;
            var deltaChangeVal;
            var scnrioone_Val;
            var scnriotwo_Val;


            if (mk == 'coutcome2') {
                metricText = "coutcome2";
                prefix = '';
                const deltaChange = MMOUtils.round(mv["Delta-Change"], 1);
                const minuteChangeThreshold = 0.1;
                if (Math.abs(deltaChange) < minuteChangeThreshold) {
                    deltaChangeVal = 0;
                } else {
                    const formattedDeltaChange = deltaChange.toFixed(1);

                    if (Math.abs(deltaChange) >= 1e9) {
                        deltaChangeVal = "$" + (formattedDeltaChange / 1e9).toFixed(2) + "B";
                    } else if (Math.abs(deltaChange) >= 1e6) {
                        deltaChangeVal = "$" + (formattedDeltaChange / 1e6).toFixed(2) + "M";
                    } else {
                        // Adjust the formatting for negative values
                        deltaChangeVal = (formattedDeltaChange < 0 ? "-$" : "$") + Math.abs(formattedDeltaChange);
                    }
                }
                $(".metricTxt").html(metricText);
                scnrioone_Val = MMOUtils.round(mv["scenario1_spend"], 0);
                scnriotwo_Val = MMOUtils.round(mv["scenario2_spend"], 0);
                change = d3.formatPrefix(".1", (scnriotwo_Val - scnrioone_Val))(scnriotwo_Val - scnrioone_Val).replace(/G/, "B")

            }
            else if (mk == 'outcome1') {
                metricText = "outcome1";
                deltaChangeVal = d3.formatPrefix(".1", mv["Delta-Change"])(mv["Delta-Change"]).replace(/G/, "B");
                $(".metricTxt").html(metricText);
                scnrioone_Val = MMOUtils.round(mv["scenario1_spend"], 0);
                scnriotwo_Val = MMOUtils.round(mv["scenario2_spend"], 0);
                change = d3.formatPrefix("$.1", (scnriotwo_Val - scnrioone_Val))(scnriotwo_Val - scnrioone_Val).replace(/G/, "B")

            } else if (mk == 'outcome2') {
                metricText = "outcome2";
                deltaChangeVal = d3.formatPrefix(".1", mv["Delta-Change"])(mv["Delta-Change"]).replace(/G/, "B");
                $(".metricTxt").html(metricText);
                scnrioone_Val = MMOUtils.round(mv["scenario1_spend"], 0);
                scnriotwo_Val = MMOUtils.round(mv["scenario2_spend"], 0);
                change = d3.formatPrefix("$.1", (scnriotwo_Val - scnrioone_Val))(scnriotwo_Val - scnrioone_Val).replace(/G/, "B")

            }
            else if (mk == 'coutcome1') {
                metricText = "coutcome1";
                const deltaChange = mv["Delta-Change"];
                const minuteChangeThreshold = 0.1;
                if (Math.abs(deltaChange) < minuteChangeThreshold) {
                    deltaChangeVal = 0;
                } else {
                    const formattedDeltaChange = deltaChange.toFixed(1);

                    if (Math.abs(deltaChange) >= 1e9) {
                        deltaChangeVal = "$" + (formattedDeltaChange / 1e9).toFixed(2) + "B";
                    } else if (Math.abs(deltaChange) >= 1e6) {
                        deltaChangeVal = "$" + (formattedDeltaChange / 1e6).toFixed(2) + "M";
                    } else {
                        // Adjust the formatting for negative values
                        deltaChangeVal = (formattedDeltaChange < 0 ? "-$" : "$") + Math.abs(formattedDeltaChange);
                    }
                }
                $(".metricTxt").html(metricText);
                scnrioone_Val = MMOUtils.round(mv["scenario1_spend"], 0);
                scnriotwo_Val = MMOUtils.round(mv["scenario2_spend"], 0);
                change = d3.formatPrefix("$.1", (scnriotwo_Val - scnrioone_Val))(scnriotwo_Val - scnrioone_Val).replace(/G/, "B")
            }
            else {
                metricText = "Spends";
                deltaChangeVal = d3.formatPrefix("$.1", mv["Delta-Change"])(mv["Delta-Change"]).replace(/G/, "B");
                $(".metricTxt").html(metricText);
                scnrioone_Val = MMOUtils.round(mv["scenario1_spend"], 0);
                scnriotwo_Val = MMOUtils.round(mv["scenario2_spend"], 0)
                change = d3.formatPrefix("$.1", (scnriotwo_Val - scnrioone_Val))(scnriotwo_Val - scnrioone_Val).replace(/G/, "B")
            }
            var percentageChange = MMOUtils.round(mv["Percentage-Change"], 0);
            var classToAdd = percentageChange > 0 ? 'positive' : percentageChange < 0 ? 'red' : 'black';
            var classToAddcpa = percentageChange < 0 ? 'positive' : percentageChange > 0 ? 'red' : 'black';
            var changeclass = mv["Delta-Change"] > 0 ? 'positive' : mv["Delta-Change"] < 0 ? 'red' : 'black';
            var changeclasscpa = mv["Delta-Change"] < 0 ? 'positive' : mv["Delta-Change"] > 0 ? 'red' : 'black';
            var htmlTemplate = '';
            if (metricText == "Spends") {
                htmlTemplate += '<div class="col-12 pl-0">'
                htmlTemplate += '<div class="col-6 summary-block-border-left" id="' + mk + '_block"><div class="row">';
                htmlTemplate += '<div class="col-6 comparison-data-block summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1"><div class="t800 text-normal">Change in ' + metricText + '</div></div><div class="stat-desc pl-1 chartBox"><div class="" id="progressBox_' + mk + '">' + progressStackedBars + '</div></div></div></div>';
                htmlTemplate += '<div class="col summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t800 text-normal">Change in ' + metricText + '</div></div><div class="px-0"><div class="row"><div class="col-12"><h2 class="green spendTxt grey ">' + deltaChangeVal + '</h2></div></div></div></div></div>';
                htmlTemplate += '<div class="col"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t800 text-normal">% Change in ' + metricText + '</div></div><div class=""><div class="row"><div class="col-12"><h2 class="blue spendTxt OAChangeinspndpercent grey ">' + percentageChange + '% </h2></div></div></div></div></div>';
                htmlTemplate += '</div></div></div>';
            }
            else if ((metricText == "outcome2") || (metricText == "outcome1")) {
                htmlTemplate += '<div class="col-6 pl-0">'
                htmlTemplate += '<div class="col summary-block-border-left" id="' + mk + '_block"><div class="row">';
                htmlTemplate += '<div class="col comparison-data-block summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1"><div class="t800 text-normal">Change in ' + metricText + '</div></div><div class="stat-desc pl-1 chartBox"><div class="" id="progressBox_' + mk + '">' + progressStackedBars + '</div></div></div></div>';
                htmlTemplate += '<div class="col summary-block-border-right m-l-5"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t800 text-normal">Change in ' + metricText + '</div></div><div class="px-0"><div class="row"><div class="col-12"><h2 class="green spendTxt black ' + changeclass + '">' + deltaChangeVal + '</h2></div></div></div></div></div>';
                htmlTemplate += '<div class="col"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t800 text-normal">% Change in ' + metricText + '</div></div><div class=""><div class="row"><div class="col-12"><h2 class="blue spendTxt OAChangeinspndpercent black ' + classToAdd + '">' + percentageChange + '% </h2></div></div></div></div></div>';
                htmlTemplate += '</div></div></div>';
            }
            else {
                htmlTemplate += '<div class="col-6 pl-0">'
                htmlTemplate += '<div class="col summary-block-border-left" id="' + mk + '_block"><div class="row">';
                htmlTemplate += '<div class="col comparison-data-block summary-block-border-right"><div class="card stat-data"><div class="stat-heading pt-1"><div class="t800 text-normal">Change in ' + metricText + '</div></div><div class="stat-desc pl-1 chartBox"><div class="" id="progressBox_' + mk + '">' + progressStackedBars + '</div></div></div></div>';
                htmlTemplate += '<div class="col summary-block-border-right m-l-5"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t800 text-normal">Change in ' + metricText + '</div></div><div class="px-0"><div class="row"><div class="col-12"><h2 class="green spendTxt black ' + changeclasscpa + '">' + deltaChangeVal + '</h2></div></div></div></div></div>';
                htmlTemplate += '<div class="col"><div class="card stat-data"><div class="stat-heading pt-1 px-0"><div class="t800 text-normal">% Change in ' + metricText + '</div></div><div class=""><div class="row"><div class="col-12"><h2 class="blue spendTxt OAChangeinspndpercent black ' + classToAddcpa + '">' + percentageChange + '% </h2></div></div></div></div></div>';
                htmlTemplate += '</div></div></div>';
            }

            $("#comparesummaryHolder").append(htmlTemplate);
            var tooltipdata = [];

            tooltipdata.push(scenarioName1);
            tooltipdata.push(scenarioName2);
            var progressStackedBars = ScenariosummaryBox.progressStackedgraphGenerate(summaryData, mk, scenarioName1, scenarioName2, metricText, tooltipdata);
        });
    };
    function truncateString(inputString, maxLength, ellip = '...') {
        if (inputString.length > maxLength) {
            return inputString.substring(0, maxLength) + ellip;
        } else {
            return inputString;
        }
    }
    this.progressStackedgraphGenerate = function (summaryData, appendTo, scenario1, scenario2, metricText, tooltipdata) {
        var cntrwidth = d3.max([$(".chartBox").width(), 254]);

        return c3.generate({
            bindto: "#progressBox_" + appendTo,
            data: {
                json: summaryData,
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
                    format: function (v, id, i, j) {
                        if ((metricText == "Spends") || (metricText == "coutcome1") || (metricText == "coutcome2")) { return "$ " + d3.formatPrefix(".1", v)(v).replace(/G/, "B") }
                        else {
                            return d3.formatPrefix(".1", v)(v).replace(/G/, "B")
                        }
                    }
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
                width: cntrwidth,
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
            // color: {
            //pattern: ['#aec7e8', '#1f77b4']
            //    pattern:['#1f77b4','#8BC53F']

            //},

            tooltip: {
                position: function () {
                    return {
                        right: 0,
                        bottom: 0
                    };
                },
                format: {
                    value: function (data, i, j, k) {
                        return d3.formatPrefix(".1", data)(data).replace(/G/, "B");
                    }
                },
                contents: function (data, defaultTitleFormat, defaultValueFormat, color) {
                    var title = tooltipdata[data[0].index]; // Assuming data[0] contains the index
                    var tooltipContent = '<div class="c3-tooltip-container">';
                    tooltipContent += '<table class="c3-tooltip">';
                    tooltipContent += '<tbody>';
                    tooltipContent += '<tr><th colspan="2">' + title + '</th></tr>';
                    tooltipContent += '<tr class="c3-tooltip-name--Current-Value">';
                    tooltipContent += '<td class="name"><span style="background-color:' + color(data[0].id) + '"></span>Current Value</td>';
                    tooltipContent += '<td class="value">' + d3.formatPrefix(".1", data[0].value)(data[0].value).replace(/G/, "B") + '</td>';
                    tooltipContent += '</tr>';
                    tooltipContent += '</tbody>';
                    tooltipContent += '</table></div>';
                    return tooltipContent;
                }
            }

        });
    }
};