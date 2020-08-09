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
    params = None
    all_params_present = True

    if intent == consts.SCHEDULE_MEETING:
        params = get_schedule_meeting_params(query_result.parameters)
    elif intent in {
        consts.STORE_AGENDA,
        consts.GET_AGENDA,
        consts.STORE_NOTES,
        consts.GET_NOTES,
        consts.CHANGE_REMIND,
        consts.CANCEL_MEETING,
        consts.DATE_INTENT,
    }:
        params = {"datetime": get_datetime(query_result.parameters)}

    if params is not None:
        all_params_present = check_params_present(params)

    result = IntentResult(
        intent, params, all_params_present, query_result.fulfillment_text,
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
    duration = None
    if "duration" in params and params["duration"]:
        duration = params["duration"]["amount"]
        if params["duration"]["unit"] == "h":
            duration *= 60

    result = {"datetime": get_datetime(params), "duration": duration}

    return result


def get_datetime(params):
    date = time = datetime = None
    if "date" in params and params["date"]:
        date = arrow.get(params["date"])
    if "time" in params and params["time"]:
        time = arrow.get(params["time"])

    if date is not None:
        datetime = date
        if time is not None:
            datetime = date.replace(hour=time.hour, minute=time.minute)

    return datetime


def check_params_present(params):
    all_present = True
    for key, val in params.items():
        if val is None:
            all_present = False
            break

    return all_present
