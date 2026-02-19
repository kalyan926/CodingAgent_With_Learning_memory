import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import create_agent
from .memory_prompts import MEMORY_SYSTEM_PROMPT, CONSOLIDATION_SYSTEM_PROMPT


# Load environment variables from a .env file
load_dotenv()


@tool
def read_file(relative_path: str) -> str:
    """
    Reads the content of a file present in specified relative path and returns it content.
    
    when to use:
    - When you need to access existing structured memory stored in files based on a relative path.
    - When you want to retrieve specific memory details based on a relative file path.

    example usage:
    - read_file("\short_term_memory\coding-knowledge.md") to access coding knowledge memory
    - read_file("\short_term_memory\observations.md") to access observations memory
    - read_file("\short_term_memory\architectural-decisions.md") to access architectural decisions memory

    Important:
    - Always use relative file paths in the format start with backslash followed by the folder name (e.g., \short_term_memory\coding-knowledge.md).
    - Do not use absolute paths.

    args:
    - relative_path (str): The relative path to the file to be read.

    """
    try:
        parts = relative_path.split("\\")  # Ensure the path uses backslashes
        file_path = os.path.join(os.getcwd(), "memory", *parts)
        
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(relative_path: str, content: str) -> str:
    """
    Writes the given content to a file at the specified relative path.

    when to use:
    - When you need to store new structured memory or update existing memory in files based on the provided relative file path.
    
    example usage:
    - write_file("\short_term_memory\coding-knowledge.md", "updated coding knowledge entry") to store new coding knowledge memory
    - write_file("\short_term_memory\observations.md", "updated observation entry") to store new observation memory
    - write_file("\short_term_memory\architectural-decisions.md", "updated architectural decision")

    Important:
    - Always use relative file paths in the format start with backslash followed by the folder name (e.g., \short_term_memory\coding-knowledge.md).
    - Do not use absolute paths.

    args:
    - relative_path (str): The relative path to the file where the content should be written

    """
    try:
        parts = relative_path.split("\\")  # Ensure the path uses backslashes
        file_path = os.path.join(os.getcwd(), "memory", *parts)

        
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Content successfully written"
    except Exception as e:
        return f"Error writing to file: {e}"


tools = [read_file, write_file]



class Memory:
    def __init__(self):
        
        current_dir = os.getcwd()
        self.short_term_memory_path = f"{current_dir}\memory\short_term_memory"
        self.long_term_memory_path = f"{current_dir}\memory\long_term_memory"
        self.consolidation_periodicity = 60 * 60 * 24 # 24 hours in seconds
        
        self.model = init_chat_model(
                                        model="gpt-oss:20b",
                                        model_provider="ollama",
                                        base_url="https://ollama.com",
                                        api_key=os.getenv('OLLAMA_API_KEY'),
                                        # Kwargs passed to the model:
                                        temperature=1,
                                        #timeout=30,
                                        max_tokens=1000,
                                    ) 
        
        
        self.memory_agent =  create_agent(
                                            self.model,
                                            system_prompt=MEMORY_SYSTEM_PROMPT,
                                            tools=tools
                                            )
        
        self.consolidation_agent = create_agent(
                                            self.model,
                                            system_prompt=CONSOLIDATION_SYSTEM_PROMPT,
                                            tools=tools
                                            )
        

    
    
    def memorize(self, memory_incident:str):
        """
        This method takes a memory incident (a string describing an event, observation, or experience) and stores it in the appropriate memory storage (short-term) based on its relevance and importance.
        """

        memorize_prompt = f"""
        MEMORIZE: Analyze the memory incident clearly and recognize the appropriate memory category files based on the following memory incident, then read those files, integrate the new structured details without duplication, rewrite the entire updated content, and save it.
        
        use only single backslash for file paths in the format start with backslash followed by the folder name (e.g., \short_term_memory\coding-knowledge.md) when mentioning the file paths while reading and writing the files.

        #memory incident: 
        {memory_incident} 

        give some done message in brief after successful memorization."""

        

        response = self.memory_agent.invoke(
                                            {"messages": [{"role": "user", "content": memorize_prompt}]}
                                            )
        
        return f"Response: {response['messages'][-1].content}" # Return the content of the last message in the response


    def recall(self, memory_context:str):
        """
        This method retrieves relevant structured memories from external memory based on the provided context. The context can be a query, a situation, or any information that helps in identifying which memories are relevant to the current situation.
        """
        recall_prompt = f"""
        RECALL: Analyze the following memory context, determine which memory category files are relevant, read only those files, extract only the memory details directly related to the provided context, and return only the relevant memory content.
        
        #memory context:
        {memory_context}

        give some done message in brief after successful recall.

        """

        response = self.memory_agent.invoke(
                                            {"messages": [{"role": "user", "content": recall_prompt}]}
                                            )
        
        return f"Response: {response['messages'][-1].content}" # Return the relevant memory content
    

    def consolidate(self):
        """
        This method is responsible for transferring important and relevant structured memories from short-term memory to long-term memory based on their significance, relevance, and potential future utility. 
        It ensures that valuable insights and knowledge are preserved for long-term retention while maintaining an organized structure in the long-term memory storage.

        """

        memory_headings = {
        "coding-knowledge.md": "Coding Knowledge",
        "architectural-decisions.md": "Architectural Decisions",
        "preferences.md": "Preferences",
        "observations.md": "Observations",
        "insights.md": "Insights",
        "constraints-discovery.md": "Constraints Discovery",
        "edge-cases-discovery.md": "Edges Cases Discovery",
        "failures.md": "Failures"
                            }   
        
        #combined all files content in short-term memory
        short_term_memory_content = ""

        path = self.short_term_memory_path
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    heading = memory_headings.get(file_name, "General Memory")
                    short_term_memory_content += f"## {heading}\n\n{content}\n\n" 
        
        

        consolidate_prompt = f""" 
        CONSOLIDATE Short term memory to long term memory: Analyze the following combined short-term memory content and identify and extract only the most important and relevant structured knowledge that should be transferred to long-term memory seperatly into episodic.md, semantic.md, procedural.md files. 
        Do not include any unnecessary or redundant information.

        #short-term memory content:
        {short_term_memory_content}

        only save the content that should be stored in long-term memory, and do not include any explanations or justifications.
        """

        response = self.consolidation_agent.invoke(
                                            {"messages": [{"role": "user", "content": consolidate_prompt}]}
                                            )
        
        return response["messages"][-1].content # Return the consolidated long-term memory content
    

    def consolidation_trigger(self):

        #it could be scheduled to run periodically (e.g., once a day) or triggered manually when the agent determines that there is enough valuable information in short-term memory that should be preserved for long-term retention.
        #The consolidation process can also be triggered after a certain number of new memory incidents have been stored in short-term memory, indicating that there is a significant amount of new information that may warrant consolidation into long-term memory.

        
        #trigger consolidation based on periodicity
        
        #all short-term catergores
        l = ["coding-knowledge", "architectural-decisions", "preferences", "observations", "insights", "constraints_discovery", "edges_cases_discovery", "failures"]
        pass








