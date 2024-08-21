$(function () {
    timeperiod()
    MMOUtils.showLoader();
    periodselection();

    $("#outcome1").prop("checked", true);
    $("#outcome2").prop("checked", false);
});
$("body").on("change", "#tatics,#period", secondarymodules);
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
function periodselection() {
    MMOUtils.showLoader();
    $.ajax({
        url: "/get_period_secondary_contribution",
        type: 'GET',
        dataType: "json",
        success: function (response) {
            $("#period").html();
            $("#tatics").html();
            MMOUtils.buildDDlFromList("#period", response.years);
            MMOUtils.buildDDlFromList("#tatics", response.tactics);
            var firstYear = response.years;
            firstYear = Object.values(firstYear)[0]
            var firstatic = response.tactics;
            firstatic = Object.values(firstatic)[0]
            $("#period").find('option[value="' + firstYear + '"]').attr('selected', 'selected')
            $("#period").selectpicker("refresh");
            $("#tatics").find('option[value="0"]').attr('selected', 'selected')
            $("#tatics").selectpicker("refresh");
            MMOUtils.hideLoader();
            secondarymodules()
        },

        error: function (error) {
            MMOUtils.hideLoader();
        }
    })
}

$(".metricLink").click(function (e) {
    var outcome = $("input[name='metric']:checked").val();
    MMOUtils.showLoader();

    if (outcome == "outcome1") {
        $("#outcome1").prop("checked", true);
        $("#outcome2").prop("checked", false);
        secondarymodules()
        MMOUtils.showLoader();
    }
    else if (outcome == "outcome2") {
        $("#outcome2").prop("checked", true);
        $("#outcome1").prop("checked", false);
        secondarymodules()
        MMOUtils.showLoader();
    }

});

function secondarymodules() {
    MMOUtils.showLoader();
    var outcome = $("input[name='metric']:checked").val();
    var period = $("#period").val();
    var tatics = $("#tatics option:selected").text();

    var queryString = `outcome=${outcome}&period=${period}&tatics=${tatics}`;
    $.ajax({
        url: "/get_secondary_contribution?" + queryString,
        type: 'GET',
        dataType: "json",
        success: function (data) {

            // Create a chart
            var chart = c3.generate({
                bindto: '#chart',
                data: {
                    x: 'channel_tactic',
                    columns: [
                        data.categories,
                        data.values
                    ],
                    type: 'bar',
                    labels: {
                        format: function (v) { return v + "%"; }
                    }
                },
                axis: {
                    x: {
                        height: 100,
                        type: 'category',
                    },
                    y: {
                        show: true,
                        label: {
                            text: tatics,
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
                size: {
                    width: 1000,
                },
                legend: {
                    show: false
                },
                bar: {
                    width: {
                        ratio: 0.3
                    }
                },
                tooltip: {
                    format: {
                        value: function (data) { return data + '%' }
                    }
                },
                color: {
                    pattern: ['#9E9E9E']
                },
            });
            MMOUtils.hideLoader();
        },
        error: function (error) {
            MMOUtils.hideLoader();
        }
    })
}



