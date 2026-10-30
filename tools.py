from langchain.tools import tool
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from datetime import timedelta
load_dotenv()
CAL_API_KEY=os.getenv("CAL_API_KEY")

@tool
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
    
#answer=drug_drug_interaction_tool("paracetmol")
#
# print(answer)   


    
BASE_URL = "https://api.cal.com/v2/slots"   

EVENT_TYPE_ID = 7703493

@tool
def check_doctor_availability(event_type_id: str) -> dict:
    """Checks all the open, available time slots for the doctor.
    
    Args:
        event_type_id (str): The ID of the doctor's event type (e.g. '7703493').
    """
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}", 
        "cal-api-version": "2024-09-04"
    }
    
    # Check slots starting from right now up to the next 3 days
    start_time = datetime.utcnow().isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
    
    query_params = {
        "eventTypeId": event_type_id,
        "start": start_time,
        "end": end_time,
        "timeZone":"Asia/Kolkata"
    }
    
    try:
        response = requests.get(url=BASE_URL, headers=headers, params=query_params, timeout=10)
        response.raise_for_status()
        result = response.json()
        slots = result["data"]
       
        if not slots:
            return {"success": True, "message": "No slots found in this window."}
            
        return {"success": True, "Available_slots": slots}
    except requests.exceptions.RequestException as e:
        error_msg = response.text if 'response' in locals() else str(e)
        return {"success": False, "error": f"API Error: {error_msg}"}
    
# Run the test
#print(check_doctor_availability(EVENT_TYPE_ID))



@tool
def reserve_Slot(event_type_id: int, start_time: str) -> dict:
    """
    Books an open slot for a patient in Cal.com.
    
    Args:
        event_type_id (int): The ID of the doctor's event type.
        start_time (str): ISO 8601 datestring in UTC timezone representing available slot. ex: 2026-11-02T09:20:00.000+05:30  
    """
    url = "https://api.cal.com/v2/slots/reservations"
    headers = {"Authorization": f"Bearer {CAL_API_KEY}","cal-api-version": "2024-09-04"}
    payload = {
        "eventTypeId": event_type_id,
        "slotStart": start_time
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result=response.json()
        return {
            "success": True,
            "Start_timing":result["data"]["slotStart"],
            "Slot_Duration":result['data']["slotDuration"]
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Booking failed: {str(e)}"}

#print(reserve_Slot(7703493,"2026-11-02T09:40:00.000+05:30"))
    