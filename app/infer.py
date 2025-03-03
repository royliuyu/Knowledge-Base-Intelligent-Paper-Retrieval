import os
import json
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema.runnable import Runnable, RunnableConfig
from typing import Any, Iterator, List, Union
from functools import lru_cache
from util import load_config


config = load_config('../config.yaml')  ## argument is config path

class CustomRunnableLLM(Runnable):
    def __init__(self, temperature=0.5, max_new_tokens=250):
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens

    def invoke(self, input: Any, config: RunnableConfig = None) -> Any:
        """
        Process a single input and return the result.
        """
        response = custom_completion(input, temperature=self.temperature, max_tokens=self.max_new_tokens)
        return response

    def batch(self, inputs: list, config: Union[RunnableConfig, List[RunnableConfig]] = None, **kwargs) -> List[Any]:
        """
        Process a list of inputs and return a list of results.
        """
        res = [self.invoke(input, config=config) for input in inputs]
        return res

    def stream(self, input: Any, config: RunnableConfig = None, **kwargs) -> Iterator[Any]:
        """
        Stream the output for a single input.
        """
        response = custom_completion(input, temperature=self.temperature, max_tokens=self.max_new_tokens)
        yield response


def custom_completion(prompt, temperature=0.5, max_tokens=250):
    model = config['llm']['model']
    try:
        API_KEY, BASE_URL  = os.getenv("QWEN_API_KEY"), os.getenv("QWEN_BASE_URL")
        if not API_KEY or not BASE_URL:
            raise ValueError("Environment variables QWEN_API_KEY and QWEN_BASE_URL must be set.")
        client = OpenAI(
            api_key = API_KEY,
            base_url = BASE_URL, # "https://dashscope.aliyuncs.com/compatible-mode/v1")
        )
        prompt = json.dumps(prompt) if isinstance(prompt, dict) else prompt
        completion = client.chat.completions.create(
            model = model, # model="qwen-plus-latest",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": str(prompt)},
                {"role": "assistant", "content": ""},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"Error: {e}")
        return "Error in generating response."


# Initialize LLM
llm = CustomRunnableLLM(temperature= config['llm']['temperature'], max_new_tokens=config['llm']['max_new_tokens'])

if not isinstance(llm, Runnable):
    raise ValueError("The provided LLM must be an instance of Runnable.")

def get_answer(question, vectorstore):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)

    template = (
        "You will be input some vectorizations, which is the content of question with the associated contents which are selected from the papers, which are under the folder user selected."
        "You are an assistant to index and reply the questions according to the context. "
        "If you are unable to find an answer to the question in the given context or if there is no context, respond with 'Not found in the context!'. "
        "Provide step-by-step answers. You must include relevant code snippets whenever possible.\n"
        "Question: {question}\n\nContext: {context}"
    )

    prompt = PromptTemplate.from_template(template)

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": config['vect']['score_threshold'], "k": config['vect']['k']},  # 0.35, 0.5
        ),
        memory=memory,
        condense_question_prompt=prompt,
    )

    return chain({"question": question})


def format_response(response):
    return f"**Response:**\n\n\"{response['answer']}\""


def chat_with_model(question, vectorstore):
    response = get_answer(question, vectorstore)
    formatted_response = format_response(response)
    return formatted_response


@lru_cache(maxsize= config['vect']['maxsize'])
def get_vectorstore(user_id: str, pdf_directory: str):
    """
    Generate vectorstore by ID folder ，using LRU buffer。
    """
    pdf_pages = []
    for directory, _, files in os.walk(pdf_directory):
        for file in files:
            file_path = os.path.join(directory, file)
            loader = PyPDFLoader(file_path)
            pdf_pages.extend(loader.load_and_split())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    documents = text_splitter.split_documents(pdf_pages)

    embeddings = SentenceTransformerEmbeddings(model_name= config['vect']['embedding_model'])
    vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=f"../vectorstores/{user_id}")
    return vectorstore