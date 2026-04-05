from app.db.supabase import get_supabase
from app.db.models import TaskCreate, TaskResponse


async def create_task(task: TaskCreate) -> TaskResponse:
    """
    Create a new agent task in Supabase.
    Status starts as 'pending'.
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("tasks")
            .insert({
                "user_input": task.user_input,
                "status": "pending"
            })
            .execute()
        )

        data = response.data[0]
        return TaskResponse(**data)

    except Exception as e:
        raise Exception(f"Failed to create task: {str(e)}")


async def update_task_status(task_id: str, status: str) -> TaskResponse:
    """
    Update task status.
    Status flow: pending → running → completed | failed
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("tasks")
            .update({"status": status})
            .eq("id", task_id)
            .execute()
        )

        data = response.data[0]
        return TaskResponse(**data)

    except Exception as e:
        raise Exception(f"Failed to update task status: {str(e)}")


async def get_task(task_id: str) -> TaskResponse:
    """
    Fetch a single task by ID.
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("id", task_id)
            .single()
            .execute()
        )

        return TaskResponse(**response.data)

    except Exception as e:
        raise Exception(f"Failed to fetch task: {str(e)}")


async def get_all_tasks() -> list[TaskResponse]:
    """
    Fetch all tasks ordered by most recent.
    """
    supabase = get_supabase()

    try:
        response = (
            supabase.table("tasks")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return [TaskResponse(**task) for task in response.data]

    except Exception as e:
        raise Exception(f"Failed to fetch tasks: {str(e)}")