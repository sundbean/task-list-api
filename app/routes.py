from app import db
from app.models.task import Task
from flask import Blueprint, make_response, request, jsonify
from sqlalchemy import desc
from datetime import datetime

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

@tasks_bp.route("", methods=["POST", "GET"])
def handle_tasks():
    if request.method == "POST":
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
            "task": {
                "id": new_task.task_id,
                "title": new_task.title,
                "description": new_task.description,
                "is_complete": is_task_complete(new_task)
            }
        }

        return make_response(jsonify(response), 201)

    elif request.method == "GET":

        sort_query = request.args.get("sort")

        if sort_query == "asc":
            tasks = Task.query.order_by("title")
        elif sort_query == "desc":
            tasks = Task.query.order_by(desc("title"))
        else:
            tasks = Task.query.all()

        tasks_response = []

        for task in tasks:
            tasks_response.append({
                "id": task.task_id,
                "title": task.title,
                "description":task.description,
                "is_complete": is_task_complete(task)
            })

        return jsonify(tasks_response)

@tasks_bp.route("/<task_id>", methods=["GET", "PUT", "DELETE"])
def handle_task(task_id):
    
    task = Task.query.get(task_id)

    if task is None:
        return make_response("", 404)

    if request.method == "GET":
    
        return {
            "task": {
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete": is_task_complete(task)
            }
        }

    elif request.method == "PUT":

        request_body = request.get_json()

        task.title = request_body['title']
        task.description = request_body['description']
        task.completed_at = request_body['completed_at']

        db.session.commit()

        return {
            "task": {
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete": is_task_complete(task)
            }
        }

    elif request.method == "DELETE":

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
        "task": {
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete": is_task_complete(task)   # False
        }
    }


@tasks_bp.route("/<task_id>/mark_complete", methods=["PATCH"])
def mark_task_complete(task_id):
    task = Task.query.get(task_id)

    if task is None:
        return make_response("", 404)

    task.completed_at = datetime.now()

    return {
        "task": {
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete": is_task_complete(task)   # False
        }
    }
# Helper functions
def is_task_complete(task):
    if not task.completed_at:
        return False
    return True