from google.cloud import dialogflow_v2 as dialogflow


def detect_intent_texts(project_id, session_id, user_message, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(
        text=user_message,
        language_code=language_code
        )
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    return response.query_result.fulfillment_text
