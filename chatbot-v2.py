import streamlit as st
import requests
import json
from tenacity import retry, stop_after_attempt,wait_fixed, wait_random

st.set_page_config(layout="wide")


#w api

auth_domain = st.secrets['general']['auth_domain']
auth_resource_identifier = st.secrets['general']['auth_resource_identifier']
api_base_url = st.secrets['general']['api_base_url']
auth_client_id =  st.secrets['general']["W_CLIENT_ID"]
auth_client_secret =  st.secrets['general']["W_CLIENT_SECRET"]
model_name = st.secrets['general']['model_name']
utility_company = st.secrets['general']['utility_company']

def refresh_auth_token():
    get_token_url = "https://"+auth_domain+"/oauth/token"
    headers = {'content-type': 'application/json'}
    parameter = {"grant_type":"client_credentials", 
                 "client_id":auth_client_id,
                 "client_secret":auth_client_secret, 
                 "audience":auth_resource_identifier}
    response = requests.post(get_token_url, data=json.dumps(parameter),headers=headers)
    info = response.json()
    return info['access_token']

@retry(reraise=True, wait=wait_fixed(1) + wait_random(0, 1), stop=stop_after_attempt(5))
def execute_sequence(sequence_name, payload):
    access_token = refresh_auth_token()
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json',
        'Accept': '*/*'
    }
                                            
    route = api_base_url + '/api/v1/execute?sequence-name=' + sequence_name
    response = requests.post(route, headers=headers, data=json.dumps(payload))
    output = response.json()
    print("raw output")
    print(output)
    if 'preds' not in output:
        raise ValueError("missing preds")
    
    output = output['preds']
    return output

# Function to call the chatbot API                                                                                                                                                                                                                            
def get_agent_response(conversations):
    # Here you'd call the real API using requests                                                                                                                                                                                                             

    conversations_org = conversations.copy()

    conversations = [{item['speaker']:item['text']} for item in conversations]
    conversations_customer =  list(filter(lambda item: item['speaker']=='customer', conversations_org))
    if len(conversations_customer) >= 1:
        customer_last_response = conversations_customer[-1]['text']
    else:
        customer_last_response = ""

    raw_payload = {
        "inputs": {
            "meta": {
                "customer_information_collected": {
                    "name": "Mary",
                    "zip_code": "21560"
                },
                "utility_company": utility_company,
                "list_of_available_internet_providers": [
                    "AT&T",
                    "Verizon"
                ],
                "agent_name": "Tom"
            },
            "conv_hist": conversations,
            "customer_last_response": customer_last_response
        }
    }
    print(f"Conversation sent to the API: {raw_payload}")
    
    
    payload = {
        "data":[
            {
                "inputs": json.dumps(raw_payload["inputs"])
            }
        ]
    }

    output = execute_sequence(model_name,payload)
    #print(output)
        
    answer = output['answer']['answer']
    print(answer)

    return {"agent":answer}

######################################################################

    
# Initialize conversation_history in session_state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Function to append messages to the conversation history
def add_message(speaker, message):
    # Make sure the message is not empty
    if message.strip() != "":
        st.session_state.conversation_history.append({"speaker": speaker, "text": message})

# Add a unique key for the message input field to clear it when needed
if 'msg_key' not in st.session_state:
    st.session_state.msg_key = 0

# UI to add messages
st.title("Chatbot Simulation")
speaker_selection = st.selectbox("Who is speaking?", ["customer", "agent"], key="speaker")

# Message input field with dynamic key
message = st.text_input("Message", key=f"message_{st.session_state.msg_key}")

# Button to add a message to the conversation history
if st.button("Add Message"):
    add_message(speaker_selection, message)
    # Increment the key to clear the input field
    st.session_state.msg_key += 1

# Button to submit the conversation history and get an agent response
if st.button("Submit"):
    if st.session_state.conversation_history:
        # Filter messages for the transaction to the chatbot API
        #chat_data = [chat for chat in st.session_state.conversation_history if chat["speaker"] == "customer"]
        chat_data = [chat for chat in st.session_state.conversation_history]
        agent_reply = get_agent_response(chat_data)
        add_message("agent", agent_reply["agent"])

# Display Conversation History
#st.write("### Conversation History")
#for chat in st.session_state.conversation_history:
#    st.text(f'{chat["speaker"].capitalize()}: {chat["text"]}')

# Custom CSS to enforce word wrap
st.markdown("""
    <style>
    .stText {
        word-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# Display Conversation History with st.text
#st.write("### Conversation History")
#for chat in st.session_state.conversation_history:
#    st.text(f"{chat['speaker'].capitalize()}: {chat['text']}")

# Display Conversation History
st.write("### Conversation History")
with st.container():
    for idx, chat in enumerate(st.session_state.conversation_history):
        with st.expander(f"Message {idx+1} ({chat['speaker'].capitalize()})",expanded=True):
            st.write(chat['text'])
            
    
# Ensure the conversation scrolls into view
st.markdown("""
    <script>
        const messageContainer = document.querySelector('.stText');
        if (messageContainer) {
            messageContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    </script>
""", unsafe_allow_html=True)

# Increase the text container width using custom CSS
st.markdown("""
<style>
    .stText { overflow-x: auto; }
</style>
""", unsafe_allow_html=True)


