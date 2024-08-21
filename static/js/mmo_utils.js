MMOUtils = {
	// method to populate dropdowns dynamically
	buildDDlFromList: function (ddl, data) {
		var OpHtml = "<option value=''>Select</option>";
		$.each(data, function (i, v) {
			OpHtml += "<option value='" + i + "'>" + v + "</option>";
		});
		$(ddl).html(OpHtml);
	},

	// method to populate dropdowns dynamically
	buildDDlFromListWithNoSelect: function (ddl, data) {
		var OpHtml = "";
		$.each(data, function (i, v) {
			OpHtml += "<option value='" + i + "'>" + v + "</option>";
		});
		$(ddl).html(OpHtml);
	},

	hideLoader: function () {
		$(".preloader").hide();
	},

	showLoader: function () {
		$(".preloader").show();
	},

	replaceComma: function (str) {
		return str.replace(/,/gi, '');
	},

	replaceSpace: function (str) {
		return str.replace(/ /gi, '');
	},

	replaceUnderscore: function (str) {
		return str.replace(/_/gi, ' ');
	},

	replaceIphen: function (str) {
		return str.replace(/-/gi, ' ');
	},

	replaceHash: function (str) {
		return str.replace(/#/gi, '');
	},
	replaceemptywithNull: function (str) {
		return str.replace(/""/gi, null);
	},
	replacepercentileword: function (str) {
		return str.replace(/Percntile/gi, '%');
	},

	round: function (value, decimals) {
		return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
	},
	percentCal: function (oneval, twoval) {
		return ((twoval - oneval) / oneval * 100).toFixed(0);
	},
	percentCalWithFixedDigit: function (oneval, twoval) {
		if (oneval == 0) {
			var oneval1 = 1
			return ((twoval - oneval) / oneval1 * 100).toFixed(1);
		}
		return ((twoval - oneval) / oneval * 100).toFixed(1);
	},
	differenceCal: function (num1, num2) {
		return num1 - num2;
	},
	commaSeparatevalue: function (val) {
		while (/(\d+)(\d{3})/.test(val.toString())) {
			val = val.toString().replace(/(\d+)(\d{3})/, '$1' + ',' + '$2');
		}
		return val;
	},
	differenceCal: function (num1, num2) {
		return num1 - num2;
	},
	commaSeparateNumberwithK: function (val) {
		if (val !== 0) {
			val = MMOUtils.round(val / 1000, 0);
		}
		while (/(\d+)(\d{3})/.test(val.toString())) {
			val = val.toString().replace(/(\d+)(\d{3})/, '$1' + ',' + '$2');
		}
		return val + "M";
	},
	dollarFormatterwithB: function (n) {
		n = Math.round(n);
		var result = n;
		return '$ ' + d3.format(",")(result) + ' B';
	},
	wrap: function wrap(text, width) {
		// alert('wrap');
		text.each(function () {
			var text = d3.select(this),
				words = text.text().split(/\s+/).reverse(),
				word,
				line = [],
				lineNumber = 0,
				lineHeight = 1.1, // ems
				y = text.attr("y"),
				dy = parseFloat(text.attr("dy")),
				tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
			while (word = words.pop()) {
				line.push(word);
				tspan.text(line.join(" "));
				if (tspan.node().getComputedTextLength() > width) {
					line.pop();
					tspan.text(line.join(" "));
					line = [word];
					tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
				}
			}
		});
	}
};