import streamlit as st
from openai import OpenAI
import fitz
from urllib.parse import urlparse
from youtube_transcript_api import YouTubeTranscriptApi

st.title("Mini Chat-Bot")
st.write("Upload File")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
st.markdown("Put youtube video Link below")
raw_transcript = st.text_input("Link")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = []

parsed_url = urlparse(raw_transcript)
if parsed_url.query:
    id = parsed_url.query.split("=")[1]
    transcript = YouTubeTranscriptApi.get_transcript(id)
    items = ""
    for content in transcript:
        items += f"{content["text"]} "
    st.session_state.messages.append({"role": "system", "content": items})
    if st.button("summarize Video"):
        summarized_video = client.chat.completions.create(model=st.session_state.openai_model, messages=[
            {"role": "user", "content": f"Summarize the following youtube video content:{items}"}])
        st.session_state.messages.append(
            {"role": "user", "content": "Summarize the following youtube video"})
        st.session_state.messages.append(
            {"role": "assistant",
                "content": summarized_video.choices[0].message.content}
        )

if uploaded_file is not None:
    docs = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in docs:
        text += page.get_text()  # type: ignore
    st.session_state.messages.append(
        {"role": "system", "content": text})

    if st.button("summarize text"):
        summarize_text = client.chat.completions.create(model=st.session_state.openai_model, messages=[
            {"role": "user", "content": f"Summarize the following content {text}"}])
        st.session_state.messages.append(
            {"role": "user", "content": "Summarize the following content"})
        st.session_state.messages.append(
            {"role": "assistant",
                "content": summarize_text.choices[0].message.content}
        )
    docs.close()

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Enter message here"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=[{
                "role": m["role"], "content": m["content"]
            }
                for m in st.session_state.messages
            ],
            stream=True
        )
        stream = st.write_stream(response)
    st.session_state.messages.append({"role": "assistant", "content": stream})
