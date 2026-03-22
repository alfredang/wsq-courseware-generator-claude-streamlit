"""CP Interpreter — Extract structured course data from Course Proposals.

Shared by all generation workflows. Uses Claude Agent SDK with Read tool.
"""

from courseware_agents.cp_interpreter.cp_interpreter import interpret_cp

__all__ = ["interpret_cp"]
