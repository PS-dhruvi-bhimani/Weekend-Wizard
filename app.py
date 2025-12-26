# app.py
import gradio as gr
from datetime import datetime

from agent import run_agent_once


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning ☀️"
    elif hour < 17:
        return "Good Afternoon 🌤️"
    else:
        return "Good Evening ✨"


async def agent_reply(message, history):
    result = await run_agent_once(user_message=message)

    answer = result.get("answer", "").strip()
    tools = result.get("tools_used", [])

    # Log for debugging
    print(f"\n{'='*60}")
    print(f"User Query: {message[:80]}...")
    print(f"Tools Called: {tools if tools else 'None'}")
    print(f"Response Preview: {answer[:100]}...")
    print(f"{'='*60}\n")

    # Format output with tools used
    if tools:
        tools_text = ", ".join(tools)
        answer = (
            f"{answer}\n\n"
            f"---\n"
            f"🛠️ **Tools used:** {tools_text}"
        )
    
    return answer


CUSTOM_CSS = """
:root {
    --body-background-fill: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    --background-fill-primary: transparent;
    --background-fill-secondary: #ffffff;
    --block-background-fill: #ffffff;
}

body {
    background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%) !important;
}

.gradio-container {
    background: transparent !important;
}

@keyframes shine {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

#wizard-title {
    font-size: 3.2rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: 0.25em;
    background: linear-gradient(90deg, #FFD700, #FFA500, #FF6347, #FF1493, #9370DB, #4169E1, #00CED1, #FFD700);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shine 3s ease-in-out infinite;
}

#wizard-greeting {
    font-size: 1.4rem;
    text-align: center;
    color: #555;
    margin-bottom: 1.8em;
}

.gr-chatbot {
    background: #ffffff !important;
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
}

footer {
    display: none !important;
}
"""


with gr.Blocks() as demo:
    greeting = get_greeting()

    gr.HTML(
        f"""
        <div id="wizard-title">weekend - wizard</div>
        <div id="wizard-greeting">
            {greeting}<br/>
            <span style="font-size:1.1rem;">Ask me anything! I'll autonomously decide which tools to use.</span>
        </div>
        """
    )

    chatbot = gr.Chatbot(
        height=420,
        show_label=False,
    )

    gr.ChatInterface(
        fn=agent_reply,
        chatbot=chatbot,
        textbox=gr.Textbox(
            placeholder="Tell me how you're feeling or what you need...",
            scale=7,
            submit_btn="✨ Ask"
        ),
    )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CUSTOM_CSS)
