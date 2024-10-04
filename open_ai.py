#!./.venv/bin/python

import json
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.documents.base import Blob
from dotenv import load_dotenv
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import ChatPromptTemplate
from prompts import reduce_template
from langchain_core.documents import Document



from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from telegram.constants import ChatType

from prompts import (
    summarize_template_with_links,
    summarize_template,
    retell_template,
    identify_params_template,
)

load_dotenv()

model_t9 = ChatOpenAI(model="gpt-4o-mini", temperature=0.9)
model_t0 = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
whisper_parser = OpenAIWhisperParser()

parser = StrOutputParser()

chain_t9 = model_t9 | parser
chain_t0 = model_t0 | parser


def ai_summarize_basic(messages: str, template: PromptTemplate) -> str:
    json_dump = json.dumps(messages, sort_keys=True, default=str, ensure_ascii=False)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=4000, chunk_overlap=500
    )
    split_messages_text = text_splitter.split_text(json_dump)
    split_messages_docs = []

    for text in split_messages_text:
        split_messages_docs.append(
            Document(page_content=text, metadata={"source": "local"})
        )


    aaa = template.format(text = "{text}")

    map_prompt_template = PromptTemplate.from_template(aaa)

    combine_prompt_template = PromptTemplate(
        template=reduce_template, input_variables=["text"]
    )

    summary_chain = None

    summary_chain = load_summarize_chain(
        llm=model_t9,
        chain_type="map_reduce",
        map_prompt=map_prompt_template,
        combine_prompt=combine_prompt_template,
    )

    output = summary_chain.invoke(split_messages_docs)
    return output
    # request = [SystemMessage(content=template), HumanMessage(content=json_dump)]

    # return chain_t9.invoke(request)


def ai_retell(messages, params):
    template = PromptTemplate.from_template(retell_template).format(
        language=params["language"], tone=params["tone"]
    )
    return ai_summarize_basic(messages, template)


def ai_summarize(messages, params, chat_type):
    template = summarize_template
    chat_id = params["chat_id"]

    if chat_type == ChatType.SUPERGROUP:
        template = summarize_template_with_links
        chat_id = str(chat_id)[4:]

    template = PromptTemplate.from_template(
        template,
        partial_variables={
            "language": params["language"],
            "tone": params["tone"],
            "chat_id": chat_id,
        },
    )

    return ai_summarize_basic(messages, template)


def ai_identify_parameters(message):
    result = chain_t0.invoke(
        [SystemMessage(content=identify_params_template), HumanMessage(content=message)]
    )
    result = json.loads(result)
    return result


def ai_request_with_params(message):
    params = ai_identify_parameters(message)
    return params


def ai_describe_image(base64_data):
    message = HumanMessage(
        content=[
            {"type": "text", "text": "describe what in the image image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
            },
        ],
    )
    response = chain_t9.invoke([message])
    return response


def ai_transcript_audio(path: Path) -> str:
    blob = Blob.from_path(path)
    documents = whisper_parser.parse(blob)
    result = ""
    for doc in documents:
        if doc.page_content:
            result += doc.page_content
    return result
