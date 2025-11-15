"""
Worker Agent Base Class
Implements the abstract base class for all worker agents in the multi-agent system.
Ensures protocol compliance and standardized LTM interface.
"""

from abc import ABC, abstractmethod
import json
import uuid
from typing import Any, Optional
from datetime import datetime


class AbstractWorkerAgent(ABC):
    """
    Abstract Base Class for all worker agents, including LTM functionality.
    All worker agents must inherit from this class and implement the abstract methods.
    """

    def __init__(self, agent_id: str, supervisor_id: str):
        """
        Initialize the worker agent.
        
        Args:
            agent_id: Unique identifier for this agent
            supervisor_id: ID of the supervisor agent
        """
        self._id = agent_id
        self._supervisor_id = supervisor_id
        self._current_task_id: Optional[str] = None

    # --- Abstract Methods (Must be Implemented by Subclasses) ---

    @abstractmethod
    def process_task(self, task_data: dict) -> dict:
        """
        The worker's unique business logic. Must return a dictionary of results.
        
        Args:
            task_data: Dictionary containing task parameters
            
        Returns:
            Dictionary with results, must include 'output' key for success
            
        Raises:
            Exception: Any exception will be caught and reported as FAILURE
        """
        pass

    @abstractmethod
    def send_message(self, recipient: str, message_obj: dict):
        """
        Sends the final JSON message object through the communication layer.
        
        Args:
            recipient: ID of the recipient agent
            message_obj: Complete message dictionary to send
        """
        pass
    
    @abstractmethod
    def write_to_ltm(self, key: str, value: Any) -> bool:
        """
        Writes a key-value pair to the agent's Long-Term Memory (LTM).
        
        Args:
            key: Unique key for storage (typically a hash of the input)
            value: Value to store (can be any serializable type)
            
        Returns:
            True on success, False otherwise
        """
        pass

    @abstractmethod
    def read_from_ltm(self, key: str) -> Optional[Any]:
        """
        Reads a value from the agent's LTM based on the key.
        
        Args:
            key: The key to look up
            
        Returns:
            The stored value or None if the key is not found
        """
        pass

    # --- Concrete Methods (Shared Communication Protocol) ---

    def handle_incoming_message(self, json_message: str):
        """
        Receives and processes an incoming JSON message from the supervisor.
        
        Args:
            json_message: JSON string containing the message
        """
        try:
            message = json.loads(json_message)
            msg_type = message.get("type")
            
            if msg_type == "task_assignment":
                task_params = message.get("task", {}).get("parameters", {})
                self._current_task_id = message.get("message_id")
                task_name = message.get("task", {}).get("name", "unknown")
                print(f"[{self._id}] received task: {task_name}")
                self._execute_task(task_params, self._current_task_id)
            else:
                print(f"[{self._id}] WARNING: Unknown message type: {msg_type}")
            
        except json.JSONDecodeError as e:
            print(f"[{self._id}] ERROR decoding message: {e}")
        except Exception as e:
            print(f"[{self._id}] ERROR handling message: {e}")

    def _execute_task(self, task_data: dict, related_msg_id: str):
        """
        Executes the concrete process_task logic and handles result reporting.
        
        Args:
            task_data: Dictionary containing task parameters
            related_msg_id: The message ID this execution relates to
        """
        status = "FAILURE"
        results = {}
        
        try:
            results = self.process_task(task_data)
            status = "SUCCESS"
        except Exception as e:
            results = {"error": str(e), "details": "Task processing failed."}
            print(f"[{self._id}] Task FAILED: {e}")
            
        self._report_completion(related_msg_id, status, results)

    def _report_completion(self, related_msg_id: str, status: str, results: dict):
        """
        Constructs and sends a task completion report.
        
        Args:
            related_msg_id: The message ID this report relates to
            status: "SUCCESS" or "FAILURE"
            results: Dictionary containing execution results or error details
        """
        report = {
            "message_id": str(uuid.uuid4()),
            "sender": self._id,
            "recipient": self._supervisor_id,
            "type": "completion_report",
            "related_message_id": related_msg_id,
            "status": status,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.send_message(self._supervisor_id, report)
        self._current_task_id = None

    # --- Helper Properties ---

    @property
    def agent_id(self) -> str:
        """Get the agent's ID."""
        return self._id

    @property
    def supervisor_id(self) -> str:
        """Get the supervisor's ID."""
        return self._supervisor_id

    @property
    def current_task_id(self) -> Optional[str]:
        """Get the current task ID being processed."""
        return self._current_task_id
