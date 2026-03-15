"""Tests for the Todoist API CLI (todoist_api.py)."""

import io
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the todoist scripts directory to the path so we can import todoist_api
TODOIST_SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    "skills",
    "productivity",
    "todoist",
    "scripts",
)
sys.path.insert(0, os.path.abspath(TODOIST_SCRIPT_DIR))

import todoist_api


def _make_args(**kwargs):
    """Build an argparse-like Namespace for testing."""
    ns = MagicMock()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _mock_response(json_data, status_code=200, headers=None):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = json.dumps(json_data)
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------
class TestListTasks(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_list_tasks_success(self, mock_requests):
        tasks = [
            {
                "id": "123",
                "content": "Buy milk",
                "description": "",
                "due": {"date": "2026-03-16", "datetime": "", "string": "Mar 16", "timezone": "", "is_recurring": False},
                "duration": None,
                "priority": 1,
                "project_id": "456",
                "labels": ["errands"],
                "url": "https://todoist.com/showTask?id=123",
            }
        ]
        mock_requests.get.return_value = _mock_response(tasks)
        mock_requests.HTTPError = Exception

        args = _make_args(filter="", project_id=None, label=None)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.list_tasks(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0]["content"], "Buy milk")
        self.assertEqual(output[0]["labels"], ["errands"])

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_list_tasks_with_filter(self, mock_requests):
        mock_requests.get.return_value = _mock_response([])
        mock_requests.HTTPError = Exception

        args = _make_args(filter="today", project_id=None, label=None)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.list_tasks(args)
        # Verify filter was passed as param
        call_kwargs = mock_requests.get.call_args
        self.assertEqual(call_kwargs.kwargs.get("params", {}).get("filter"), "today")

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_list_tasks_with_label(self, mock_requests):
        mock_requests.get.return_value = _mock_response([])
        mock_requests.HTTPError = Exception

        args = _make_args(filter="", project_id=None, label="school")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.list_tasks(args)
        call_kwargs = mock_requests.get.call_args
        self.assertEqual(call_kwargs.kwargs.get("params", {}).get("label"), "school")


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------
class TestGetTask(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_get_task_success(self, mock_requests):
        task = {
            "id": "123",
            "content": "Write report",
            "description": "Q1 summary",
            "due": {"date": "2026-03-16", "datetime": "2026-03-16T10:00:00Z", "string": "Mar 16 10am", "timezone": "UTC", "is_recurring": False},
            "duration": {"amount": 60, "unit": "minute"},
            "priority": 3,
            "project_id": "456",
            "labels": ["work"],
            "url": "https://todoist.com/showTask?id=123",
        }
        mock_requests.get.return_value = _mock_response(task)
        mock_requests.HTTPError = Exception

        args = _make_args(task_id="123")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.get_task(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["id"], "123")
        self.assertEqual(output["duration"]["amount"], 60)
        self.assertEqual(output["priority"], 3)


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------
class TestCreateTask(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_create_task_basic(self, mock_requests):
        created = {
            "id": "999",
            "content": "New task",
            "description": "",
            "due": None,
            "duration": None,
            "priority": 1,
            "project_id": "456",
            "labels": [],
            "url": "https://todoist.com/showTask?id=999",
        }
        mock_requests.post.return_value = _mock_response(created)
        mock_requests.HTTPError = Exception

        args = _make_args(
            content="New task", description="", due_datetime=None,
            due_string=None, due_date=None, duration=None,
            project_id=None, priority=None, labels=None, deadline=None,
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.create_task(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["content"], "New task")
        # Verify POST body
        call_kwargs = mock_requests.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        self.assertEqual(body["content"], "New task")
        self.assertNotIn("duration", body)

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_create_task_with_duration(self, mock_requests):
        created = {
            "id": "999",
            "content": "Study math",
            "description": "",
            "due": {"date": "2026-03-16", "datetime": "2026-03-16T10:00:00Z", "string": "", "timezone": "", "is_recurring": False},
            "duration": {"amount": 90, "unit": "minute"},
            "priority": 3,
            "project_id": "456",
            "labels": ["school"],
            "url": "",
        }
        mock_requests.post.return_value = _mock_response(created)
        mock_requests.HTTPError = Exception

        args = _make_args(
            content="Study math", description="", due_datetime="2026-03-16T10:00:00Z",
            due_string=None, due_date=None, duration=90,
            project_id=None, priority=3, labels="school", deadline=None,
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.create_task(args)
        # Verify POST body has duration and duration_unit
        call_kwargs = mock_requests.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        self.assertEqual(body["duration"], 90)
        self.assertEqual(body["duration_unit"], "minute")
        self.assertEqual(body["due_datetime"], "2026-03-16T10:00:00Z")
        self.assertEqual(body["priority"], 3)
        self.assertEqual(body["labels"], ["school"])

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_create_task_with_labels_split(self, mock_requests):
        created = {"id": "999", "content": "t", "description": "", "due": None, "duration": None, "priority": 1, "project_id": "", "labels": ["a", "b"], "url": ""}
        mock_requests.post.return_value = _mock_response(created)
        mock_requests.HTTPError = Exception

        args = _make_args(
            content="t", description="", due_datetime=None,
            due_string=None, due_date=None, duration=None,
            project_id=None, priority=None, labels="a, b", deadline=None,
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.create_task(args)
        call_kwargs = mock_requests.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        self.assertEqual(body["labels"], ["a", "b"])

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_create_task_with_deadline(self, mock_requests):
        created = {"id": "999", "content": "t", "description": "", "due": None, "duration": None, "priority": 1, "project_id": "", "labels": [], "url": ""}
        mock_requests.post.return_value = _mock_response(created)
        mock_requests.HTTPError = Exception

        args = _make_args(
            content="t", description="", due_datetime=None,
            due_string=None, due_date=None, duration=None,
            project_id=None, priority=None, labels=None, deadline="2026-03-20",
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.create_task(args)
        call_kwargs = mock_requests.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        self.assertEqual(body["deadline"], {"date": "2026-03-20"})

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_create_task_with_due_string(self, mock_requests):
        created = {"id": "999", "content": "t", "description": "", "due": None, "duration": None, "priority": 1, "project_id": "", "labels": [], "url": ""}
        mock_requests.post.return_value = _mock_response(created)
        mock_requests.HTTPError = Exception

        args = _make_args(
            content="t", description="", due_datetime=None,
            due_string="tomorrow at 2pm", due_date=None, duration=None,
            project_id=None, priority=None, labels=None, deadline=None,
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.create_task(args)
        call_kwargs = mock_requests.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        self.assertEqual(body["due_string"], "tomorrow at 2pm")
        self.assertNotIn("due_datetime", body)


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------
class TestUpdateTask(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_update_task_duration(self, mock_requests):
        updated = {"id": "123", "content": "t", "description": "", "due": None, "duration": {"amount": 45, "unit": "minute"}, "priority": 1, "project_id": "", "labels": [], "url": ""}
        mock_requests.post.return_value = _mock_response(updated)
        mock_requests.HTTPError = Exception

        args = _make_args(
            task_id="123", content=None, description=None,
            due_datetime=None, due_string=None, due_date=None,
            duration=45, project_id=None, priority=None, labels=None, deadline=None,
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.update_task(args)
        call_kwargs = mock_requests.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        self.assertEqual(body["duration"], 45)
        self.assertEqual(body["duration_unit"], "minute")

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_update_task_no_fields_exits(self, mock_requests):
        args = _make_args(
            task_id="123", content=None, description=None,
            due_datetime=None, due_string=None, due_date=None,
            duration=None, project_id=None, priority=None, labels=None, deadline=None,
        )
        with self.assertRaises(SystemExit):
            todoist_api.update_task(args)


# ---------------------------------------------------------------------------
# complete_task
# ---------------------------------------------------------------------------
class TestCompleteTask(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_complete_task_success(self, mock_requests):
        mock_requests.post.return_value = _mock_response(None, 204)
        mock_requests.HTTPError = Exception

        args = _make_args(task_id="123")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.complete_task(args)
        output = json.loads(buf.getvalue())
        self.assertTrue(output["success"])
        self.assertEqual(output["task_id"], "123")


# ---------------------------------------------------------------------------
# delete_task
# ---------------------------------------------------------------------------
class TestDeleteTask(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_delete_task_success(self, mock_requests):
        mock_requests.delete.return_value = _mock_response(None, 204)
        mock_requests.HTTPError = Exception

        args = _make_args(task_id="123")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.delete_task(args)
        output = json.loads(buf.getvalue())
        self.assertTrue(output["success"])
        self.assertTrue(output["deleted"])


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------
class TestListProjects(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_list_projects_success(self, mock_requests):
        projects = [
            {"id": "100", "name": "Inbox", "color": "grey", "is_inbox_project": True, "is_favorite": False, "order": 0},
            {"id": "200", "name": "School", "color": "blue", "is_inbox_project": False, "is_favorite": True, "order": 1},
        ]
        mock_requests.get.return_value = _mock_response(projects)
        mock_requests.HTTPError = Exception

        args = _make_args()
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.list_projects(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0]["name"], "Inbox")
        self.assertTrue(output[0]["is_inbox_project"])


# ---------------------------------------------------------------------------
# list_labels
# ---------------------------------------------------------------------------
class TestListLabels(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_list_labels_success(self, mock_requests):
        labels = [
            {"id": "10", "name": "school", "color": "blue", "order": 1, "is_favorite": False},
            {"id": "20", "name": "work", "color": "red", "order": 2, "is_favorite": True},
        ]
        mock_requests.get.return_value = _mock_response(labels)
        mock_requests.HTTPError = Exception

        args = _make_args()
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.list_labels(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0]["name"], "school")
        self.assertEqual(output[1]["name"], "work")


# ---------------------------------------------------------------------------
# get_scheduled
# ---------------------------------------------------------------------------
class TestGetScheduled(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    @patch.dict(os.environ, {"TZ": "UTC"})
    def test_get_scheduled_with_gaps(self, mock_requests):
        """Tasks at 09:00-09:30 and 11:00-12:00 should produce gaps."""
        import time
        time.tzset()
        tasks = [
            {
                "id": "1",
                "content": "Morning standup",
                "description": "",
                "due": {"date": "2026-03-16", "datetime": "2026-03-16T09:00:00+00:00", "string": "", "timezone": "UTC", "is_recurring": False},
                "duration": {"amount": 30, "unit": "minute"},
                "priority": 2,
                "project_id": "",
                "labels": ["work"],
                "url": "",
            },
            {
                "id": "2",
                "content": "Code review",
                "description": "",
                "due": {"date": "2026-03-16", "datetime": "2026-03-16T11:00:00+00:00", "string": "", "timezone": "UTC", "is_recurring": False},
                "duration": {"amount": 60, "unit": "minute"},
                "priority": 3,
                "project_id": "",
                "labels": ["work", "coding"],
                "url": "",
            },
        ]
        mock_requests.get.return_value = _mock_response(tasks)
        mock_requests.HTTPError = Exception

        args = _make_args(date="2026-03-16", working_hours="08:00-22:00")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.get_scheduled(args)

        output = json.loads(buf.getvalue())
        self.assertEqual(output["date"], "2026-03-16")
        self.assertEqual(len(output["scheduled_tasks"]), 2)
        self.assertEqual(output["scheduled_tasks"][0]["content"], "Morning standup")
        self.assertEqual(output["scheduled_tasks"][1]["content"], "Code review")
        # Should have gaps: 08:00-09:00, 09:30-11:00, 12:00-22:00
        self.assertEqual(len(output["available_gaps"]), 3)
        # Total scheduled should be 90 minutes
        self.assertEqual(output["total_scheduled_minutes"], 90)

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_get_scheduled_no_tasks(self, mock_requests):
        """Empty day should produce one gap covering full working hours."""
        mock_requests.get.return_value = _mock_response([])
        mock_requests.HTTPError = Exception

        args = _make_args(date="2026-03-16", working_hours="08:00-22:00")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.get_scheduled(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(len(output["scheduled_tasks"]), 0)
        self.assertEqual(len(output["available_gaps"]), 1)
        self.assertEqual(output["available_gaps"][0]["start"], "08:00")
        self.assertEqual(output["available_gaps"][0]["end"], "22:00")
        self.assertEqual(output["available_gaps"][0]["duration_minutes"], 840)
        self.assertEqual(output["total_available_minutes"], 840)
        self.assertEqual(output["total_scheduled_minutes"], 0)

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_get_scheduled_unscheduled_tasks(self, mock_requests):
        """Tasks with date but no datetime should appear in unscheduled_tasks."""
        tasks = [
            {
                "id": "789",
                "content": "Buy groceries",
                "description": "",
                "due": {"date": "2026-03-16", "datetime": "", "string": "Mar 16", "timezone": "", "is_recurring": False},
                "duration": None,
                "priority": 1,
                "project_id": "",
                "labels": [],
                "url": "",
            }
        ]
        mock_requests.get.return_value = _mock_response(tasks)
        mock_requests.HTTPError = Exception

        args = _make_args(date="2026-03-16", working_hours="08:00-22:00")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.get_scheduled(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(len(output["scheduled_tasks"]), 0)
        self.assertEqual(len(output["unscheduled_tasks"]), 1)
        self.assertEqual(output["unscheduled_tasks"][0]["content"], "Buy groceries")

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    def test_get_scheduled_custom_working_hours(self, mock_requests):
        """Custom working hours should change gap boundaries."""
        mock_requests.get.return_value = _mock_response([])
        mock_requests.HTTPError = Exception

        args = _make_args(date="2026-03-16", working_hours="10:00-18:00")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.get_scheduled(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["working_hours"]["start"], "10:00")
        self.assertEqual(output["working_hours"]["end"], "18:00")
        self.assertEqual(output["available_gaps"][0]["duration_minutes"], 480)

    @patch.object(todoist_api, "TODOIST_API_TOKEN", "tok")
    @patch("todoist_api.requests")
    @patch.dict(os.environ, {"TZ": "UTC"})
    def test_get_scheduled_no_duration_defaults_30(self, mock_requests):
        """Tasks with datetime but no duration should default to 30 min."""
        import time
        time.tzset()
        tasks = [
            {
                "id": "1",
                "content": "Quick call",
                "description": "",
                "due": {"date": "2026-03-16", "datetime": "2026-03-16T10:00:00+00:00", "string": "", "timezone": "UTC", "is_recurring": False},
                "duration": None,
                "priority": 1,
                "project_id": "",
                "labels": [],
                "url": "",
            }
        ]
        mock_requests.get.return_value = _mock_response(tasks)
        mock_requests.HTTPError = Exception

        args = _make_args(date="2026-03-16", working_hours="08:00-22:00")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            todoist_api.get_scheduled(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(len(output["scheduled_tasks"]), 1)
        self.assertEqual(output["scheduled_tasks"][0]["duration_minutes"], 30)


# ---------------------------------------------------------------------------
# config check
# ---------------------------------------------------------------------------
class TestConfigCheck(unittest.TestCase):
    @patch.object(todoist_api, "TODOIST_API_TOKEN", "")
    def test_missing_token_exits(self):
        with self.assertRaises(SystemExit):
            todoist_api._check_config()


# ---------------------------------------------------------------------------
# helper functions
# ---------------------------------------------------------------------------
class TestHelpers(unittest.TestCase):
    def test_parse_working_hours(self):
        sh, sm, eh, em = todoist_api._parse_working_hours("08:00-22:00")
        self.assertEqual((sh, sm, eh, em), (8, 0, 22, 0))

    def test_parse_working_hours_custom(self):
        sh, sm, eh, em = todoist_api._parse_working_hours("09:30-17:45")
        self.assertEqual((sh, sm, eh, em), (9, 30, 17, 45))

    def test_time_to_minutes(self):
        self.assertEqual(todoist_api._time_to_minutes(8, 0), 480)
        self.assertEqual(todoist_api._time_to_minutes(22, 0), 1320)
        self.assertEqual(todoist_api._time_to_minutes(0, 0), 0)

    def test_minutes_to_time(self):
        self.assertEqual(todoist_api._minutes_to_time(480), "08:00")
        self.assertEqual(todoist_api._minutes_to_time(1320), "22:00")
        self.assertEqual(todoist_api._minutes_to_time(0), "00:00")
        self.assertEqual(todoist_api._minutes_to_time(615), "10:15")


if __name__ == "__main__":
    unittest.main()
