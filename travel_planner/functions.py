import json
from durable_entities_agents import run_agent
import azure.durable_functions as df

bp = df.Blueprint()

# Orchestration of multiple agents with human approval
@bp.orchestration_trigger(context_name="context")
def travel_planner_orchestrator(context: df.DurableOrchestrationContext):
    input = context.get_input()
    if not input:
        raise Exception("Input missing")

    special_requirements = input.get("specialRequirements", "")
    duration_in_days = input.get("durationInDays", 3)

    destinations_json = yield run_agent(context, agent_name="destination_expert_agent", input=special_requirements)
    destinations = json.loads(destinations_json)
    top_destination = destinations.get("recommendations", [])[0]

    itinerary_request = {
        "destination_name": top_destination["destination_name"],
        "duration_in_days": duration_in_days,
        "budget": input.get("budget", "$1000"),
        "travel_dates": input.get("travelDates", "TBD"),
        "special_requirements": special_requirements
    }

    itinerary_json = yield run_agent(context, agent_name="itinerary_planner_agent", input=itinerary_request)
    itinerary = json.loads(itinerary_json)

    local_recs_request = {
        "destination_name": top_destination["destination_name"],
        "duration_in_days": duration_in_days,
        "preferred_cuisine": "Any",
        "include_hidden_gems": True,
        "family_friendly": True
    }

    local_recs_json = yield run_agent(context, agent_name="local_recommendations_agent", input=local_recs_request)
    local_recs = json.loads(local_recs_json)

    response = {
        "destination": top_destination,
        "itinerary": itinerary,
        "local_recommendations": local_recs,
        "approval_status": "pending"
    }
    context.set_custom_status(response)

    approval_result = yield context.wait_for_external_event("approval_event")

    if approval_result != "approved":
        response["approval_status"] = "rejected"
        return response

    booking_result = yield context.call_activity("book_travel_activity", response)
    response["booking_details"] = booking_result
    response["approval_status"] = "approved"

    return response


@bp.activity_trigger(input_name="booking_input")
def book_travel_activity(booking_input: str):
    return {
        "booked": True,
        "booking_id": f"TRV-{hash(str(booking_input)) % 10000:04d}",
        "status": "confirmed",
        "message": "Travel booking confirmed successfully"
    }