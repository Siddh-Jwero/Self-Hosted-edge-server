# app/qa.py
from app import config
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


JWERO_SYSTEM_PROMPT = (
    "You are a helpful assistant that only uses information from the retrieved RAG (documents). "
    "when query is hi or hello or hey or sup, respond with a greeting only. like 'Hello! How can I assist you today?' only 'Hello! How can I assist you today?'"
    "if anybody says i need help or i need assistance, respond with 'Sure! How can I assist you today?' only 'Sure! How can I assist you today?'"
    "Don't invent, guess, or assume info; only answer from RAG. "
    "Give correct branded platform URLs when asked; brand mapping: "
    "- Jwero main website: https://jwero.ai/ "
    "- Jwero Chats: https://chats.jwero.ai/ "
    "- Jwero CRM: https://crm.jwero.ai/ "
    "give links in answers preferably at starting. "
    "when query is about creating template like 'i need to create template'and it is not specifiend marketing or utlity, answer like 'which template you want to create?'. "
    "when query is about 'how to assign a contact to a team member' it should take reference from RAG document 'how to assign a contact to a team member.txt' and answer accordingly. and don't give/ add '6. To check if the contact is assigned, click on Chats. 7. From the list of team members, the contact will be checked for the members its assigned to. 8. The added contact will appear under the Contacts assigned section. 9. To check if the contact is assigned, click on Chats. 10. From the list of team members, the contact will be checked for the members its assigned to.' this in this query"
    "when query is about 'how to auto-assign contacts to team members' it should take reference from RAG document 'auto-assign-contacts-to-team-members-desktop.pdf' and answer accordingly."
    "while answering responses like 'Go to Settings > Team Member >> Add new Team Member >> Add Name + Number + Email >> Manage Access' give links like 'https://chats.jwero.ai/settings/team-management' at starting like go to ..... "
    "while answering, prioritize URLs over feature lists. "
    "don't give multiple same duplicate answers in one response. "
    "If you need more detailed instructions on how to edit a contact's information in CRM, please provide me with additional context so that I can assist you further. this should be included in EVERY answer in last and after one blank line"
    "For queries containing 'main website', 'main website link', 'jwero website', or similar, always reply: The Jwero main website is at jwero.ai."
    "For queries about 'chat website', 'chats website', or 'chats url', reply: The Jwero Chats website is at chats.jwero.ai. "
    "For queries about 'crm website', 'crm link', or 'crm url', reply: The Jwero CRM website is at crm.jwero.ai. "
    "For queries about 'main website' or 'jwero website', reply: The Jwero main website is at jwero.ai. "
    "For queries about Jwero Chats or 'chats', give only short and branded answers. Summarize features using bullet points only if available in RAG. Never give generic explanations about chatbots; reply only Jwero-specific info or the website link. "
    "If asked about CRM features, provide a short bullet-point summary only if found in RAG documents; otherwise, respond only with website link. Never mix feature summaries with website links in the same answer unless explicitly requested. "
    "Answers must be concise, clear, and never longer than necessary. "
    "For greetings like 'hi', 'hello', 'hey', or 'sup', always respond: Hello! How can I assist you today? Never apologize or ask for details in greeting cases."
    "Never hallucinate or add info not found in RAG."
    "If the query is unrelated to Jwero products or outside RAG scope, respond: I'm sorry, I can only assist with questions related to Jwero products and services. Please visit jwero.ai for more information."
    "Never hallucinate or add info not found in RAG."
)


def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_PATH)
    return FAISS.load_local(
        config.VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )


def map_query_to_category(query: str) -> str | None:
    """Map user query keywords to document category metadata for filtering."""
    q = query.lower()
    if any(x in q for x in ["broadcast", "send broadcast", "create broadcast"]):
        return "broadcast"
    if any(x in q for x in ["crm", "customer relationship", "customer management"]):
        return "crm"
    if any(x in q for x in ["chat", "chatbot", "conversational"]):
        return "chat"
    if any(x in q for x in ["marketing", "advertisement", "ads"]):
        return "marketing"
    if any(x in q for x in ["task", "tasks", "task management"]):
        return "task_management"
    if any(x in q for x in ["team member", "team management"]):
        return "team_management"
    if any(x in q for x in ["contact", "contacts", "import contacts"]):
        return "contacts"
    if any(x in q for x in ["automation", "auto assign", "automatic"]):
        return "automation"
    if any(x in q for x in ["live agent"]):
        return "live_agent"
    if any(x in q for x in ["qr code"]):
        return "qr_code"
    # Fallback: no filter
    return None


def get_qa_chain(
    temperature: float = 0.8,
    top_p: float = 0.95,
    max_tokens: int = 1024,
    system_prompt: str = None,
    query: str = None,
):
    if system_prompt is None:
        system_prompt = JWERO_SYSTEM_PROMPT

    vectorstore = load_vectorstore()
    category = None
    if query:
        category = map_query_to_category(query)

    search_kwargs = {"k": 10}
    if category:
        search_kwargs["filter"] = {"category": category}

    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    llm = Ollama(
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
        temperature=temperature,
        top_p=top_p,
        num_predict=max_tokens,
        system=system_prompt,
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    template = """{context}

Question: {question}

Answer:"""

    prompt = ChatPromptTemplate.from_template(template)

    chain = RunnableParallel(
        result=(
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        ),
        source_documents=retriever
    )

    return chain


def ask(
        
    query: str,
    temperature: float = 0.8,
    top_p: float = 0.95,
    max_tokens: int = 1024,
    system_prompt: str = None,
):
    start_time = datetime.now()
    chain = get_qa_chain(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        query=query,
    )
    result = chain.invoke(query)

    print(f"\n❓ Query: {query}\n")
    print(f"\n🧠 Answer:\n{result['result']}\n")
    print("📚 Sources:")
    
    for doc in result["source_documents"]:
        print(f" - {doc.metadata.get('source')}")
        
    # calculate elapsed time
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print(f"\n🕒 Generation Time: {elapsed:.2f} sec\n")

    return result["result"]