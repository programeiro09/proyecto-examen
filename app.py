import gradio as gr
from query import get_qa_chain

chain = get_qa_chain()

def ask(question, history):
    if not question.strip():
        return "", history

    result = chain.invoke({"query": question})
    answer = result["result"]

    sources = set(
        doc.metadata.get("source", "desconocido")
        for doc in result["source_documents"]
    )
    if sources:
        answer += f"\n\n**Fuentes:** {', '.join(sources)}"

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    return "", history

with gr.Blocks(title="Second Brain") as demo:
    gr.Markdown("## 🧠 Second Brain Lite")
    chatbot = gr.Chatbot(height=420)
    with gr.Row():
        txt = gr.Textbox(placeholder="Pregunta algo sobre tus notas...", scale=4)
        btn = gr.Button("Enviar", scale=1)

    btn.click(ask, [txt, chatbot], [txt, chatbot])
    txt.submit(ask, [txt, chatbot], [txt, chatbot])

demo.launch()
