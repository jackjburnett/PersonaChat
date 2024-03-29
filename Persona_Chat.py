import streamlit as st
import random
import PersonaList
import llama2local
import evaluation

# App title
st.set_page_config(page_title="Persona Chatbot")

# Persona Gen
if "rn" not in st.session_state:
    st.session_state["rn"] = random.randint(0, len(PersonaList.personas))

if "persona" not in st.session_state:
    st.session_state["persona"] = [(PersonaList.personas[st.session_state["rn"]]).replace('.', ',')]
    st.session_state["persona"].append(PersonaList.random_persona().replace('.', ','))
    st.session_state["persona"].append(PersonaList.random_persona().replace('.', ','))
    st.session_state["persona"].append(PersonaList.random_persona().replace('.', ','))

if "order" not in st.session_state:
    order = list(range(4))
    random.shuffle(order)
    st.session_state["order"] = order

if "show_advanced" not in st.session_state:
    st.session_state["show_advanced"] = False


def advanced_change():
    st.session_state["show_advanced"] = not st.session_state["show_advanced"]


# Replicate Credentials
with st.sidebar:
    st.title('Persona Chatbot')

    # Refactored from https://github.com/a16z-infra/llama2-chatbot
    st.subheader('Models and parameters')
    selected_model = st.sidebar.selectbox('Choose a Large Language Model',
                                          ['LLaMa2-7B-Chat', 'LLaMa2-13B-Chat', 'GPT-3.5-turbo-1106'],
                                          key='selected_model')

    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.72, step=0.01,
                                    disabled=(selected_model == "GPT-3.5-turbo-1106"))
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.73, step=0.01,
                              disabled=(selected_model == "GPT-3.5-turbo-1106"))
    st.sidebar.button('Toggle Advanced Options', on_click=advanced_change)

    if st.session_state["show_advanced"]:
        top_k = st.sidebar.slider('top_k', min_value=0, max_value=100, value=0, step=1,
                                  disabled=(selected_model == "GPT-3.5-turbo-1106"))
        repetition = st.sidebar.slider('repetition_penalty', min_value=0.0, max_value=2.0, value=1.1, step=0.01,
                                       disabled=(selected_model == "GPT-3.5-turbo-1106"))
        max_length = st.sidebar.slider('max_length', min_value=64, max_value=4096, value=512, step=8,
                                       disabled=(selected_model == "GPT-3.5-turbo-1106"))
    else:
        top_k = 0
        repetition = 1.1
        max_length = 512

    st.markdown('----')
    st.write("**Rate the Persona**")
    perceived_persona = st.radio("Which persona do you feel is being represented:",
                                 [st.session_state["persona"][st.session_state["order"][0]],
                                  st.session_state["persona"][st.session_state["order"][1]],
                                  st.session_state["persona"][st.session_state["order"][2]],
                                  st.session_state["persona"][st.session_state["order"][3]]])

    coherency = st.slider('Coherency (how well does the AI match the persona)', min_value=0, max_value=10, value=5,
                          step=1)
    fluency = st.slider('Fluency (how natural is the conversation)', min_value=0, max_value=10, value=5, step=1)
    st.sidebar.button(label='Rate Persona',
                      on_click=evaluation.submit_rating,
                      args=(selected_model, temperature, top_p, top_k, repetition, max_length,
                            st.session_state["persona"][0],
                            st.session_state["persona"][0] == perceived_persona,
                            coherency, fluency))
    st.markdown('----')


def clear_chat_history():
    del st.session_state["rn"]
    del st.session_state["persona"]
    del st.session_state["order"]
    st.session_state.messages = [{"role": "Persona", "content": "Hello!", "avatar": "🤖"}]


st.sidebar.button('Clear Chat History and Change Persona', on_click=clear_chat_history)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "Persona", "content": "Hello!", "avatar": "🤖"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message["avatar"]):
        st.write(message["content"])


# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    string_dialogue = f"""
[INST] <<SYS>>
You now have the persona '{st.session_state["persona"][0]}'.
<</SYS>>
Current conversation:
"""
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Persona: " + dict_message["content"] + "\n\n"
    output = llama2local.model_call(selected_model, f"{string_dialogue} {prompt_input} Persona: [/INST]", temperature,
                                    top_p, top_k, repetition, max_length)
    return output


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

# Generate a new response if last message is not from Persona
if st.session_state.messages[-1]["role"] != "Persona":
    with st.chat_message("Persona", avatar="🤖"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "Persona", "content": full_response, "avatar": "🤖"}
    st.session_state.messages.append(message)
