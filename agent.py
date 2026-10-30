from pathlib import Path
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents.structured_output import ToolStrategy
from langchain.agents import create_agent
from tools import drug_drug_interaction_tool, check_doctor_availability, reserve_Slot

logs = Path("logs.json")
logs_content = json.dumps(json.loads(logs.read_text()), indent=2) if logs.exists() and logs.stat().st_size > 2 else "No past interactions yet."

ROOT = Path(__file__).parent
LOG_FILE = ROOT / "logs.json"

SYSTEM_PROMPT = f"""
You are a dedicated Drug-Drug Interaction Inspector AI. Your sole responsibility is to evaluate potential interactions between two medications to ensure patient safety.

OPERATIONAL EXECUTION FLOW PROTOCOL:
1. INTAKE ANALYSIS: Extract the names of both drugs and the patient's current symptoms from the user input. If exact formulations or timings are missing, DO NOT pause to ask questions. Assume standard adult variations and immediately proceed to evaluation.
2. CACHE LOOKUP: Before executing any tool calls, inspect the "PAST INTERACTION LOGS" section below. If the exact combination of the two drugs is present, immediately use that cached interaction data and skip calling the `drug_drug_interaction_tool`.
3. LIVE TOOL CALL: If no matching cache entry exists, you MUST call `drug_drug_interaction_tool`. Pass the two drug names as separate arguments. You are strictly forbidden from determining interaction severity using your own internal knowledge; you must rely exclusively on the tool output.

SEVERITY ROUTING ENGINE MATRIX (STRICT ENFORCEMENT):
- mild:
  * Actions: Suggest 2-3 safe home remedies or general comfort measures. 
  * Restrictions: DO NOT call any scheduling or calendar tools (`check_doctor_availability`, `reserve_Slot`).
  * Required Conclusion: Conclude your final response exactly with: "If symptoms worsen, see a doctor."
  
- moderate:
  * Actions: Instruct the user to see a healthcare professional soon.
  * Required Tool Sequence: You MUST execute these sequentially. First, call `check_doctor_availability` to fetch valid time strings. Wait for the tool output, select the first available slot from the response list, and then call `reserve_Slot` using that exact start time. Do not make up a time.
  
- severe:
  * Actions: Adopt an urgent, authoritative tone. Command the user to go to the nearest Emergency Room (ER) immediately.
  * Required Tool Sequence: You MUST execute these sequentially. First, call `check_doctor_availability` to fetch valid time strings for follow-up evaluation. Wait for the tool output, select the first available slot from the response list, and then call `reserve_Slot` using that exact start time. Do not make up a time.

PAST INTERACTION LOGS:
{{logs_content}}
"""

class Interaction_result(BaseModel):
    drug_1: str = Field(description="The drug name")
    drug_2: str = Field(description="The other drug name")
    severity: str = Field(description="The severity of the interaction")
    remedy: str = Field(description="The remedy for the interaction")
    doctor_scheduled: bool = Field(description="Whether the doctor was scheduled or not")


def write_logs(drug_1: str, drug_2: str, severity: str, remedy: str = None, doctor_scheduled: bool = False, invoked_tools: list = None):
    log_entry = {
        "drug_1": drug_1,
        "drug_2": drug_2,
        "severity": severity,
        "remedy": remedy,
        "doctor_scheduled": doctor_scheduled,
        "invoked_tools": invoked_tools or []
    }
    logs_data = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                logs_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logs_data = []
            
    logs_data.append(log_entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs_data, f, indent=2)
            
load_dotenv()

def main():
    Model = os.getenv("Model", "gpt-4o")
    
    model = ChatOpenAI(
        model=Model,
        timeout=90,
        max_retries=2,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://aipipe.org/openai/v1",
        model_kwargs={"reasoning_effort": "none"}
    )
    
    # FIXED: Removed ToolStrategy so the agent can invoke multiple different tools in sequence
    agent = create_agent(
        model=model,
        tools=[drug_drug_interaction_tool, check_doctor_availability, reserve_Slot],
        system_prompt=SYSTEM_PROMPT
    )
    
    try:
        result = agent.invoke({
            "messages": [
                {"role": "user", "content": "I took Tylenol and DayQuil together 2 hours ago. I am now experiencing severe upper-right abdominal pain, nausea, and yellowing of my eyes."}
                
            ]
        })
        print(result)
        return result
    except Exception as e:
        print(f"Error during agent invocation: {e}")
        return {"error": str(e)}
        
     
        
       
        
    
if __name__ == "__main__":
    main()