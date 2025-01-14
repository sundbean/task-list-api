from app import db
from app.models.task import Task
from app.models.goal import Goal
from flask import Blueprint, make_response, request, jsonify
from sqlalchemy import desc
from datetime import datetime
import requests
import os

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")
goals_bp = Blueprint("goals", __name__, url_prefix="/goals")

##########################
#### /tasks Endpoints ####
##########################

@tasks_bp.route("", methods=["POST"])
def post_new_task():
    request_body = request.get_json()

    try:
        new_task = Task(title=request_body['title'],
                        description=request_body['description'],
                        completed_at=request_body['completed_at'])
    except KeyError:
        return make_response({
            "details": "Invalid data"
        }, 400)

    db.session.add(new_task)
    db.session.commit()

    response = {
        "task": new_task.get_task_info()
    }

    return make_response(jsonify(response), 201)


@tasks_bp.route("", methods=["GET"])
def get_tasks():
    sort_query = request.args.get("sort")
    sort_by_id_query = request.args.get("sort_by_id")
    filter_by_query = request.args.get("filter_by_title")

    if sort_query == "asc":
        tasks = Task.query.order_by("title")
    elif sort_query == "desc":
        tasks = Task.query.order_by(desc("title"))
    elif sort_by_id_query == "asc":
        tasks = Task.query.order_by("task_id")
    elif sort_by_id_query == "desc":
        tasks = Task.query.order_by(desc("task_id"))
    elif filter_by_query:
        tasks = Task.query.filter_by(title=filter_by_query)
    else:
        tasks = Task.query.all()

    return jsonify([task.get_task_info() for task in tasks])


@tasks_bp.route("/<task_id>", methods=["GET"])
def get_single_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return make_response("", 404)

    return {
        "task": task.get_task_info()
    }


@tasks_bp.route("/<task_id>", methods=["PUT"])
def edit_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return make_response("", 404)

    request_body = request.get_json()

    task = task.from_json(request_body)

    db.session.commit()

    return {
        "task": task.get_task_info()
    }


@tasks_bp.route("/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return make_response("", 404)

    db.session.delete(task)
    db.session.commit()

    return {
        "details": f"Task {task.task_id} \"{task.title}\" successfully deleted"
    }


@tasks_bp.route("/<task_id>/mark_incomplete", methods=["PATCH"])
def mark_task_incomplete(task_id):
    task = Task.query.get(task_id)

    if task is None:
        return make_response("", 404)

    task.completed_at = None

    return {
        "task": task.get_task_info()
    }


@tasks_bp.route("/<task_id>/mark_complete", methods=["PATCH"])
def mark_task_complete(task_id):
    task = Task.query.get(task_id)

    if task is None:
        return make_response("", 404)

    task.completed_at = datetime.now()

    post_to_slack(f"Someone just completed the task {task.title}")

    return {
        "task": task.get_task_info()
    }



##########################
#### /goals Endpoints ####
##########################

@goals_bp.route("", methods=['POST'])
def post_new_goal():
    request_body = request.get_json()

    try:
        new_goal = Goal(title=request_body['title'])
    except KeyError:
        return make_response({
            "details": "Invalid data"
        }, 400)

    db.session.add(new_goal)
    db.session.commit()

    response = {
        "goal": new_goal.to_json()
    }

    return make_response(jsonify(response), 201)


@goals_bp.route("", methods=['GET'])
def get_goals():
    sort_query = request.args.get("sort")
    sort_by_id_query = request.args.get("sort_by_id")
    filter_by_title_query = request.args.get("filter_by_title")

    if sort_query == "asc":
        goals = Goal.query.order_by("title")
    elif sort_query == "desc":
        goals = Goal.query.order_by(desc("title"))
    elif sort_by_id_query == "asc":
        goals = Goal.query.order_by("goal_id")
    elif sort_by_id_query == "desc":
        goals = Goal.query.order_by(desc("goal_id"))
    elif filter_by_title_query:
        goals = Goal.query.filter_by(title=filter_by_title_query)
    else:
        goals = Goal.query.all()

    return jsonify([goal.to_json() for goal in goals])


@goals_bp.route("/<goal_id>", methods=['GET'])
def get_single_goal(goal_id):
    goal = Goal.query.get(goal_id)
    if goal is None:
        return make_response("", 404)

    return {
        "goal": goal.to_json()
    }


@goals_bp.route("/<goal_id>", methods=['PUT'])
def edit_goal(goal_id):
    goal = Goal.query.get(goal_id)
    if goal is None:
        return make_response("", 404)

    request_body = request.get_json()

    goal.title = request_body["title"]

    db.session.commit()

    return {
        "goal": goal.to_json()
    }


@goals_bp.route("/<goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    goal = Goal.query.get(goal_id)
    if goal is None:
        return make_response("", 404)
    
    db.session.delete(goal)
    db.session.commit()

    return {
        "details": f"Goal {goal.goal_id} \"{goal.title}\" successfully deleted"
    }


@goals_bp.route("/<goal_id>/tasks", methods=["POST"])
def post_tasks_for_goal(goal_id):
    goal = Goal.query.get(goal_id)
    if goal is None:
        return make_response("", 404)

    request_body = request.get_json()

    for task_id in request_body['task_ids']:
        task = Task.query.get(task_id)
        task.goal_id = int(goal_id)
        
    db.session.commit()

    return {
        "id": int(goal_id),
        "task_ids": request_body['task_ids']
    }


@goals_bp.route("/<goal_id>/tasks", methods=["GET"])
def get_tasks_for_goal(goal_id):
    goal = Goal.query.get(goal_id)
    if goal is None:
        return make_response("", 404)

    associated_tasks = Task.query.filter_by(goal_id=int(goal_id))

    response = goal.to_json()
    response['tasks'] = [task.get_task_info() for task in associated_tasks]

    return response



##########################
#### Helper Functions ####
##########################

def post_to_slack(message):
    """
    Posts a given message to the task-notifications channel in my Task Manager Slack workspace.
    """
    path = "https://slack.com/api/chat.postMessage"

    SLACK_API_KEY = os.environ.get("SLACK_API_KEY")

    auth_header = {
        "Authorization": f"Bearer {SLACK_API_KEY}"
    }

    query_params = {
        "channel": "task-notifications",
        "text": message
    }

    requests.post(path, params=query_params, headers=auth_header)

