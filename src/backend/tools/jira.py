import os
import requests
from typing import Any, Dict
from pydantic import BaseModel, Field
from backend.tools.base import BaseTool
from backend.schemas.tool import ToolDefinition

class JiraCreateIssueInput(BaseModel):
    summary: str = Field(..., description="A concise summary or title for the Jira ticket/bug report.")
    description: str = Field(..., description="Detailed description of the issue or task details.")
    issue_type: str = Field(default="Task", description="Type of issue in Jira. Examples: 'Bug', 'Task'.")
    priority: str = Field(default="Medium", description="Priority level. Options: 'Low', 'Medium', 'High'.")

class JiraTool(BaseTool):
    """ToolGen Tool: Enables LLM agents to autonomously create tickets in Jira."""
    
    ID = "jira_create_issue"
    NAME = "jira_create_issue"
    DESCRIPTION = "Creates a new issue or bug ticket in Jira for engineering or product tracking."
    
    is_available = True
    is_visible = True
    auth_implementation = None
    args_schema = JiraCreateIssueInput

    @classmethod
    def get_tool_definition(cls) -> ToolDefinition:
        return ToolDefinition(
            name=cls.ID,
            display_name="Jira Create Issue",
            description=cls.DESCRIPTION,
            implementation=cls,
            is_available=cls.is_available,
            is_visible=cls.is_visible,
            auth_implementation=cls.auth_implementation,
            parameter_definitions={
                "summary": {
                    "description": "A concise summary or title for the Jira ticket/bug report.",
                    "type": "str",
                    "required": True,
                },
                "description": {
                    "description": "Detailed description of the issue or task details.",
                    "type": "str",
                    "required": True,
                },
                "issue_type": {
                    "description": "Type of issue in Jira. Examples: 'Bug', 'Task'.",
                    "type": "str",
                    "required": False,
                },
                "priority": {
                    "description": "Priority level. Options: 'Low', 'Medium', 'High'.",
                    "type": "str",
                    "required": False,
                },
            },
        )

    def __init__(self):
        super().__init__()
        self.jira_domain = os.getenv("JIRA_DOMAIN", "https://your-domain.atlassian.net")
        self.jira_email = os.getenv("JIRA_EMAIL")
        self.jira_api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "TOOLGEN")

    # ADDED 'async' HERE
    async def call(self, parameters: Dict[str, Any], **kwargs: Any) -> Any:
        try:
            validated_input = JiraCreateIssueInput(**parameters)
        except Exception as e:
            return [{"status": "error", "message": f"Invalid tool arguments: {str(e)}"}]

        if not self.jira_email or not self.jira_api_token:
            # Wrapped in a list
            return [{
                "status": "success",
                "issue_url": f"{self.jira_domain.rstrip('/')}/browse/MOCK-123",
                "message": f"MOCK SUCCESS: Jira ticket '{validated_input.summary}' created successfully (Add real credentials to .env to execute API)."
            }]

        url = f"{self.jira_domain.rstrip('/')}/rest/api/3/issue"
        auth = (self.jira_email, self.jira_api_token)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": validated_input.summary,
                "issuetype": {"name": validated_input.issue_type},
                "priority": {"name": validated_input.priority},
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": validated_input.description}]}]
                }
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
            if response.status_code == 201:
                issue_key = response.json().get("key")
                return [{
                    "status": "success",
                    "issue_url": f"{self.jira_domain.rstrip('/')}/browse/{issue_key}",
                    "message": f"Successfully created Jira ticket {issue_key}."
                }]
            
            # Properly return actual API errors
            return [{"status": "error", "status_code": response.status_code, "message": response.text}]
        except requests.RequestException as e:
            # Properly return network/connection errors
            return [{"status": "error", "message": str(e)}]