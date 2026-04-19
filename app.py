import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

# 1. CSS MODERN & SOBER (Glassmorphism & Shadows)
CSS = """
/* Import de la police moderne 'Inter' */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

/* Style global */
.gradio-container {
    background-color: #0d1117 !important; /* Fond sombre doux style GitHub Dark */
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: #c9d1d9 !important;
}

/* Titre principal moderne */
.main-title {
    font-weight: 600;
    font-size: 2.2em;
    color: #f0f6fc;
    margin-bottom: 20px;
    letter-spacing: -1px;
}

/* Style des cartes (Effet de Verre + Ombre douce) */
.glass-card {
    background: rgba(22, 27, 34, 0.7); /* Translucide */
    border: 1px solid rgba(48, 54, 61, 0.8);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5); /* Ombre douce portée */
    backdrop-filter: blur(10px); /* Effet de flou dépoli (Glassmorphism) */
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* Effet de survol sur les cartes */
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
}

/* Style compact pour le tableau */
.table-container {
    font-size: 0.9em;
    border-radius: 8px;
    overflow: hidden;
}

/* Texte de statut épuré */
.stat-text {
    font-size: 1.1em;
    font-weight: 400;
    color: #8b949e;
}

/* Label de cible sélectionnée */
.selected-label {
    color: #58a6ff; /* Bleu accent moderne */
    font-weight: 600;
}
"""

def get_radar_plot():
    now = time.time()
    fig = go.Figure()

    # Cercles de distance minimalistes
    for r in [50, 100, 150, 200]:
        fig.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, 
                      line=dict(color="rgba(48, 54, 61, 0.6)", width=1, dash='dot'))

    status_text = "🟢 SIGNAL ACTIF"
    df_display = pd.DataFrame(columns=["Nom", "X", "Y", "Altitude"])

    if data_store["last_packet_time"] == 0 or (now - data_store["last_packet_time"] > 20):
        status_text = "🔴 HORS LIGNE"
        fig.add_annotation(text="ATTENTE DE DONNÉES...", x=0, y=0, showarrow=False, font=dict(size=18, color="#8b949e"))
    else:
        data = data_store["avatars"]
        if data:
            for d in data:
                rel_x = d["X"] - 128
                rel_y = d["Y"] - 128
                
                # Interaction : Si sélectionné, changement de couleur sobre
                is_selected = (d["Avatar"] == data_store["selected"])
                # Bleu électrique moderne si sélectionné, gris clair sinon
                color = "#58a6ff" if is_selected else "#f0f6fc"
                size = 14 if is_selected else 10
                
                # Points minamalistes (plus propre que des triangles)
                fig.add_trace(go.Scatter(
                    x=[rel_x], y=[rel_y],
                    mode='markers',
                    marker=dict(size=size, color=color, 
                                line=dict(width=2 if is_selected else 1, color="#f0f6fc")),
                    hoverinfo="text",
                    text=[d["Avatar"]],
                ))
            
            # Préparation du tableau sobre
            df_display = pd.DataFrame([
                {"Nom": d["Avatar"], "X": round(d["X"],1), "Y": round(d["Y"],1), "Altitude": round(d["Z"],1)} 
                for d in data
            ])

    # Configuration du graphique ultra-sobre
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(range=[-140, 140], visible=False, zeroline=False),
        yaxis=dict(range=[-140, 140], visible=False, zeroline=False, scaleanchor="x", scaleratio=1),
        showlegend=False, width=580, height=580
    )

    return fig, df_display, status_text

# Fonction de sélection (Lock target)
def on_select(evt: gr.SelectData):
    data_store["selected"] = evt.value
    # On retourne un HTML stylisé pour la cible
    return f"CIBLE VERROUILLÉE : <span class='selected-label'>{evt.value}</span>"

# 2. CONSTRUCTION DE L'INTERFACE MODERNE
with gr.Blocks(css=CSS) as demo:
    # Conteneur principal avec padding
    with gr.Column(elem_id="main_container", padding=True):
        gr.HTML("<h1 class='main-title' style='text-align:center;'>🛰️ Local Scanner System</h1>")
        
        with gr.Row():
            # Colonne Radar (La carte flottante)
            with gr.Column(scale=3, elem_classes="glass-card"):
                radar_map = gr.Plot(label="Radar View", show_label=False)
            
            # Colonne Données
            with gr.Column(scale=2):
                # Carte de Statut (Verre)
                with gr.Group(elem_classes="glass-card"):
                    with gr.Row():
                        gr.HTML("<span class='stat-text'>📟 État :</span>")
                        connection_status = gr.Markdown("🟢 SIGNAL ACTIF", elem_classes="stat-text")
                    
                    # Information de Cible (Verre)
                    gr.HTML("<hr style='border: 0; border-top: 1px solid rgba(48, 54, 61, 0.5); margin: 15px 0;'>")
                    target_info = gr.HTML("<span class='stat-text'>🎯 Cliquez sur un nom pour tracker</span>")
                
                # Tableau (Épuré)
                gr.HTML("<br>")
                gr.Markdown("### 👥 Localisation Complète")
                target_table = gr.Dataframe(
                    headers=["Nom", "X", "Y", "Altitude"],
                    interactive=False,
                    elem_classes="table-container"
                )

    # Mise à jour automatique (toutes les 3 secondes)
    gr.Timer(3).tick(get_radar_plot, outputs=[radar_map, target_table, connection_status])
    
    # Interaction : Sélection dans le tableau
    target_table.select(on_select, outputs=target_info)

# 3. FASTAPI & UPLOAD (Inchangé)
@app.post("/update")
async def update(request: Request):
    body = await request.body()
    content = body.decode("utf-8")
    data_store["last_packet_time"] = time.time()
    new_data = []
    if content and content != "empty":
        for entry in content.split(";"):
            parts = entry.split("|")
            if len(parts) == 2:
                name, coords = parts[0], parts[1].split(",")
                new_data.append({"Avatar": name, "X": float(coords[0]), "Y": float(coords[1]), "Z": float(coords[2])})
    data_store["avatars"] = new_data
    return {"status": "ok"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
