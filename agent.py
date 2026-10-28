from pathlib import Path
import json

logs = Path("logs.json")
logs_content = json.dumps(json.loads(logs.read_text()), indent=2) if logs.exists() and logs.stat().st_size > 2 else "No past interactions yet."

SYSTEM_PROMPT = f"""
You are a Drug-Food Interaction Inspector AI.

Always collect: drug name, food consumed, symptoms, and timing before proceeding.

Use `drug_food_interaction_tool` to normalize the drug and fetch real FDA interaction data.
From the ouput that's generated check for the user food and drug warnings.
Never determine severity from your own knowledge — only from fetched data.

Severity routing:
- mild → give 2-3 home remedy suggestions, end with "if symptoms worsen, see a doctor." Do not schedule.
- moderate → tell user to see a doctor soon, automatically call `check_doctor_availability` to find open slots, then call `book_doctor_appointment` to confirm. Include interaction summary in the booking briefing.
- severe → urgent tone, tell user to go to ER immediately, automatically call `check_doctor_availability` and `book_doctor_appointment` for the earliest available slot. Include interaction summary for ER/doctor staff.

For moderate and severe, always attempt scheduling without waiting for the user to ask.
Never recommend prescription medications. Never skip drug normalization.

Past interaction logs (use these directly if the same drug+food combination is found, skip tool calls):
{logs_content}
"""

from pydantic import BaseModel,Field

class Interaction_result(BaseModel):
    drug: str = Field(description="The drug name")
    food: str = Field(description="The food item")
    severity: str = Field(description="The severity of the interaction")
    remedy: str = Field(description="The remedy for the interaction")
    doctor_scheduled: bool = Field(description="Whether the doctor was scheduled or not")

from pathlib import Path
   
ROOT = Path(__file__).parent
LOG_FILE = ROOT / "logs.json"

def write_logs(drug: str,food: str,severity: str,remedy: str = None,doctor_scheduled: bool = False):
    log_entry = {
        "drug": drug,
        "food": food,
        "severity": severity,
        "remedy": remedy,
        "doctor_scheduled": doctor_scheduled
    }
    with open(LOG_FILE, "r+") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
        logs.append(log_entry)
        f.seek(0)
        json.dump(logs, f, indent=2)
        

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from dotenv import load_dotenv
import os

from tools import drug_food_interaction_tool, check_doctor_availability, book_doctor_appointment


load_dotenv()
Model = os.getenv("Model", "gpt-4o")
        
def main()-> Interaction_result:
    model = ChatOpenAI(
        model=Model,
        use_responses_api=True,
        timeout=90,
        max_retries=2,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://aipipe.org/openai/v1"
    )
    agent = create_agent(
        model=model,
        tools=[drug_food_interaction_tool, check_doctor_availability, book_doctor_appointment],
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(Interaction_result)
    )
    try:
        result = agent.invoke({
            "input": "I took aspirin and ate grapefruit."
        })
        print(result)
        write_logs(
            drug=result.drug,
            food=result.food,
            severity=result.severity,
            remedy=result.remedy,
            doctor_scheduled=result.doctor_scheduled
        )
    except Exception as e:
        write_logs(
            drug="unknown",
            food="unknown",
            severity="error",
            remedy=f"Error occurred: {str(e)}",
            doctor_scheduled=False
        )


if __name__ == "__main__":
    main()




