from langchain.tools import tool
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
CAL_API_KEY=os.getenv("CAL_API_KEY")

#@tool
def drug_drug_interaction_tool(drug_name: str) -> dict:
    """
    Agent tool that normalizes a drug name via RxNav and then retrieves 
    its official FDA food interaction warnings using the openFDA API.
    
    Args:
        drug_name (str): The name of the drug to check (e.g. "aspirin", "Lipitor").
    """
    clean_drug = drug_name.strip()
    if not clean_drug:
        return {"error": "Please provide a valid drug name."}

    # STEP 1: Normalize via RxNav approximateTerm to get the canonical generic name
    rxnav_url = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
    rxnav_params = {"term": clean_drug, "maxEntries": 1, "option": 1}
    
    canonical_name = clean_drug # Fallback
    try:
        rx_res = requests.get(rxnav_url, params=rxnav_params, timeout=5)
        if rx_res.status_code == 200:
            candidates = rx_res.json().get("approximateGroup", {}).get("candidate", [])
            if candidates:
                # Use the standardized name for better openFDA matching
                print("running reached")
                canonical_name = candidates[0].get("name", clean_drug)
                print(canonical_name)
    except requests.exceptions.RequestException:
        print("failed to fetch")
        pass # If RxNav fails, fallback to the user's raw string for openFDA

    # STEP 2: Query openFDA for the drug's food interaction warnings
    fda_url = "https://api.fda.gov/drug/label.json"
    # Search the active ingredient or brand name
    fda_params = {
        "search": f'openfda.active_ingredient:"{canonical_name}" openfda.brand_name:"{canonical_name}"',
        "limit": 1
    }
    
    try:
        fda_res = requests.get(fda_url, params=fda_params, timeout=8)
        if fda_res.status_code == 404:
            return {
                "success": False,
                "message": f"Could not find an official FDA drug label for '{canonical_name}'."
            }
        fda_res.raise_for_status()
        fda_data = fda_res.json()
        
        # Extract results
        results = fda_data.get("results", [])
        if not results:
            return {"success": False, "message": "No label data returned."}
            
        label = results[0]
        print(label.keys())
        # openFDA maps food interactions to 'drug_and_food_interactions' or fields within 'description'/'warnings'
        #food_interactions = label.get("warnings_and_cautions", None)
        food_interactions = label.get("drug_interactions_table", [""])
        
        # Fallback check if the specific food field is missing but general warnings exist
        if not food_interactions:
            precautions = label.get("warnings_and_cautions", [""])
            
            
            # Combine them for the LLM to scan
            food_interactions = [f"Check general warnings:  {precautions[0]}"]
            

        return {
            "success": True,
            "normalized_drug_name": canonical_name,
            "fda_food_interaction_text": food_interactions[0] if food_interactions else "No explicit food interaction section found on the label. Please evaluate general precautions."
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to retrieve data from FDA servers: {str(e)}"}
    
answer=drug_drug_interaction_tool("paracetmol")
print(answer)   


    
BASE_URL = "https://cal.com"    

#@tool
def check_doctor_availability(event_type_id: int, start_date: str, end_date: str) -> dict:
    """
    Scans Cal.com for a doctor's open appointment slots within a date range.
    
    Args:
        event_type_id (int): The ID of the doctor's event type (e.g. 123456).
        start_date (str): The starting date to check in YYYY-MM-DD format.
        end_date (str): The ending date to check in YYYY-MM-DD format.
    """
    url = f"{BASE_URL}/slots"
    headers = {"Authorization": f"Bearer {CAL_API_KEY}"}
    params = {
        "eventTypeId": event_type_id,
        "startTime": f"{start_date}T00:00:00Z",
        "endTime": f"{end_date}T23:59:59Z"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        slots_data = data.get("slots", {})
        if not slots_data:
            return {
                "success": True, 
                "message": f"No available slots found between {start_date} and {end_date}."
            }
            
        return {
            "success": True,
            "available_slots": slots_data
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API request failed: {str(e)}"}

@tool
def book_doctor_appointment(event_type_id: int, start_time: str, patient_name: str) -> dict:
    """
    Books an open slot for a patient in Cal.com.
    
    Args:
        event_type_id (int): The ID of the doctor's event type.
        start_time (str): The exact ISO timestamp chosen by the user (e.g., '2026-10-28T14:30:00Z').
        patient_name (str): Full name of the patient.
        
    """
    url = f"{BASE_URL}/bookings"
    headers = {"Authorization": f"Bearer {CAL_API_KEY}"}
    payload = {
        "eventTypeId": event_type_id,
        "start": start_time,
        "name": patient_name,
        "timeZone": "UTC",
        "language": "en"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        booking_data = response.json().get("booking", {})
        
        return {
            "success": True,
            "booking_id": booking_data.get("id"),
            "status": booking_data.get("status"),
            "summary": booking_data.get("title"),
            "confirmed_time": booking_data.get("start")
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Booking failed: {str(e)}"}
    