from langchain.tools import tool, ToolRuntime
from memory.memory import Memory
import os
from typing import Dict, Literal
from schemas import Todo, NextTodo
from executor import execute


agent_todos = []

# todo write tool to write the entire todos to the list
@tool
def todo_write(todos: list[Dict[str, str]]):
    """
    Write the entire todos to the list intially when starting a new task.

    When to use:
        - Initialize a new todo list at the start of a complex task.
        - Break down a large task into manageable subtasks.

    When NOT to use:
        - To mark a single task as complete (use todo_next instead).
        - To add one task to existing list (overwrite entire list).

    Examples:
        >>> todo_write([{"subtask": "Parse input", "status": "pending"}, 
                        {"subtask": "Process data", "status": "pending"}])
        >>> todo_write([{"subtask": "Research API docs", "status": "pending"},
                        {"subtask": "Implement auth", "status": "pending"},
                        {"subtask": "Write tests", "status": "pending"}])
    Args:
        todos (list[Dict[str, str]]): Complete list of Todo objects to store.

    Returns:
        str: Confirmation message of successful write.
    """
    global agent_todos

    agent_todos = todos  # Update the global todos variable with the provided list

    return "Todo list saved successfully"


# function to get the next todo item
@tool
def todo_next(completed_subtask:Dict[str, str] = None, intial_todo: bool = False):
    """
    Mark a subtask as completed and retrieve the next pending todo item.

    When to use:
        - To start processing the first todo item when beginning a new task, use --> todo_next(intial_todo=True).
        - After completing a subtask, to progress to the next one.
        - Track progress through a multi-step task.
        - Maintain sequential execution of planned tasks.

    When NOT to use:
        - When no todos have been created yet (use todo_write first).
        - To view all todos without marking completion (read /todos/todos.txt).

    Examples:
        >>> todo_next(intial_todo=True) # Get the first todo item only
        >>> todo_next(completed_subtask={"subtask": "Parse input", "status": "completed"})
        >>> todo_next(completed_subtask={"subtask": "Research API docs", "status": "completed"})

    Args:
        completed_subtask (Dict[str, str]): The Todo object that has been completed.
        intial_todo (bool): Flag to indicate retrieval of the first todo item only.
    Returns:
        NextTodo: Object with fields (subtask, instructions) for next pending task.
    """

    global agent_todos  # Access the global todos variable

    if intial_todo:
        if not agent_todos:
            return "No todos found. Please write todos first using todo_write tool."
        return NextTodo(
            subtask = agent_todos[0]["subtask"],
            instructions = "This is the first todo item to be addressed."
        )

    #check if todos exist
    if not agent_todos:
        return "No todos found. Please write todos first using todo_write tool."
    #mark the given subtask as completed
    todo_next = 0
    for todo in agent_todos:
        todo_next += 1
        if todo["subtask"] == completed_subtask["subtask"]:
            todo["status"] = "completed"
            break
    #get the next pending todo  
    if todo_next < len(agent_todos):
        return NextTodo(
            subtask = agent_todos[todo_next]["subtask"],
            instructions = "This is the next todo item to be addressed.")
    else:
        return NextTodo(
            subtask = "All todos are completed.",
            instructions = "No more pending todo items.")      



Workspace = os.path.join(os.getcwd(), "workspace")

@tool
def read_file(path:str, start_line:int =0, no_lines:int = None) -> str:
    
    """
    Read the content of a file at the specified path.

    When to use:
        - Access previously created files for inspection or modification.
        - Read configuration files or data needed for current task.
        - Verify content of files created in earlier steps.

    When NOT to use:
        - When you need to list files in a directory (use list_files instead).
        - When searching for specific patterns (use grep instead).

    Examples:
        >>> file_read("/project/hello.py")
        >>> file_read("/project/settings.json")
        >>> file_read("/project/results.csv")
        >>> file_read("/project/memory")

    Args:
        path (str): The path to the file to be read.
        start_line (int): The line number to start reading from (default: 0).
        no_lines (int|None): The number of lines to read (default: None, which means read until the end of the file).

    Returns:
            str: The content of the file from the specified start line and for the specified number of lines.
    """
    try:
        actual_path = os.path.join(Workspace, path)

        with open(actual_path, 'r') as f:
            lines = f.readlines()
            limit = min(no_lines + start_line,len(lines)) if no_lines else None

        selected_lines = lines[start_line:limit] if limit else lines[start_line:]

        formatted_lines = []
        for i, line in enumerate(selected_lines, start=1):
            formatted_lines.append(f"{i:6}\t{line}")

        content = "".join(formatted_lines)

        return f"content: {content}"

    except Exception as e:
        return f"Error reading file path: {path}"



@tool
def write_file(path:str, content:str = "") -> str:
    """
    Write content to a file at the specified path.

    when to use:
        - This tool will overwrite the existing file if there is one at the provided path.
        - If this is an existing file, you MUST use the read_file tool first to read the file's contents. This tool will fail if you did not read the file first.
        - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
        - NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

    when not to use:
        - When you need to change partially to an existing file (use edit_file instead).

    Examples:
        >>> file_write("index.html", "<html><body><h1>Welcome</h1></body></html>")
        >>> file_write("styles.css", "body { background-color: lightblue; }")
        >>> file_write("script.js", "console.log('Hello, World!');")

        >>> file_write("main.py", "print('Hello, World!')")
        >>> file_write("project/hello.py", "print('Hello, World!')")
        >>> file_write("project/settings.json", '{"debug": true, "version": "1.0.0"}')
        
            
    Args:
        path (str): The path where the content file should be created or overwritten.
        content (str): The content to be written to the file (default: empty string).

    """

    try:
        actual_path = os.path.join(Workspace, path)

        with open(actual_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"content successfully written to specified file path: {path}"
    except Exception as e:
        return f"Error writing to file path: {path}"



def edit_file(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> dict:

    """
    Performs exact string replacements in files.

    when to use:
        - You must use your `read_file` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. 
        - When editing text from read_file tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.
        - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
        - The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`. 
        - Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.
    
    when not to use:
        - When you need to write new content to a file without modifying existing content (use write_file instead).
        - When there are multiple identical strings in the file and you only want to replace one of them without providing additional context to make it unique.
    
    Args:
        file_path (str): The absolute path to the file to modify
        old_string (str): The text to replace
        new_string (str): The text to replace it with
        replace_all (bool|False): Replace all occurrences of old_string (default False)
    
    Returns:
        dict: Status of the operation with details
    """
    try:
        # Read the file
        actual_path = os.path.join(Workspace, file_path)
        with open(actual_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if old_string exists in file
        if old_string not in content:
            return {
                "success": False,
                "error": f"String not found in file: {file_path}"
            }
        
        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            count = content.count(old_string)
        else:
            # Check uniqueness if not replace_all
            if content.count(old_string) > 1:
                return {
                    "success": False,
                    "error": "String is not unique in file. provide more surrounding context to make it unique."
                }
            new_content = content.replace(old_string, new_string, 1)
            count = 1
        
        # Write back to file
        with open(actual_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "success": True,
            "message": f"Successfully replaced {count} occurrence(s)",
        }
    
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"An error occurred: at file path {file_path}"
        }



@tool
def list_files(directory: str = "") -> list:

    """
    Lists files and directories in the specified directory.
    
    Args:
        directory: The directory to list (default is current directory)

    """
    
    try:
        path = os.path.join(Workspace, directory)
        items = os.listdir(path)
        return f"Items in directory': {items}"
    except Exception as e:
        return f"Error listing directory: {directory}"


@tool
def make_directory(path: str) -> str:
    """
    Creates a new directory at the specified path.

    Args:
        path: The path to the new directory to create
    """
    try:
        full_path = os.path.join(Workspace, path)
        os.makedirs(full_path, exist_ok=True)
        return f"Directory created successfully at: {path}"
    except Exception as e:
        return f"Error creating directory: path {path}"



@tool
def grep(file_path: str, search_string: str) -> list:
    """
    Searches for a specific string in a file and returns the lines containing it.
    
    Args:
        file_path: The absolute path to the file to search
        search_string: The string to search for
    
    Returns:
        list: Lines containing the search string
    """
    try:
        actual_path = os.path.join(Workspace, file_path)
        with open(actual_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        matching_lines = [line for line in lines if search_string in line]
        return f"Matching lines in file : {matching_lines}"
    
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"An error occurred: at path {file_path}"


@tool
def glob(pattern:str, directory:str = "") -> list:
    """
    Finds files matching a specific pattern in a directory.
    
    Args:
        pattern: The glob pattern to match (e.g., '*.py' for Python files)
        directory: The directory to search in (default is current directory)
    
    Returns:
        list: Files matching the glob pattern
    """
    try:
        import glob as glob_module
        path = os.path.join(Workspace, directory, pattern)
        matching_files = glob_module.glob(path)
        return f"Matching files in directory with pattern {pattern}: {matching_files}"
    except Exception as e:
        return f"Error performing glob search: at directory {directory} with pattern {pattern}"


@tool
def get_human_feedback():
    """
    Get human feedback for the agent's execution through the UI.
    
    This tool triggers a popup modal in the UI asking for human feedback.
    The user can either provide feedback or reject the request.

    When to use this tool:
    1. When the agent is stuck and cannot make progress, it can use this tool to ask for human feedback to get unstuck.
    2. When the agent is unsure about the next step to take, it can use this tool to ask for human feedback to get guidance on the next step.
    3. Immediately after the agent completes a todo item, it can use this tool to ask for human feedback on the completed item to get feedback on whether it was done correctly or if there are any improvements that can be made.
    4. When the agent fails to complete a todo item, it can use this tool to ask for human feedback on the failed item to get feedback on what went wrong and how to fix it.

    When NOT to use this tool:
    1. When the agent is making good progress and does not need any help, it should not use this tool to ask for human feedback, as it may interrupt the agent's flow and cause unnecessary delays.
    2. When the agent is confident about the next step to take and does not need any guidance, it should not use this tool to ask for human feedback, as it may waste time and resources on unnecessary feedback.

    Args:
        None

    Returns:
        str: The human feedback provided by the user formatted with reflection prompts.
    """
    
    # Import the request function from feedback_manager (avoids circular import)
    try:
        from feedback_manager import request_feedback_from_ui
        response = request_feedback_from_ui()
        
        feedback = response.get("feedback", "")
        accepted = response.get("accepted", False)
        
        #if not accepted:
            #return "Human feedback request was rejected. Continue with your best judgment."
            
    except Exception as e:
        # Fallback to terminal input if UI is not available
        feedback = input("Please provide feedback: ")

    without_feedback_prompt = """reflect upon the process and execution so far, and call memorization tool if there are any important insights, learning, failures, edge cases, constraints discovered or architectural decisions made.
    Also, if there is any important information that should be remembered for future use, call the memorization tool to store that information in the memory."""
    
    with_feedback_prompt = """reflect upon the process and execution so far independently of the feedback, and then reflect on the human feedback provided. If there are any important insights, learning, failures, edge cases, constraints discovered or architectural decisions, preferences made based on the feedback or in general, 
    Also, if there is any important information that should be remembered for future use based on the feedback or in general upon the agent independent of the feedback, call the memorization tool to store that information in the memory."""

    forced_prompt = ""
    
    # Format the feedback based on the without_feedback_prompt and with_feedback_prompt
    if accepted and feedback.strip():
        forced_prompt = f"{with_feedback_prompt} Here is the human feedback: {feedback}"
    else:
        forced_prompt = f"{without_feedback_prompt}"
    
    return forced_prompt




memory_system = Memory()

@tool
def memorization(coding_knowledge: str = None, architectural_decisions: str = None, preferences: str = None, observations: str = None, insights: str = None, constraints_discovery: str = None, edges_cases_discovery: str = None, failures: str = None):

    """
    This tool is used to store structured learning extracted from the agent’s reasoning after completing a TODO or encountering an error.
    It enables reflective learning and supports consolidation into short-term memory for future recollection.

    It must be called:
    - After completing each TODO (reflection phase)
    - Immediately after any failure or unexpected behavior
    - After receiving meaningful human feedback
    - After discovering new constraints, insights, or edge cases


    IMPORTANT:
    The goal of this tool is structured reflection and consolidation — not logging raw execution traces or trivial successes.
    The agent must only provide the memory components that are relevant to the current context. 
    Only provide arguments that are relevant to the current situation.
    Do NOT populate all fields.
    If a category is not applicable, leave it as None.

    When to use this tool:
        - A new reusable coding pattern is learned
        - An architectural decision is finalized or revised
        - A human provides preference or correction
        - An important observation is made
        - A root cause insight is discovered
        - A new constraint is identified
        - An edge case is discovered
        - A failure occurs and its cause is understood

    When NOT to use this tool:
        - A TODO completes without any new learning
        - Minor or obvious steps were executed
        - No new insight, failure, or constraint emerged
        - Information is purely temporary or session-specific noise

        
    Examples:

        Example 1
        Situation: The agent encountered a runtime error due to missing `await` in an async function and fixed it.

        >>> memorization(
                failures="Async function result used without await caused runtime error.",
                insights="Missing await in async workflows leads to Promise object misuse.",
                coding_knowledge="Always await async function calls before using returned value."
            )

        Example 2
        Situation: The human specifies that the project must use Python 3.8 and avoid newer syntax features.

        >>> memorization(
                constraints_discovery="Environment restricted to Python 3.8.",
                preferences="Avoid Python 3.10+ syntax features such as match-case."
            )


        Example 3
        Situation:The agent decides to introduce a repository layer to decouple database logic from business logic.

        >>> memorization(
                architectural_decisions="Introduced repository layer to decouple database operations from service logic.",
                insights="Layered architecture improves maintainability and testability."
            )


        Example 4
        Situation: An edge case was discovered where empty input caused a crash.

        >>> memorization(
                edges_cases_discovery="Empty list input caused IndexError in processing loop.",
                coding_knowledge="Always validate input length before accessing list elements."
            )

    Args:
        coding_knowledge (str | None): Generalizable coding patterns, reusable fixes, or technical lessons learned.

        architectural_decisions (str | None): Architectural choices made, revised, or reinforced.

        preferences (str | None): Human preferences or coding style guidance that should influence future behavior.

        observations (str | None): High-signal runtime observations such as errors, unexpected behavior, or metrics.

        insights (str | None): Root cause analysis, abstracted lessons, or conceptual understanding gained.

        constraints_discovery (str | None): Newly discovered constraints related to environment, performance, security, or deployment.

        edges_cases_discovery (str | None): Newly identified edge cases or boundary conditions.

        failures (str | None): Clear description of encountered failures and their impact.

    Important:
        - do not use null for arguments that are not applicable, simply leave them as None or do not provide them at all when calling the tool.
        - only provide the relevant arguments that are applicable to the current situation. Do not populate all.

    Returns:
        None
    """

    

    memory_headings = {
        "coding_knowledge": "Coding Knowledge",
        "architectural_decisions": "Architectural Decisions",
        "preferences": "Preferences",
        "observations": "Observations",
        "insights": "Insights",
        "constraints_discovery": "Constraints Discovery",
        "edges_cases_discovery": "Edges Cases Discovery",
        "failures": "Failures"
    }


    memory_abstractions = [coding_knowledge, architectural_decisions, preferences, observations, insights, constraints_discovery, edges_cases_discovery, failures]

    #name associations or details and some context at the memory associations variable.
    memory_associations = ""

    for i in range(len(memory_abstractions)):
        if memory_abstractions[i] is not None:
            memory_associations += f"#{memory_headings[list(memory_headings.keys())[i]]} -{ memory_abstractions[i]}\n"

    #call memory(memory_associations) to store the important information in the memory
    response = memory_system.memorize(memory_associations)

    return f"memorization done you can retrieve the important information later when needed. Response from memory system: {response}"



@tool
def memory_recollection(memory_context: str):

    """
    This tool retrieves relevant structured memories from external memory
    based on the provided context.

    It is used before starting a new TODO, during planning, or when
    encountering uncertainty, failure, or architectural decisions.

    The purpose is to:
    - Prevent repeating past mistakes
    - Reuse prior successful strategies
    - Enforce discovered constraints
    - Adapt behavior based on similar past situations
    - Inject long-term lessons into current reasoning

    The input `memory_context` should clearly describe:
    - The current TODO or task
    - Relevant environment details
    - Frameworks or libraries involved
    - Error messages (if any)
    - Architectural area being modified
    - Any signals of uncertainty

    When to use this tool:
        - Before executing a new TODO
        - Before making architectural decisions
        - When using a framework previously associated with failures
        - After encountering an error
        - When performance, security, or constraints are involved
        - When human feedback previously modified similar logic

    When NOT to use this tool:
        - For trivial operations with no prior learning relevance
        - When no similar past context exists
        - For purely mechanical code generation steps

    Examples:

        Example 1
        Situation:The agent is about to implement async database calls.

        >>> memory_recollection(
                memory_context="Implementing async database access in FastAPI using Python 3.8"
            )

        Expected retrieval:
            - Past async-related failures
            - Missing await patterns
            - Version-related constraints
            - Reusable async fix patterns


        Example 2
        Situation: The agent encounters a LangChain-related error.

        >>> memory_recollection(
                memory_context="LangChain method call error in version 0.0.300"
            )

        Expected retrieval:
            - API hallucination failures
            - Version drift lessons
            - Verification procedural rules


        Example 3
        Situation: Planning system architecture for new project.

        >>> memory_recollection(
                memory_context="Designing backend architecture for scalable API with performance constraints"
            )

        Expected retrieval:
            - Past architecture decisions
            - Performance lessons
            - Strategy rules
            - Human global preferences

    Args:
        memory_context (str): A structured or descriptive summary of the current situation. This should include enough detail to allow relevant matching against stored short-term memory structured memories.

    Returns:
        Retrieved relevant memories appropriate to the current context.

    """

    #call memory.recall(memory_context) to retrieve the relevant information from the memory based on the provided context.

    retrieved_memories = memory_system.recall(memory_context)

    return retrieved_memories   #return the retrieved relevant memories appropriate to the current context.


@tool
def consolidate():
    """
    consolide all the findings of the short-term memory into the long-term memory after all the todos are completed. 
    This function should be called at the end of the execution of all the todos to consolidate the important information and learning into the long-term memory for future use.
    
    when to use:
        - After all the todos are completed and there is important information in the short-term memory that should be retained for future use.

    when not to use:
        - When there are still pending todos to be executed.
        - When there is no important information in the short-term memory that needs to be retained for future use.

    Args:
        None

    """

    memory_system.consolidate()

    return "Memory consolidation completed. Important information has been retained in long-term memory for future use."



def force_consolidate():

    memory_system.consolidate()





# executes only python and npm commands
@tool
def execute_command(command:str):
    """
    executes only python, pip and npm commands in the terminal and returns the output. It validates the command before execution to ensure it is either a python,pip or npm command.
    If the command is invalid, it returns an error message. If the command is valid but fails during execution, it returns the error message from the terminal.
    
    when to use:
        - When you need to execute a python, pip or npm command in the terminal and get the output.
        - When you need to run tests, scripts, or manage packages as part of your task execution.
        - to use pip use command starting with "python -m pip" to ensure it uses the correct python environment.

    when not to use:
        - When you need to execute commands that are not python, pip or npm related.
        - when you want to execute shell commands that are not related to python, pip or npm.
        - When you need to perform file operations, use the file tools instead.
        
        
    examples:
        >>> execute("python hello.py")
        >>> execute("python -m pip install requests")
        >>> execute("npm install express")
        >>> execute("ls -la") # This will return an error message as it is not a valid command for this tool.

    
    Args:        
        
        command (str): The command to be executed in the terminal which is of only python, pip or npm related.  

    Returns:
        str: The output from the terminal after executing the command or an error message if the command is invalid or fails during execution. 
    
    """

    output = execute(command)

    return output