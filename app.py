# app.py
import gradio as gr
from datetime import datetime

from agent import run_agent_once
from config import (
    GRADIO_THEME,
    GRADIO_CHATBOT_HEIGHT,
    GRADIO_TEXTBOX_SCALE,
    UI_TITLE,
    UI_PLACEHOLDER,
    UI_SUBMIT_BUTTON,
    GREETING_MORNING,
    GREETING_AFTERNOON,
    GREETING_EVENING,
    MORNING_HOUR_CUTOFF,
    AFTERNOON_HOUR_CUTOFF,
    LOG_SEPARATOR_WIDTH,
    LOG_MESSAGE_PREVIEW_LENGTH,
    LOG_RESPONSE_PREVIEW_LENGTH
)


def get_greeting():
    hour = datetime.now().hour
    if hour < MORNING_HOUR_CUTOFF:
        return GREETING_MORNING
    elif hour < AFTERNOON_HOUR_CUTOFF:
        return GREETING_AFTERNOON
    else:
        return GREETING_EVENING


async def agent_reply(message, history):
    result = await run_agent_once(user_message=message)

    answer = result.get("answer", "").strip()
    tools = result.get("tools_used", [])

    # Log for debugging
    print(f"\n{'='*LOG_SEPARATOR_WIDTH}")
    print(f"User Query: {message[:LOG_MESSAGE_PREVIEW_LENGTH]}...")
    print(f"Tools Called: {tools if tools else 'None'}")
    print(f"Response Preview: {answer[:LOG_RESPONSE_PREVIEW_LENGTH]}...")
    print(f"{'='*LOG_SEPARATOR_WIDTH}\n")

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
    color: #555555;
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
        <div id="wizard-title">{UI_TITLE}</div>
        <div id="wizard-greeting">
            {greeting}<br/>
            <span style="font-size:1.1rem;">Hello! How can I assist you today?</span>
        </div>
        """
    )

    chatbot = gr.Chatbot(
        height=GRADIO_CHATBOT_HEIGHT,
        show_label=False,
    )

    gr.ChatInterface(
        fn=agent_reply,
        chatbot=chatbot,
        textbox=gr.Textbox(
            placeholder=UI_PLACEHOLDER,
            scale=GRADIO_TEXTBOX_SCALE,
            submit_btn=UI_SUBMIT_BUTTON
        ),
    )


if __name__ == "__main__":
    # Get theme dynamically from config
    theme_name = GRADIO_THEME
    theme = getattr(gr.themes, theme_name, gr.themes.Soft)()
    demo.launch(theme=theme, css=CUSTOM_CSS)
