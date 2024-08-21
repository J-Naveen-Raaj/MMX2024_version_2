// Reusable tree class
MMOTree = function (config) {
	// nodes where tree should be rendered
	this.tableNode = config.tableNode;
	this.treeHeadNode = config.treeHeadNode;
	this.treeBodyNode = config.treeBodyNode;
	this.headerStructure = config.headerStructure;
	this.formatCellData = config.formatCellData;
	this.rowTitleClick = config.rowTitleClick
	this.changeHandler = config.changeHandler;
	var isEqual = function (value, other) {

		// Get the value type
		var type = Object.prototype.toString.call(value);

		// If the two objects are not the same type, return false
		if (type !== Object.prototype.toString.call(other)) return false;

		// If items are not an object or array, return false
		if (['[object Array]', '[object Object]'].indexOf(type) < 0) return false;

		// Compare the length of the length of the two items
		var valueLen = type === '[object Array]' ? value.length : Object.keys(value).length;
		var otherLen = type === '[object Array]' ? other.length : Object.keys(other).length;
		if (valueLen !== otherLen) return false;

		// Compare two items
		var compare = function (item1, item2) {

			// Get the object type
			var itemType = Object.prototype.toString.call(item1);

			// If an object or array, compare recursively
			if (['[object Array]', '[object Object]'].indexOf(itemType) >= 0) {
				if (!isEqual(item1, item2)) return false;
			}

			// Otherwise, do a simple comparison
			else {

				// If the two items are not the same type, return false
				if (itemType !== Object.prototype.toString.call(item2)) return false;

				// Else if it's a function, convert to a string and compare
				// Otherwise, just compare
				if (itemType === '[object Function]') {
					if (item1.toString() !== item2.toString()) return false;
				} else {
					if (item1 !== item2) return false;
				}

			}
		};

		// Compare properties
		if (type === '[object Array]') {
			for (var i = 0; i < valueLen; i++) {
				if (compare(value[i], other[i]) === false) return false;
			}
		} else {
			for (var key in value) {
				if (value.hasOwnProperty(key)) {
					if (compare(value[key], other[key]) === false) return false;
				}
			}
		}

		// If nothing failed, return true
		return true;

	};
	//this.getCustomFieldValue = config.getCustomFieldValue;

	// internal to the tree functioning
	//this.currentHeader = '';
	this.cellData = {};
	this.rowCount = 0;
	this.currentHeaders = null;
	this.allNodeIds = [];
	this.rootNodes = [];

	this.resetTree = function () {
		$(this.treeHeadNode).html('');
		$(this.treeBodyNode).html('');
		this.cellData = {};
		this.rowCount = 0;
		this.currentHeaders = null;
		this.allNodeIds = [];
		this.rootNodes = [];
	};

	this.refreshTable = function (data, headerKey, subHeaderNeeded) {
		var headers;

		if (headerKey == this.headerKey) {
			// only refresh the data, no need to update the tree itself
			headers = this.headerStructure[headerKey];

			if (isEqual(this.currentHeaders, headers)) {
				this.populateData(data, subHeaderNeeded);
			}
			else {
				if (this.headerStructure) {
					this.headerKey = headerKey;
					headers = this.headerStructure[headerKey];
					this.currentHeaders = headers;
					this.regenerateHead();
				}

				// then populate the data
				if (data) {
					this.regenerateBody(data, headers);
				}
				// TODO this id needs to be parameterized
				if (this.tableNode) {
					$(this.tableNode.id).data("simple-tree-table").init();
				}
				else {
					$("table#geolevel_Tbltree").data("simple-tree-table").init();
				}

				// then populate the data
				this.populateData(data, subHeaderNeeded);
			}


		}
		else {
			// first build the tree
			if (this.headerStructure) {
				this.headerKey = headerKey;
				headers = this.headerStructure[headerKey];
				this.currentHeaders = headers;
				this.regenerateHead();
			}

			// then populate the data
			if (data) {
				this.regenerateBody(data, headers);
			}
			if (this.tableNode) {
				$(this.tableNode.id).data("simple-tree-table").init();
			}
			else {
				$("table#geolevel_Tbltree").data("simple-tree-table").init();
			}

			// then populate the data
			this.populateData(data, subHeaderNeeded);
		}

		if (this.tableNode) {
			$(this.tableNode.id).tableHeadFixer({ "left": 0 });
		}
		else {
			$("table#geolevel_Tbltree").tableHeadFixer({ "left": 0 });
		}


	};

	this.regenerateHead = function () {
		var headers = this.currentHeaders;
		if (!headers) return;

		$(this.treeHeadNode).html('');

		// to determine colspans and alignments
		var subHeaderCnt;
		// for the main headers
		var htmlTemplate = '<tr><td align="center" class="top-level-heading bl">Marketing Tactics</td>';
		if (config.planner) {
			htmlTemplate = '<tr><td align="center" class="top-level-heading bl">Channel</td>';
			htmlTemplate += '<td align="center" class="top-level-heading bl" style="width:33%">Marketing Tactics</td>';
		}
		$.map(headers, function (header) {
			subHeaderCnt = header.subheaders.length;
			htmlTemplate += '<td colspan="' + subHeaderCnt + '" align="center" class="top-level-heading bl">' + header.title + '</td>';
		});
		htmlTemplate += '</tr>';
		$(this.treeHeadNode).append(htmlTemplate);

		// for the sub-headers
		htmlTemplate = '<tr><td>&nbsp;</td>';
		if (config.planner) {
			htmlTemplate = '<tr style="border-bottom:1px solid black"><td> </td><td> </td>';
		}
		$.map(headers, function (header) {
			subHeaderCnt = header.subheaders.length;
			$.map(header.subheaders, function (subHeader) {
				htmlTemplate += '<td class="second-level-heading bl" style="border-bottom:1px solid black">' + subHeader.title + '</td>';
			});
		});
		htmlTemplate += '</tr>';

		$(this.treeHeadNode).append(htmlTemplate);
	};

	this.regenerateBody = function (data, headers) {
		var me = this;

		// the size of the grid is determined by the data when it's generated
		this.rowCount = data.length;

		// clear the HTML so we can append the new markup
		$(this.treeBodyNode).html('');

		var htmlTemplate = '';
		var rowData = [];
		//var cellData;

		// data is for row and header is for column
		// for each row
		$.each(data, function (i, el) {
			var open_close_class = ''
			if (config.comparision) {
				if (el.node_parent == 0) {
					open_close_class = 'tree-opened'
				}

				else if (el.node_name) {
					open_close_class = 'tree-empty'
				}

				else {
					open_close_class = 'tree-closed'
				}
			}
			if (el.node_parent == 0) {
				me.rootNodes.push(el.node_id);
			}
			me.allNodeIds.push(el.node_id);

			htmlTemplate += '<tr data-node-id="' + el.node_id + '" data-node-pid="' + el.node_parent + '" class="' + open_close_class + '">';
			if (config.planner) {
				htmlTemplate += '<td class="">' + el.node_category + '</td>';
			}
			htmlTemplate += '<td class="">' + el.node_disp_name + '</td>';


			// for each of the headers, loop through the sub-headers to build the grid
			if (headers) {
				$.each(headers, function (j, header) {
					headerKey = header.key;
					htmlTemplate += me.getRowSection(el.node_id, header.key, header.subheaders);
				});
			}
			htmlTemplate += '</tr>';
		});

		// append the html built above
		$(this.treeBodyNode).append(htmlTemplate);
	};

	this.getRowSection = function (nodeId, headerKey, subHeaders) {
		var me = this;
		var html = '';
		var editNonEdit = '';
		var value;

		$.each(subHeaders, function (idx, sh) {
			value = '';
			//idString = headerKey + "_" + MMOUtils.replaceHash(nodeRefName) + "_" + sh.key + "_" + nodeId;
			idString = me.getCellId(nodeId, headerKey, sh.key);
			if (sh.editable) {
				tdContent = '<input type="text"  class="form-control mx-0 text-right mb-0 spendDetailipBox  customipBox"'
					+ ' name="' + idString
					+ '" id="' + idString + '"'
					+ ' autocomplete="off"'
					//+ '" onchange="' +  + '()"'
					+ '/>';

				// add the listener as well
				$("body").on("change", "#" + idString, me.changeHandler);
			}
			else {
				tdContent = '<span class="text-right ' + idString
					+ '" id="' + idString + '">'
					+ value
					+ '</span>'
			}
			html += '<td class="p-1">' + tdContent + '</td>';
		});
		return html;
	};

	this.populateData = function (data, subHeaderNeeded) {
		var me = this;
		var headerKey;
		var subheader;
		var elementId;
		var rawValueObj;
		var rawValue;
		var value;
		var subheadersToPopulate;

		var headers = this.currentHeaders;

		$.each(data, function (i, el) {
			// for each of the headers, loop through to populate the values for sub-header selected
			$.each(headers, function (j, header) {
				headerKey = header.key
				rawValueObj = el.node_data ? el.node_data[headerKey] : el[headerKey];
				rawValue = rawValueObj ? rawValueObj.toString() : "0"

				if (subHeaderNeeded) {
					// find the subheader object
					subheader = me.findSubHeader(header, subHeaderNeeded);
					subheadersToPopulate = [subheader];
				}
				else {
					subheadersToPopulate = header.subheaders;
				}

				$.each(subheadersToPopulate, function (k, subheader) {
					// build the element ID and populate the element
					elementId = me.getCellId(el.node_id, headerKey, subheader.key);
					me.cellData[elementId] = rawValue;
					roundoff = subheader.roundoff ? subheader.roundoff : 0;
					title = subheader.title
					value = me.formatCellData(rawValue, roundoff, title, headerKey);

					// field if editable, html if not
					// update the value to the grid
					if (subheader.editable) {
						$("#" + elementId).val(value);
					}
					else {
						$("#" + elementId).html(value);
					}
				});
			});
		});
	};

	this.getCellId = function (rowNodeId, headerKey, subHeaderKey) {
		return 'row_' + rowNodeId + '_' + headerKey + '_' + subHeaderKey;
	};

	this.getFieldName = function (rowNodeId, headerKey, subHeaderKey, nodeId) {
		return 'row_' + rowNodeId + '_' + headerKey + '_' + subHeaderKey + '_' + nodeId;
	};

	this.findSubHeader = function (header, subHeaderKey) {
		var subheader = {};
		$.each(header.subheaders, function (j, sh) {
			if (sh.key == subHeaderKey) {
				subheader = sh;
			}
		});
		return subheader;
	}

	this.findHeader = function (headerKey) {
		var header = {};
		var headers = this.currentHeaders;

		$.each(headers, function (i, h) {
			if (h.key == headerKey) {
				header = h;
			}
		});

		return header;
	}

	this.getCellData = function (cellId) {
		return this.cellData[cellId];
	}

	this.setCellData = function (cellId, value) {
		this.cellData[cellId] = value;
	}

	this.updateCell = function (cellId, value) {
		// first update the value internally
		this.setCellData(cellId, value.toString());

		// get the formatted value by getting the header, sub-header
		var cellIdParts = cellId.split("_");
		value = this.formatCellData(value.toString(), cellIdParts[3]);

		// field if editable, html if not
		var subheader = this.findSubHeader(this.findHeader(cellIdParts[2]), cellIdParts[3]);
		if (subheader.editable) {
			$("#" + cellId).val(value);
		}
		else {
			$("#" + cellId).html(value);
		}
	}

	this.getRowCount = function () {
		return this.rowCount;
	}

	this.getHeaders = function () {
		return this.currentHeaders;
	}

	this.getAllNodeIds = function () {
		return this.allNodeIds;
	}

	this.getRootNodes = function () {
		return this.rootNodes;
	}
};