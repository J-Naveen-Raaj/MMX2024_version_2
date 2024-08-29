# coding=utf-8
import ast
import io
import json
import pdb
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from io import BytesIO
from sched import scheduler

import numpy as np
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import jsonify, make_response, request, send_from_directory
from flask_login import current_user
from pandas import ExcelWriter

from app_server import database_handler
from app_server.common_utils_handler import UtilsHandler
from app_server.custom_logger import get_logger
from app_server.maintenance_handler import MaintenanceHandler
from app_server.optimization_dao import OptimizationDAO
from app_server.optimization_handler import OptimizationHandler
from app_server.reporting_handler import ReportingHandler
from app_server.scenario_comparison_handler import ScenarioComparisonHandler
from app_server.scenario_handler import ScenarioHandler
from config import (APP_LOG_FILES_DIR, OP_INPUT_FILES_DIR, OP_LOG_FILES_DIR,
                    OP_OUTPUT_FILES_DIR)

logger = get_logger(__name__)
executor = ThreadPoolExecutor()

text_csv = "text/csv"
XLSX_FORMAT = ".xlsx"
ATTACHMENT_FILENAME = "attachment; filename="

def default(o):
    if isinstance(o, np.int64):
        return int(o)
    raise TypeError


def getScenarioList():
    """
    Method to scenario list
    Returns
    -------

    """
    results = ScenarioHandler().fetch_scenario_list_from_outcome()
    scenarios = dict([(x["scenario_id"], x["scenario_name"]) for x in results])
    return jsonify(scenarios)


def UserScenario(user_id):
    """
    Get user scenario
    Parameters
    ----------
    user_id

    Returns
    -------

    """
    if request.method == "GET":
        logger.debug("In get user scenario")
        request_data = request.args or {}
        scenario_name = request_data.get("scenario_name")
        period_type = request_data.get("period_type")
        results = ScenarioHandler().get_initial_user_scenario(
            user_id, scenario_name, period_type
        )
        if (scenario_name == "null") or (scenario_name == ""):
            results["message"] = "Invalid scenario"
            return jsonify(results)
        return jsonify(results)

    if request.method == "POST":
        logger.debug("Save Scenario and Run Whatif")
        request_data = request.get_json()
        results = ScenarioHandler().save_new_scenario(user_id, request_data)
        return jsonify(results)


def ChangeScenario():
    """
    Compute Delta if there is change in scenario spend
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ScenarioHandler().compute_delta(request_data)
    # pdb.set_trace()
    return json.dumps(results, default=default)


def importSpendScenario():
    """
    get import spend scenario and compute delta
    Returns
    -------

    """
    imported_data = request.files["file"]
    if allowed_file(imported_data.filename):
        scenario_id = request.form["scenario_id"] or 1
        period_type = request.form["period_type"]
        results = ScenarioHandler().compute_delta_for_imported_scenario(
            imported_data, period_type, scenario_id
        )
        return jsonify(results)
    else:
        return jsonify({"error": "Invalid file type"}), 400


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"csv"}


def getReportingAllocations():
    """
    Get reporting allocation data for a scenario
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ReportingHandler().fetch_reporting_allocations(request_data)
    return jsonify(results)


def getReportingAllocationsYear():
    """
    Get year drop down data for a Reporting Allocation Actuals
    Returns
    -------

    """
    results = ReportingHandler().fetch_yearlist_from_reporting()
    results = dict([(x["year"], x["year"]) for x in results])
    return jsonify(results)


def getReportingAllocationsSOC():
    """
    Get year drop down data for a Reporting Allocation Actuals
    Returns
    -------

    """
    results = ReportingHandler().fetch_yearlist_from_reporting()
    results = dict([(x["scenario_id"], x["year"]) for x in results])
    return jsonify(results)


def getReportingAllocationGraph():
    """ """
    request_data = request.args.to_dict()
    results = ReportingHandler().fetch_reporting_allocation_graph(request_data)
    return jsonify(results)


def getSpendAllocationsSummary():
    """
    Get Allocation Spend summary for a scenario
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ReportingHandler().fetch_spend_allocation_summary(request_data)
    return jsonify(results)


def getScenarioComarisonByNode():
    nodes = parse_nodes(request.args.get("nodes", ""))

    # Prepare data for processing
    request_data = request.args.to_dict()
    request_data["nodes"] = nodes
    results = ScenarioComparisonHandler().get_scenario_comp_graph(request_data)
    return jsonify(results)


def getSpendComparisonSummary():
    """
    Get Spend summary for a scenarios
    Returns
    -------

    """
    request_data = request.args.to_dict()
    required_fields = ["scenario_1", "scenario_2"]
    if any(request_data[field] == "" for field in required_fields):
        logger.error("One or more required fields are empty.")
        return jsonify({"error": "Required fields are empty"}), 400
    else:
        results = ScenarioComparisonHandler().fetch_spend_comparison_summary(
            request_data
        )
        return jsonify(results)


def getMediaHierarchyList():
    """
    Get Media hierarchy list
    Returns
    -------

    """
    if request.method == "GET":
        results = ReportingHandler().fetch_media_hierarchy()
        return jsonify(results)
    if request.method == "POST":
        request_data = request.get_json()
        results = ReportingHandler().fetch_media_hierarchy_level(request_data)
        return results



def downloadScenarioPlanningReport():
    """
    Download the spends for selected scenario planner
    Returns
    -------

    """
    request_data = request.args
    scenario_id = request_data["scenario_id"]
    period_type = request_data["period_type"]

    result = ScenarioHandler().downloadScenarioPlanningReport(scenario_id, period_type)
    resp = make_response(result.to_csv(encoding="utf-8", index=False))
    resp.headers["Content-Disposition"] = (
        "attachment; filename=scenario_data_" + request_data["period_type"] + ".csv"
    )
    resp.headers["Content-Type"] = text_csv
    return resp


def DownloadScenarioComparisons():
    """
    Download the scenario comparison data
    Returns
    -------

    """
    request_data = request.args
    download_type = request_data.get("download_type")
    result = ScenarioComparisonHandler().download_data(request_data)
    return generate_excel_or_csv_file(
        download_type,
        result,
        "download_scenario_comparisons.csv",
        "download_scenario_comparisons.xlsx",
        "",
        "",
        "fileDownload=true; path=/",
    )


def DownloadReportingSoc():
    """
    Download Source of change data
    Returns
    -------

    """
    request_data = request.args
    download_type = request_data.get("download_type")
    result = ReportingHandler().download_soc_data(request_data)
    if request_data.get("period_type") == "quarter":
        years = eval(request_data.get("years"))
        quarters = eval(request_data.get("quarters"))
        filename = (
            years[0]
            + " "
            + quarters[0]
            + " - "
            + years[1]
            + " "
            + quarters[1]
            + " "
            + request_data.get("outcome")
            + ".csv"
        )
        filename_excel = (
            years[0]
            + " "
            + quarters[0]
            + " - "
            + years[1]
            + " "
            + quarters[1]
            + " "
            + request_data.get("outcome")
            + XLSX_FORMAT
        )
    elif request_data.get("period_type") == "halfyear":
        years = eval(request_data.get("years"))
        halfyears = eval(request_data.get("halfyears"))
        filename = (
            years[0]
            + " "
            + halfyears[0]
            + " - "
            + years[1]
            + " "
            + halfyears[1]
            + " "
            + request_data.get("outcome")
            + ".csv"
        )
        filename_excel = (
            years[0]
            + " "
            + halfyears[0]
            + " - "
            + years[1]
            + " "
            + halfyears[1]
            + " "
            + request_data.get("outcome")
            + XLSX_FORMAT
        )
    else:
        years = eval(request_data.get("years"))
        filename = (
            years[0] + " - " + years[1] + " " + request_data.get("outcome") + ".csv"
        )
        filename_excel = (
            years[0] + " - " + years[1] + " " + request_data.get("outcome") + XLSX_FORMAT
        )

    return generate_excel_or_csv_file(
        download_type,
        result,
        filename,
        filename_excel,
        "reporting_soc",
        request_data.get("outcome"),
        "",
    )


def DownloadReportingAllocations():
    """
    Download Reporting Allocation data
    Returns
    -------

    """
    request_data = request.args
    download_type = request_data.get("download_type")
    result = ReportingHandler().download_reporting_allocations(request_data)
    if request_data.get("period_type") == "quarter":
        filename = (
            request_data.get("year")
            + " Q"
            + request_data.get("quarter")
            + " Actuals.csv"
        )
        filename_excel = (
            request_data.get("year")
            + " Q"
            + request_data.get("quarter")
            + " Actuals.xlsx"
        )
    else:
        filename = request_data.get("year") + " Actuals.csv"
        filename_excel = request_data.get("year") + " Actuals.xlsx"

    return generate_excel_or_csv_file(
        download_type, result, filename, filename_excel, "", "", ""
    )


def generate_excel_or_csv_file(
    download_type,
    result,
    filename_csv,
    filename_excel,
    report_type,
    outcome_name,
    setCookie,
):
    """
    generate excel or csv files
    Returns
    ------
    """
    if download_type == "csv":
        resp = make_response(result.to_csv(encoding="utf-8", index=False))
        resp.headers["Content-Disposition"] = ATTACHMENT_FILENAME + filename_csv
        resp.headers["Content-Type"] = text_csv
        resp.headers["Set-Cookie"] = setCookie
        return resp
    else:
        excel_name = filename_excel
        if report_type == "reporting_soc" and len(filename_excel) >= 31:
            excel_name = outcome_name + XLSX_FORMAT
        output = io.BytesIO()
        # Use the BytesIO object as the filehandle.
        writer = pd.ExcelWriter(output, engine="xlsxwriter")

        # Write the data frame to the BytesIO object.
        result.to_excel(writer, sheet_name=excel_name.split(".")[0], index=False)

        writer.save()
        xlsx_data = output.getvalue()
        resp = make_response(xlsx_data)
        resp.headers["Content-Disposition"] = ATTACHMENT_FILENAME + excel_name
        resp.headers["Content-Type"] = "application/vnd.ms-excel"
        resp.headers["Set-Cookie"] = setCookie
        return resp


def getScenarioListForMRC():
    """
    Get scenario list from marginal return curves data
    Returns
    -------

    """

    results = ReportingHandler().fetch_scenario_list_for_mrc()
    scenarios = dict([(x["scenario_id"], x["scenario_name"]) for x in results])
    return jsonify(scenarios)


def parse_nodes(nodes_param):
    return nodes_param.split(",") if nodes_param else []


def getMarginalReturnCurves():
    """
    Get marginal return curves data for selected nodes
    Returns
    -------

    """
    nodes = parse_nodes(request.args.get("nodes", ""))
    scenario_id = request.args.get("scenario_id", None)

    request_data = {"nodes": nodes, "scenario_id": scenario_id}
    results = ReportingHandler().fetch_marginal_return_curves_data(request_data)
    return jsonify(results)


def getSpendAllocations():
    """
    Get Spend allocation data
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ReportingHandler().fetch_spend_allocation_data(request_data)

    return jsonify(results)


def getSpendComparison():
    """
    Get Spend comparison data for two scenario
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ScenarioComparisonHandler().fetch_spend_comparison_data(request_data)

    return jsonify(results)


def getSocComarisonByNode():
    """
    Get Source of change comparison data for selected nodes
    Returns
    -------

    """
    nodes = parse_nodes(request.args.get("nodes", ""))

    # Prepare data for processing
    request_data = request.args.to_dict()
    request_data["nodes"] = nodes
    results = ReportingHandler().fetch_soc_comparison_by_node(request_data)

    return jsonify(results)


def getSOCWaterfallChartData():
    """
    Get Waterfall chart data for selected scenarios
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ReportingHandler().fetch_soc_waterfall_chart_data(request_data)
    if results == "Data Not Found":
        message = "Waterfall chart is not available for selected time-period!"
        status_code = 303
        resp = make_response(message, status_code)
        return resp
    return jsonify(results)


def get_time_data():
    """
    Get Period for Existing data
    Returns
    -------

    """
    results = UtilsHandler().get_period_range()
    return jsonify(results)


def getDueToAnalysis():
    """
    Get Data for due analysis chart for selected nodes
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ReportingHandler().due_to_analysis(request_data)
    return jsonify(results)


def getDueToAnalysisCompare():
    """
    Get Data for due analysis chart for selected nodes
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = ScenarioComparisonHandler().due_to_analysis(request_data)
    return jsonify(results)



def getInitialConfigList():
    """
    Get all initial configuration required for optimization input planning page
    Returns
    -------

    """
    # get all scenario list
    results = OptimizationHandler().get_all_scenario_list()
    all_scenarios = dict([(x["scenario_id"], x["scenario_name"]) for x in results])

    # get base scenario list
    results = OptimizationHandler().get_base_scenario_list()
    scenarios = dict([(x["scenario_id"], x["scenario_name"]) for x in results])

    results = OptimizationHandler().get_optimization_scenario_list()
    opt_scenarios = dict([(x["id"], x["name"]) for x in results])

    # get optimization type list
    types = OptimizationHandler().get_optimization_type_list()
    optimization_types = dict([(x["id"], x["name"]) for x in types])

    # get touchpoint groups
    groups = OptimizationHandler().get_touchpoint_groups_list()
    touchpoint_groups = dict([(x["id"], x["name"]) for x in groups])

    # get outcome maximum
    outcome_maximum = OptimizationHandler().get_outcome_maximum_list()
    opt_outcome_maximum = dict([(x["name"], x["name"]) for x in outcome_maximum])

    return jsonify(
        {
            "all_scenarios": all_scenarios,
            "scenarios": scenarios,
            "outcome_maximum": opt_outcome_maximum,
            "optimization_scenarios": opt_scenarios,
            "optimization_types": optimization_types,
            "touchpoint_groups": touchpoint_groups,
        }
    )


def getMediaTouchpointGroupsList():
    """
    Get all touchpoint groups and all touchpoints
    Returns
    -------

    """
    results = OptimizationHandler().get_touchpoint_groups_list()
    touchpoint_groups = dict([(x["id"], x["name"]) for x in results])
    media_touchpoints_list = (
        OptimizationHandler().get_granular_level_media_touchpoints_list()
    )
    touchpoints = dict(
        [(x["variable_id"], x["variable_description"]) for x in media_touchpoints_list]
    )

    return jsonify({"touchpoint_groups": touchpoint_groups, "touchpoints": touchpoints})



def checkoptimizationstatus():
    """
    Check Optimized Scenario status
    Returns
    -------
    status of scenario.
    """
    request_data = request.args.to_dict()
    results = OptimizationHandler().fetch_optimization_status(request_data)
    return jsonify(results[0])


def runScenarioOptimization():
    """
    Run optimization
    Returns
    -------

    """
    id = request.json["optimization_scenario_id"]
    get_status= OptimizationHandler().fetch_optimization_scenario_status(id)
    if get_status[0]['status'] == 'Completed' or get_status[0]['status'] == 'Incomplete':
        result = {
            "status": 303,
            "message": "Scenario already created for optimization, Please create new scenario",
        }
        message = result["message"]
        status_code = result["status"]
        resp = make_response(message, status_code)
        return resp
    else:
        current_user.name = 'User'
        username = current_user.name 
        future = executor.submit(OptimizationHandler().run_optimization_new, id,username)
        # results = OptimizationHandler().run_optimization_new(id,'User')
        # Wait for the result and handle any errors
        result_data = wait_for_future(future)
        if result_data["status"] == "error":
            # Handle the validation error
            error_message = result_data["message"]
            if "futures unfinished" in error_message.lower():
                return jsonify('In-Progress')
            else:
                # If not, return 500
                error_message_obj = ast.literal_eval(error_message)
                formatted_error = [error_message_obj[0], [error_message_obj[1][0]], error_message_obj[2]]
                formatted_error = [formatted_error[0],
                        [formatted_error[1][0]],
                        formatted_error[2]]
                resp = make_response({"message":formatted_error}, 500)
                return resp
        else:
            # Handle success
            success_message = result_data["message"]
            resp = make_response(success_message, 200)
            return resp
        # return "in-progress"
def wait_for_future(future, timeout=10):
    try:
        completed_future, = as_completed([future], timeout=timeout)
        result_data = completed_future.result()
    except TimeoutError:
        result_data = {"status": "error", "message": "In-Progress: The operation timed out"}
    except Exception as e:
        result_data = {"status": "error","message":str(e)}
    else:
        # If no exception occurred, set the "In-Progress" message
        result_data = {"status": 200,"message": "In-Progress"}

    return result_data

def getGroupConstraints():
    """
    Get list of group constraints
    Returns
    -------

    """
    request_data = request.args.to_dict()
    scenario_id = int(request_data["scenario_id"])
    results = OptimizationHandler().get_optimization_group_constraints(scenario_id)
    return jsonify(results)


def getBaseScenarioTotalBudget():
    """
    Get Total Spend of a base scenario
    Returns
    -------

    """
    request_data = request.args.to_dict()
    total = OptimizationHandler().get_base_scenario_total_budget(request_data)
    return jsonify(total[0])


def createOptimizationScenario():
    """
    Create new optimization scenario
    Returns
    -------

    """
    logger.info("In create new optimization scenario")
    request_data = request.json
    period_end = request_data["period_end"]
    if period_end != None:
        result = OptimizationHandler().create_optimization_scenario(request_data)
        if type(result) == dict and result["status"]:
            logger.info(result["message"])
            message = result["message"]
            status_code = result["status"]
            resp = make_response(message, status_code)
            return resp

        results,upper_bound_sum,lower_bound_sum,base_spend_sum = OptimizationHandler().save_individual_spend_bounds_for_opt_scenario(
            result, request_data
        )
        logger.info("Successfully created scenario.")
    else:
        result = {"status": 303, "message": "Select Valid Time Period"}
        if type(result) == dict and result["status"]:
            logger.info(result["message"])
            message = result["message"]
            status_code = result["status"]
            resp = make_response(message, status_code)
            return resp
    return jsonify({"optimization_scenario_id": result, "spend_bounds": results,"lower_bound_sum":lower_bound_sum,"upper_bound_sum":upper_bound_sum,"base_spend_sum":base_spend_sum})


def downloadIndividualSpendBounds():
    """
    Download individual spend bounds
    Returns
    -------

    """
    print(request.args)
    period_type = request.args.get("period_type")
    request_data = request.args.get("optim-id")
    result = pd.DataFrame.from_records(
        OptimizationHandler().get_individual_basespends(request_data, period_type)
    )
    result["lock"] = "Yes"
    result["Lower Bound %"] = ""
    result["Upper Bound %"] = ""
    result["Lower Bound $"] = result["spend"]
    result["Upper Bound $"] = result["spend"]

    result_filtered = result[
        (~result["variable_name"].str.contains("_FLAGS_"))
        & (result["variable_name"].str.startswith("M_"))
    ].reset_index(drop=True)
    period_start = int(request.args.get("period_start"))
    period_end = int(request.args.get("period_end"))
    result_filtered = result_filtered[
        (result_filtered["period"] >= period_start)
        & (result_filtered["period"] <= period_end)
    ]
    result_filtered = result_filtered.rename(
        columns={"period": "period(" + str(period_type) + "ly)"}
    )
    resp = make_response(result_filtered.to_csv(encoding="utf-8", index=False))
    filename = "Individual Spend Bounds.csv"
    resp.headers["Content-Disposition"] = ATTACHMENT_FILENAME + filename
    resp.headers["Content-Type"] = text_csv
    return resp

def download_app_logs():
    """
    download app logs
    Returns
    -------
    """
    request_data = request.args.to_dict()
    if request_data['category'] == 'Optimized':
        result = pd.DataFrame.from_records(
            MaintenanceHandler().get_individual_basespends(request_data)
        )
        period_end=int(request_data['period_end'])
        period_start = int(request_data['period_start'])
        period_type = request_data['period_type']
        scenario_type_mapping = {
        1: 'Budget Reallocation',
        2: 'reallocation',
        3: 'New Budget Allocation',
        4: 'Incremental Budget Allocation'
        }

        # Update the scenario_type column using the mapping
        result['scenario_type'] = result['scenario_type'].map(scenario_type_mapping)
        result_filtered = result[
            (~result["variable_name"].str.contains("_FLAGS_"))
            & (result["variable_name"].str.startswith("M_"))
        ].reset_index(drop=True)
        result_filtered = result_filtered[
                (result_filtered["period"] >= period_start)
                & (result_filtered["period"] <= period_end)
            ]
        if request_data['status'] == 'Completed':
            result1 = pd.DataFrame.from_records(MaintenanceHandler().get_scenario_outcome(request_data))
            result1 = result1[
            (~result1["variable_name"].str.contains("_FLAGS_"))
            & (result1["variable_name"].str.startswith("M_"))].reset_index(drop=True)
            if period_type == "quarter":
                result1 = result1[
                    (result1["quarter"] >= period_start)
                    & (result1["quarter"] <= period_end)
                ]
            if period_type == "month":
                result1 = result1[
                    (result1["month"] >= period_start)
                    & (result1["month"] <= period_end)
                ]
        # Create ExcelWriter and write DataFrames to sheets
        output = BytesIO()
        with ExcelWriter(output, engine='xlsxwriter') as writer:
            result_filtered.to_excel(writer, sheet_name='Individual_Spend_Bounds', index=False,header=True)
            if request_data['status'] == 'Completed':
                result1.to_excel(writer, sheet_name='Optimized_scenario', index=False,header=True)

        output.seek(0)
        
        # Create Flask response with the Excel file
        resp = make_response(output.read())
        user_name = request_data['user_name'] if request_data['user_name'] and request_data['user_name'] != 'null' and request_data['user_name'] != 'undefined' else 'user'
        filename = f"{user_name}_{request_data['scenario_name']}.xlsx" 
        resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"
        resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return resp
    else:
        result = pd.DataFrame.from_records(MaintenanceHandler().get_scenario_outcome_planner(request_data))
        result_filtered = result[
        (~result["variable_name"].str.contains("_FLAGS_"))
        & (result["variable_name"].str.startswith("M_"))
        ].reset_index(drop=True)
        resp = make_response(result_filtered.to_csv(encoding="utf-8", index=False))
        user_name = request_data['user_name'] if request_data['user_name'] and request_data['user_name'] != 'null' and request_data['user_name'] != 'undefined' else 'user'
        filename = f"{user_name}_{request_data['scenario_name']}.csv" 
        resp.headers["Content-Disposition"] = ATTACHMENT_FILENAME + filename
        resp.headers["Content-Type"] = text_csv
        return resp


def ImportIndividualSpendBounds():
    """
    Import and save individual spend bounds
    Returns
    -------

    """
    scenario_id = request.form["scenario_id"] or 1
    imported_data = request.files["file"]
    period_type = request.form["period_type"]
    results,lower_sum,upper_sum,base_sum = OptimizationHandler().save_individual_spend_bounds(
        imported_data, scenario_id, period_type
    )
    if base_sum == '':
        base_sum = request.form["base_sum"]
    lower_sum = convert_to_native_types(lower_sum)
    upper_sum = convert_to_native_types(upper_sum)
    base_sum = convert_to_native_types(base_sum)
    return jsonify({"data":results,"lower_sum":lower_sum,"upper_sum":upper_sum,"base_sum":base_sum})


def updateIndividualSpendsBounds():
    """
    update individual spend bounds
    Returns
    -------

    """
    request_data = request.json
    results,bounds,optimization_type = OptimizationHandler().update_individual_spend_bounds(request_data)
    results["lower_sum"]=((int(results["Lower Bound $"]) - round(bounds[0]["lowerbound"],0) )+request_data['lower_sum'])
    results["upper_sum"]=((int(results["Upper Bound $"]) - round(bounds[0]["upperbound"],0))+request_data['upper_sum'])
    if optimization_type == 3:
        results["base_sum"]=((int(results["spend"]) - round(bounds[0]["base_spend"],0) )+request_data['base_sum'])
    return jsonify(results)


def updateIndividualSpendsLockUnlockAll():
    """
    lock unlock all individual spend bounds
    Returns
    -------

    """
    request_data = request.json
    results = OptimizationHandler().update_individual_spend_lock_unlock_all(
        request_data
    )
    return jsonify(results)


def getGroupTouchpoints():
    """
    Get list of touchpoints for a group
    Returns
    -------

    """
    request_data = request.args.to_dict()
    group_id = int(request_data["group"])
    results = OptimizationHandler().get_touchpoints_for_group(group_id)
    return jsonify(results)


def saveGroupTouchpoints():
    """
    Save touchpoints for a group
    Returns
    -------

    """
    request_data = request.json
    # save group touchpoint mapping
    results = OptimizationHandler().save_group_touchpoint_mapping(request_data)

    # get touchpoint groups
    groups = OptimizationHandler().get_touchpoint_groups_list()
    touchpoint_groups = dict([(x["id"], x["name"]) for x in groups])

    return jsonify(touchpoint_groups)


def addGroupConstraint():
    """
    Add group constraint from an optimization scenario
    Returns
    -------

    """
    request_data = request.json
    results = OptimizationHandler().add_group_constraint(request_data)
    return jsonify(results)


def deleteGroupConstraint():
    """
    remove group constraint to an optimization scenario
    Returns
    -------

    """
    request_data = request.json
    results = OptimizationHandler().delete_group_constraint(request_data)
    return jsonify(results)


def delete_optimized_scenario():
    """
    remove group constraint to an optimization scenario
    Returns
    -------

    """
    request_data = request.json
    if request_data['category']== 'Optimized': 
        results = MaintenanceHandler().delete_optimized_scenario(request_data)
    else:
        results = MaintenanceHandler().delete_scenario(request_data)

    return jsonify(results)


def optimizationImportScenarioSpends():
    """
    import base scenario spends
    Returns
    -------

    """
    imported_data = request.files["file"]
    results = OptimizationHandler().import_scenario_spends(imported_data)
    return jsonify(results)


def optimizationCreateBaseScenario():
    """
    Create new base scenario and add data to it
    Returns
    -------

    """
    request_data = request.json
    result = OptimizationHandler().create_base_scenario(request_data)

    if "status" in result:
        message = result["message"]
        status_code = result["status"]
        resp = make_response(message, status_code)
        return resp

    # get latest base scenario list
    results = OptimizationHandler().get_base_scenario_list()
    scenarios = dict([(x["scenario_id"], x["scenario_name"]) for x in results])

    return jsonify(scenarios)


def getOptimizationScenarioDetails():
    """
    Get optimization scenario details for selected scenario
    Returns
    -------

    """
    request_data = request.args.to_dict()
    results = OptimizationHandler().getOptimizationScenarioDetails(request_data)

    return jsonify(results)


def get_optimization_scenario_outcome_results():
    """
    get optimization scenario outcome
    Returns
    -------
    """
    request_data = request.json
    results = OptimizationHandler().getOptimizationScenarioOutcomes(request_data)
    return jsonify(results)


def get_kpi_output_comparison_data():
    """
    get kpi output comparison data
    Returns
    -------
    """
    request_data = request.args.to_dict()
    results = OptimizationHandler().getKPIOutputComparisonData(request_data)
    return jsonify(results)


def download_kpi_output_comparison():
    request_data = request.args
    result = OptimizationHandler().download_kpi_output_comparison(request_data)
    file_name = result
    return send_from_directory(OP_OUTPUT_FILES_DIR, file_name, as_attachment=True)


def get_maintenance_scenario_list():
    """
    get maintenance scenario list
    Returns
    -------
    """
    result = MaintenanceHandler().get_maintenance_scenario_list()
    return jsonify(result)




def download_waterfall_chart_data():
    """
    download water fall data
    Returns

    a csv file
    -------
    """
    request_data = request.args
    waterfall_data = ReportingHandler().get_all_soc_data(request_data)
    resp = make_response(waterfall_data.to_csv(encoding="utf-8", index=False))
    filename = request_data["filename"]
    resp.headers["Content-Disposition"] = ATTACHMENT_FILENAME + filename
    resp.headers["Content-Type"] = text_csv
    return resp



def get_romi_cpa_data():
    nodes = parse_nodes(request.args.get("nodes", ""))
    request_data = request.args.to_dict()
    request_data["nodes"] = nodes
    romi_cpa_data = ReportingHandler().fetch_data_ROMI_CPA(request_data)
    romi_cpa_data_serializable = convert_to_native_types(romi_cpa_data)
    json_data = json.dumps(romi_cpa_data_serializable)
    return json_data


def get_romi_cpa_data_compare():
    request_data = request.json
    romi_cpa_data = ScenarioComparisonHandler().fetch_data_ROMI_CPA(request_data)
    romi_cpa_data_serializable = convert_to_native_types(romi_cpa_data)
    json_data = json.dumps(romi_cpa_data_serializable)
    return json_data


def convert_to_native_types(data):
    if isinstance(data, (np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    elif isinstance(data, (np.float64, np.float32)):
        return float(data)
    elif isinstance(data, dict):
        return {key: convert_to_native_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_native_types(item) for item in data]
    else:
        return data


def get_base_spend_value_for_group_constraints():
    request_data = request.args
    base_spend = OptimizationHandler().get_base_spend_value_for_group_constraints(
        request_data
    )
    return jsonify(base_spend)


def get_period_data_sc():
    results = ReportingHandler().fetch_period_data_reporting_sc()
    return jsonify(results)


def get_interaction_effect():
    request_data = request.args
    results = ReportingHandler().fetch_data_reporting_sc(request_data)
    return jsonify(results)


def download_marginal_return_curves_data():
    request_data = request.args
    marginal_return_curves_data = (
        ReportingHandler().download_marginal_return_curves_data(request_data)
    )

    # Convert Excel data to CSV
    csv_data = convert_excel_to_csv(marginal_return_curves_data)

    resp = make_response(csv_data)
    resp.headers["Content-Disposition"] = (
        ATTACHMENT_FILENAME + "Marginal_Return_Curves" + ".csv"
    )
    resp.headers["Content-Type"] = text_csv  # Set content type to CSV
    return resp

def convert_excel_to_csv(excel_data):
    # Check if excel_data is already bytes
    if isinstance(excel_data, bytes):
        df = pd.read_excel(BytesIO(excel_data))
    else:
        df = pd.read_excel(excel_data)
        
    csv_data = df.to_csv(index=False)
    
    return csv_data

