import arrow
import dialogflow

import consts


class IntentResult:
    def __init__(self, intent, params, all_params_present, fulfill_text, is_mentioned):
        self.intent = intent
        self.params = params
        self.all_params_present = all_params_present
        self.fulfill_text = fulfill_text
        self.is_mentioned = is_mentioned


def get_intent(session_id, text=None, input_audio=None) -> IntentResult:
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
    if text is None and input_audio is None:
        raise ValueError("Either text or input_audio must be provided")

    project_id = "dojochatbot-gcietn"
    language_code = "en"
    session_client = dialogflow.SessionsClient.from_service_account_file("keyfile.json")
    session = session_client.session_path(project_id, session_id)

    if text is not None:
        text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
    else:
        audio_encoding = dialogflow.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16
        audio_config = dialogflow.types.InputAudioConfig(
            audio_encoding=audio_encoding, language_code=language_code,
        )
        query_input = dialogflow.types.QueryInput(audio_config=audio_config)

    response = session_client.detect_intent(
        session=session, query_input=query_input, input_audio=input_audio
    )
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

    is_mentioned = query_result.query_text.lower().startswith(
        f"hey {consts.BOT_NAME.lower()}"
    )
    result = IntentResult(
        intent, params, all_params_present, query_result.fulfillment_text, is_mentioned
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
