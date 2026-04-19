import gradio as gr
import pandas as pd
import plotly.express as px
import time
from fastapi import FastAPI, Request
import os
import uvicorn

# 1. Créer l'objet FastAPI D'ABORD
app = FastAPI() 

# 2. Ton stockage et tes fonctions (get_plot, etc.)
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

# ... (insère ici tes fonctions get_plot, update_api, etc.) ...

# 3. Créer l'interface Gradio
with gr.Blocks() as demo:
    # ... ton interface ...
    pass

# 4. Monter Gradio sur FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# 5. Lancer le serveur
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
