import gradio as gr
from main import app
import uvicorn
import os

# Create a simple Gradio interface for the Space's front page
with gr.Blocks(title="LinkedIn Company Agent API") as demo:
    gr.Markdown("# 🔍 LinkedIn Company Agent — Backend API")
    gr.Markdown("""
    This Hugging Face Space hosts the **FastAPI Backend** for the LinkedIn Company Agent.
    
    ### 🚀 API Endpoints
    - **Documentation**: [Open API Docs](/docs)
    - **Health Check**: [Check Status](/health)
    
    The React frontend (hosted on Vercel) connects to this API to perform searches, manage leads, and generate AI messages.
    """)
    
    with gr.Accordion("System Status", open=False):
        gr.Markdown(f"**Port**: 7860 (Hugging Face Default)")
        gr.Markdown(f"**SDK**: Gradio (FastAPI Mounted)")

# Mount the Gradio app into the FastAPI app
# This allows both to coexist on the same port (7860)
# Gradio will be at the root (/), and FastAPI routes will be accessible as usual.
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Hugging Face Spaces automatically provide the PORT environment variable
    # but we default to 7860 which is the standard.
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
