"""
This script is for all the routes mapping and end point urls mapping
"""

import os

import pandas as pd
import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_oidc import OpenIDConnect
from flask_session import Session

from app_server.MMOptim.validation import FeasibilityError, ValidationError
from config import *
from helpers import config, is_access_token_valid, is_id_token_valid
from user import User

# CONFIGURING APP PATH

ABSPATH = os.path.abspath(__file__)
DNAME = os.path.dirname(ABSPATH)
os.chdir(DNAME)
os.sys.path.append(DNAME)
os.environ.update({"PROJECT_PATH": DNAME})

from app_server.views import (ChangeScenario, DownloadReportingAllocations,
                              DownloadReportingSoc,
                              DownloadScenarioComparisons,
                              ImportIndividualSpendBounds, UserScenario,
                              addGroupConstraint, checkoptimizationstatus,
                              createOptimizationScenario,
                              delete_optimized_scenario, deleteGroupConstraint,
                              download_app_logs,
                              download_kpi_output_comparison,
                              download_marginal_return_curves_data,
                              download_waterfall_chart_data,
                              downloadIndividualSpendBounds,
                              downloadScenarioPlanningReport,
                              get_base_spend_value_for_group_constraints,
                              get_interaction_effect,
                              get_kpi_output_comparison_data,
                              get_maintenance_scenario_list,
                              get_period_data_sc, get_romi_cpa_data,
                              get_time_data, getBaseScenarioTotalBudget,
                              getDueToAnalysis, getDueToAnalysisCompare,
                              getGroupConstraints, getGroupTouchpoints,
                              getInitialConfigList, getMarginalReturnCurves,
                              getMediaHierarchyList,
                              getMediaTouchpointGroupsList,
                              getOptimizationScenarioDetails,
                              getReportingAllocationGraph,
                              getReportingAllocations,
                              getReportingAllocationsSOC,
                              getReportingAllocationsYear,
                              getScenarioComarisonByNode, getScenarioList,
                              getScenarioListForMRC, getSocComarisonByNode,
                              getSOCWaterfallChartData, getSpendAllocations,
                              getSpendAllocationsSummary, getSpendComparison,
                              getSpendComparisonSummary, importSpendScenario,
                              optimizationCreateBaseScenario,
                              optimizationImportScenarioSpends,
                              runScenarioOptimization, saveGroupTouchpoints,
                              updateIndividualSpendsBounds,
                              updateIndividualSpendsLockUnlockAll)

# Flask constructor takes the name of
# current module (__name__) as argument.

app = Flask(__name__)

app.config.from_pyfile("config.py")

login_manager = LoginManager()
login_manager.init_app(app)

APP_STATE = "ApplicationState"
NONCE = "SampleNonce"

ss = Session()
ss.init_app(app)


# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/index.html")
def callback():
    """render home page"""
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if len(request.args) == 0 or request.args.get("iss") == "https://ebates.okta.com":
        query_params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "scope": "openid email profile",
            "state": APP_STATE,
            "nonce": NONCE,
            "response_type": "code",
            "response_mode": "query",
        }

        # build request_uri
        request_uri = "{base_url}?{query_params}".format(
            base_url=config["auth_uri"],
            query_params=requests.compat.urlencode(query_params),
        )
        return redirect(request_uri)
    code = request.args.get("code")
    if not code:
        return (
            f"The code was not returned or is not accessible1 to {request} {request.args}",
            403,
        )
    query_params = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": request.base_url,
    }
    query_params = requests.compat.urlencode(query_params)
    exchange = requests.post(
        config["token_uri"],
        headers=headers,
        data=query_params,
        auth=(config["client_id"], config["client_secret"]),
    ).json()

    # Get tokens and validate
    if not exchange.get("token_type"):
        return "Unsupported token type. Should be 'Bearer'.", 403
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]

    if not is_access_token_valid(access_token, config["issuer"]):
        return "Access token is invalid", 403

    if not is_id_token_valid(id_token, config["issuer"], config["client_id"], NONCE):
        return "ID token is invalid", 403

    # Authorization flow successful, get userinfo and login user
    userinfo_response = requests.get(
        config["userinfo_uri"], headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    print(userinfo_response["email"], userinfo_response["given_name"])

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response["email"]
    user_name = userinfo_response["given_name"]

    user = User(id_=unique_id, name=user_name, email=user_email)

    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email)

    login_user(user)
    return redirect(url_for("index1"))


@app.route("/", methods=["GET", "POST"])
# @login_required
def index1():
    """render home page"""
    return render_template("index.html", user=current_user)


@app.route("/login", methods=["GET", "POST"])
# @login_required
def login():
    """render login page"""
    return redirect(url_for("index"))


@app.route("/scenarioanalysis.html", methods=["GET", "POST"])
# @login_required
def scenario_planning():
    """render scenario planning page"""
    return render_template("scenarioanalysis.html")


@app.route("/scenario-comparison.html", methods=["GET", "POST"])
# @login_required
def scenariocompare():
    """Render scenario comparison page"""
    return render_template("scenario-comparison.html")


@app.route("/optimization.html", methods=["GET", "POST"])
# @login_required
def optimization_new_page():
    """Render optimization page"""
    return render_template("optimization_new.html")


@app.route("/reporting-allocation-actuals.html", methods=["GET", "POST"])
# @login_required
def reporting_allocation_actuals_page():
    """Render reporting allocation page"""
    return render_template("reporting-allocation-actuals.html")


@app.route("/reporting-due-charts.html", methods=["GET", "POST"])
def reporting_due_charts_page():
    """Render due to chart page"""
    return render_template("reporting-due-charts.html")


@app.route("/reporting-source-change.html", methods=["GET", "POST"])
def reporting_source_change_page():
    """Render source of change page in reporting tab"""
    return render_template("reporting-source-change.html")


@app.route("/reporting-marginal-return-curves.html", methods=["GET", "POST"])
def reporting_marginal_return_curves_page():
    """Render marginal return curve page in reporting tab"""
    return render_template("reporting-marginal-return-curves.html")


@app.route("/spend_vs_outcome_charts.html", methods=["GET", "POST"])
def romi_and_cpa_charts():
    """Render ROMI and CPA charts page in reporting tab"""
    return render_template("spend_vs_outcome_charts.html")


@app.route("/reporting-secondary-contribution.html", methods=["GET", "POST"])
def interaction_effect():
    """Render Interaction Effect page in reporting tab"""
    return render_template("reporting-secondary-contribution.html")


@app.route("/maintenance.html", methods=["GET", "POST"])
def maintenance_page():
    """Render Maintenance Page"""
    return render_template("maintenance.html")


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    response = jsonify(error.to_dict())
    response.status_code = 500
    return response


@app.errorhandler(FeasibilityError)
def handle_feasibility_error(error):
    response = jsonify(error.to_dict())
    response.status_code = 500
    return response


# End point definitions for scenario planning module

app.add_url_rule("/getScenarioList", view_func=getScenarioList, methods=["GET"])

app.add_url_rule("/changenodespend", view_func=ChangeScenario, methods=["GET"])

app.add_url_rule(
    "/importSpendScenario", view_func=importSpendScenario, methods=["POST"]
)

app.add_url_rule(
    "/userscenario/<string:user_id>", view_func=UserScenario, methods=["POST", "GET"]
)

app.add_url_rule(
    "/get_media_hierarchy_list",
    view_func=getMediaHierarchyList,
    methods=["POST", "GET"],
)

app.add_url_rule(
    "/download_scenario_planning_report",
    view_func=downloadScenarioPlanningReport,
    methods=["GET"],
)

# End point definitions for reporting module

app.add_url_rule(
    "/get_reporting_allocations", view_func=getReportingAllocations, methods=["GET"]
)

app.add_url_rule(
    "/get_reporting_allocations_graph",
    view_func=getReportingAllocationGraph,
    methods=["GET"],
)

app.add_url_rule(
    "/get_reporting_allocations_list",
    view_func=getReportingAllocationsYear,
    methods=["GET"],
)

app.add_url_rule(
    "/get_reporting_allocations_list_SOC",
    view_func=getReportingAllocationsSOC,
    methods=["GET"],
)

app.add_url_rule(
    "/get_spend_allocations_summary",
    view_func=getSpendAllocationsSummary,
    methods=["GET"],
)

app.add_url_rule(
    "/download_reporting_soc", view_func=DownloadReportingSoc, methods=["GET"]
)

app.add_url_rule(
    "/download_reporting_allocations",
    view_func=DownloadReportingAllocations,
    methods=["GET"],
)

app.add_url_rule(
    "/get_scenario_list_mrc", view_func=getScenarioListForMRC, methods=["GET"]
)

app.add_url_rule(
    "/get_marginal_return_curves", view_func=getMarginalReturnCurves, methods=["GET"]
)

app.add_url_rule(
    "/get_spend_allocations", view_func=getSpendAllocations, methods=["GET"]
)

app.add_url_rule(
    "/get_soc_comarison_by_node", view_func=getSocComarisonByNode, methods=["GET"]
)

app.add_url_rule(
    "/get_soc_wfc_data", view_func=getSOCWaterfallChartData, methods=["GET"]
)

app.add_url_rule(
    "/get_reporting_due_to_analysis", view_func=getDueToAnalysis, methods=["GET"]
)

app.add_url_rule(
    "/download_waterfall_data", view_func=download_waterfall_chart_data, methods=["GET"]
)

app.add_url_rule("/get_romi_cpa_data", view_func=get_romi_cpa_data, methods=["GET"])

# app.add_url_rule("/get_romi_cpa_compare", view_func=get_romi_cpa_data_compare, methods=['POST'])

app.add_url_rule(
    "/download_marginal_return_curves_data",
    view_func=download_marginal_return_curves_data,
    methods=["GET"],
)

app.add_url_rule(
    "/get_period_secondary_contribution", view_func=get_period_data_sc, methods=["GET"]
)

app.add_url_rule(
    "/get_secondary_contribution", view_func=get_interaction_effect, methods=["GET"]
)


# End point definitions for optimization module

app.add_url_rule(
    "/run_scenario_optimization", view_func=runScenarioOptimization, methods=["POST"]
)

app.add_url_rule(
    "/optimization_scenario_status", view_func=checkoptimizationstatus, methods=["GET"]
)
# app.add_url_rule("/download_optim_output_new", view_func=download_optimization_report, methods=['GET'])

app.add_url_rule(
    "/get_initial_config_list", view_func=getInitialConfigList, methods=["GET"]
)

app.add_url_rule(
    "/getMediaTouchpointGroupsList",
    view_func=getMediaTouchpointGroupsList,
    methods=["GET"],
)

# app.add_url_rule("/getSpendScenarioGranularLevel", view_func=getSpendScenarioGranularLevel, methods=['POST'])

app.add_url_rule("/getGroupConstraints", view_func=getGroupConstraints, methods=["GET"])

app.add_url_rule(
    "/get_base_scenario_budget", view_func=getBaseScenarioTotalBudget, methods=["GET"]
)

app.add_url_rule(
    "/create_optimization_scenario",
    view_func=createOptimizationScenario,
    methods=["POST"],
)

app.add_url_rule(
    "/download_individual_spend_bounds",
    view_func=downloadIndividualSpendBounds,
    methods=["GET"],
)

app.add_url_rule(
    "/import_individual_spend_bounds",
    view_func=ImportIndividualSpendBounds,
    methods=["POST"],
)

app.add_url_rule(
    "/update_individual_spends_bounds",
    view_func=updateIndividualSpendsBounds,
    methods=["POST"],
)

app.add_url_rule(
    "/update_individual_spends_lock_unlock",
    view_func=updateIndividualSpendsLockUnlockAll,
    methods=["POST"],
)

app.add_url_rule("/getGroupTouchpoints", view_func=getGroupTouchpoints, methods=["GET"])

app.add_url_rule(
    "/saveGroupTouchpoints", view_func=saveGroupTouchpoints, methods=["POST"]
)

app.add_url_rule("/addGroupConstraint", view_func=addGroupConstraint, methods=["POST"])

app.add_url_rule(
    "/delete_group_constraints", view_func=deleteGroupConstraint, methods=["POST"]
)

app.add_url_rule(
    "/optimization_import_scenario_spends",
    view_func=optimizationImportScenarioSpends,
    methods=["POST"],
)

app.add_url_rule(
    "/optimization_create_base_scenario",
    view_func=optimizationCreateBaseScenario,
    methods=["POST"],
)

app.add_url_rule(
    "/get_optimization_scenario_details",
    view_func=getOptimizationScenarioDetails,
    methods=["GET"],
)

# app.add_url_rule("/get_optimization_scenario_outcome_results", view_func=get_optimization_scenario_outcome_results,
#                  methods=['POST'])

app.add_url_rule(
    "/get_kpi_output_comparison_data",
    view_func=get_kpi_output_comparison_data,
    methods=["GET"],
)

app.add_url_rule(
    "/download_kpi_output_comparison",
    view_func=download_kpi_output_comparison,
    methods=["GET"],
)

# app.add_url_rule("/download_group_constraints", view_func=download_group_constraints_report, methods=['GET'])

app.add_url_rule(
    "/get_base_spend_value_for_group_constraints",
    view_func=get_base_spend_value_for_group_constraints,
    methods=["GET"],
)

# app.add_url_rule("/download_base_scenario", view_func=download_base_scenario_details, methods=['GET'])


# End point definition for Scenario Comparison module

app.add_url_rule(
    "/get_spend_comparison_summary",
    view_func=getSpendComparisonSummary,
    methods=["GET"],
)

app.add_url_rule(
    "/get_scenario_comarison_by_node",
    view_func=getScenarioComarisonByNode,
    methods=["GET"],
)

app.add_url_rule("/get_spend_comparison", view_func=getSpendComparison, methods=["GET"])

app.add_url_rule("/get_time_period", view_func=get_time_data, methods=["GET"])

app.add_url_rule(
    "/download_scenario_comparisons",
    view_func=DownloadScenarioComparisons,
    methods=["GET"],
)

app.add_url_rule(
    "/get_comparision_due_to_analysis",
    view_func=getDueToAnalysisCompare,
    methods=["GET"],
)

# End point definition for maintenance module

app.add_url_rule(
    "/get_maintenance_scenario_list",
    view_func=get_maintenance_scenario_list,
    methods=["GET"],
)

app.add_url_rule(
    "/delete_optimized_scenario", view_func=delete_optimized_scenario, methods=["POST"]
)

app.add_url_rule("/download_app_logs", view_func=download_app_logs, methods=["GET"])
