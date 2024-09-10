import streamlit as st
from streamlit_chat import message
import tempfile
from langchain_community.document_loaders import CSVLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.llms import CTransformers
from langchain.chains import ConversationalRetrievalChain
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
#local folder to store embeddings
db_faiss_path = "vectorstorer/db_fais"


tokenizer = AutoTokenizer.from_pretrained("t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("t5-base")
nlp_pipeline = pipeline(
    "text2text-generation", 
    model=model, 
    tokenizer=tokenizer,
    clean_up_tokenization_spaces=True  # Explicitly set this parameter
)



#display title of app
st.title('App for interacting with CSV files using Llama 2')

#text which you can give
st.markdown("<h2 style='text-align:center; color:Black;'>Built by <a href='https://github.com/Ashoksai-tech'>Ashok Sai-Tech</a></h2>", 
            unsafe_allow_html=True)

#var to store file
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type='csv')

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())  # Correct way to write file content
        tmp_file_path = tmp_file.name

    loader = CSVLoader(file_path=tmp_file_path, encoding='latin', csv_args={'delimiter': ','})
    data = loader.load()
    st.json(data)

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
    db = FAISS.from_documents(data, embeddings)
    db.save_local(db_faiss_path)

    llm = load_llm()
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retrieval=db.as_retriever())

    def conversation(query):
        result = chain({"question": query, "chat_history": st.session_state['history']})
        st.session_state['history'].append((query, result['answer']))  # Append a tuple (question, answer)
        return result['answer']

    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Hey, I'm here to answer anything about " + uploaded_file.name]

    if 'past' not in st.session_state:
        st.session_state['past'] = ['Hey! 👋']  # Emoji fix

    # container for chat history
    res_container = st.container()

    # container for user input
    container = st.container()

    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_input("Query:", placeholder="Get insights with your data", key='input')
            submit_button = st.form_submit_button(label='Interact')

        if submit_button and user_input:
            output = conversation(user_input)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)  # Append the result to the generated list

    # Ensure that chat history is displayed correctly
    if st.session_state['generated']:
        with res_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs-up")  # Added a thumbs-up emoji style

