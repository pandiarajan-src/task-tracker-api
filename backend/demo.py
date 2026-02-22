#!/usr/bin/env python3
"""
Task Tracker API Demo Script

This script demonstrates how to interact with the Task Tracker API.
Make sure the API server is running before executing this script.
"""

import requests
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"


def create_task(title: str, description: str = None, completed: bool = False) -> Dict[Any, Any]:
    """Create a new task."""
    data = {"title": title, "completed": completed}
    if description:
        data["description"] = description
    
    response = requests.post(f"{API_BASE_URL}/tasks", json=data)
    response.raise_for_status()
    return response.json()


def get_all_tasks() -> list:
    """Get all tasks."""
    response = requests.get(f"{API_BASE_URL}/tasks")
    response.raise_for_status()
    return response.json()


def get_task(task_id: int) -> Dict[Any, Any]:
    """Get a specific task by ID."""
    response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()


def update_task(task_id: int, **updates) -> Dict[Any, Any]:
    """Update a task."""
    response = requests.put(f"{API_BASE_URL}/tasks/{task_id}", json=updates)
    response.raise_for_status()
    return response.json()


def delete_task(task_id: int) -> Dict[Any, Any]:
    """Delete a task."""
    response = requests.delete(f"{API_BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()


def main():
    """Demonstrate API usage."""
    print("🚀 Task Tracker API Demo")
    print("=" * 30)
    
    try:
        # Test API connection
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✅ API is running: {response.json()['message']}")
        
        # Create tasks
        print("\n📝 Creating tasks...")
        task1 = create_task("Buy groceries", "Milk, bread, eggs")
        task2 = create_task("Write documentation", "Complete the API documentation", False)
        task3 = create_task("Review code", None, False)
        
        print(f"Created task: {task1['title']} (ID: {task1['id']})")
        print(f"Created task: {task2['title']} (ID: {task2['id']})")
        print(f"Created task: {task3['title']} (ID: {task3['id']})")
        
        # Get all tasks
        print("\n📋 All tasks:")
        tasks = get_all_tasks()
        for task in tasks:
            status = "✅" if task['completed'] else "⏳"
            print(f"  {status} {task['title']} (ID: {task['id']})")
        
        # Update a task
        print(f"\n✏️ Marking task {task1['id']} as completed...")
        updated_task = update_task(task1['id'], completed=True)
        print(f"Updated: {updated_task['title']} -> Completed: {updated_task['completed']}")
        
        # Get specific task
        print(f"\n🔍 Getting task {task2['id']}:**")
        specific_task = get_task(task2['id'])
        print(f"Task: {specific_task['title']}")
        print(f"Description: {specific_task['description']}")
        print(f"Completed: {specific_task['completed']}")
        
        # Delete a task
        print(f"\n🗑️ Deleting task {task3['id']}...")
        delete_result = delete_task(task3['id'])
        print(f"Result: {delete_result['message']}")
        
        # Final task list
        print("\n📋 Final task list:")
        final_tasks = get_all_tasks()
        if final_tasks:
            for task in final_tasks:
                status = "✅" if task['completed'] else "⏳"
                print(f"  {status} {task['title']} (ID: {task['id']})")
        else:
            print("  No tasks remaining")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("   Make sure the server is running: uv run uvicorn main:app --reload")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()