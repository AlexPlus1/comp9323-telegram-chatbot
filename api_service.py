import datetime as dt
import dialogflow

import consts


def get_intent(session_id, text):
    """Get intent from a given text

    Args:
        session_id (str): the session ID allows continuation of a conversation
        text (str): the text for getting its intent

    Returns:
        dict: the text intent along with some other information
            {
                "intent": str,
                "params": dict(key=param_key, value=param_value),
                "all_params_present": bool,
                "fulfill_text": str
            }
    """
    project_id = "dojochatbot-gcietn"
    language_code = "en"
    session_client = dialogflow.SessionsClient.from_service_account_file("keyfile.json")

    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session, query_input=query_input)

    query_result = response.query_result
    intent = query_result.intent.display_name
    params = {}

    if intent == consts.SCHEDULE_MEETING:
        params = get_schedule_meeting_params(query_result.parameters)

    result = {
        "intent": intent,
        "params": params,
        "all_params_present": query_result.all_required_params_present,
        "fulfill_text": query_result.fulfillment_text,
    }

    return result


def get_schedule_meeting_params(params):
    """Extract and format the parameters for scheduling a meeting

    Args:
        params (dict): the dictionary of parameters from Dialogflow

    Returns:
        dict: the dictionary of parameters
            {
                "datetime": Python datetime object,
                "duration": (float): duration in minutes
            }
    """
    date = time = date_time = duration = None
    if params["date"]:
        date = dt.datetime.fromisoformat(params["date"])
    if params["time"]:
        time = dt.datetime.fromisoformat(params["time"])
    if date is not None and time is not None:
        date_time = date.replace(hour=time.hour, minute=time.minute)

    if params["duration"]:
        duration = params["duration"]["amount"]
        if params["duration"]["unit"] == "h":
            duration *= 60

    result = {"datetime": date_time, "duration": duration}

    return result

