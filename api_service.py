import arrow
import dialogflow

import consts


class IntentResult:
    def __init__(self, intent, params, all_params_present, fulfill_text):
        self.intent = intent
        self.params = params
        self.all_params_present = all_params_present
        self.fulfill_text = fulfill_text


def get_intent(session_id, text) -> IntentResult:
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
    # meeting list
    elif intent == consts.MEETING_LIST:
        params = None

    result = IntentResult(
        intent,
        params,
        query_result.all_required_params_present,
        query_result.fulfillment_text,
    )

    return result


def get_schedule_meeting_params(params):
    """Extract and format the parameters for scheduling a meeting

    Args:
        params (dict): the dictionary of parameters from Dialogflow

    Returns:
        dict: the dictionary of parameters
            {
                "datetime": Arrow object,
                "duration": (float): duration in minutes
            }
    """
    date = time = date_time = duration = reminder = None
    if params["date"]:
        date = arrow.get(params["date"])
    if params["time"]:
        time = arrow.get(params["time"])
    if date is not None and time is not None:
        date_time = date.replace(hour=time.hour, minute=time.minute)
    if params["reminder"]:
        reminder = params["reminder"]

    if params["duration"]:
        duration = params["duration"]["amount"]
        if params["duration"]["unit"] == "h":
            duration *= 60

    result = {"datetime": date_time, "duration": duration, "reminder": reminder}

    return result

