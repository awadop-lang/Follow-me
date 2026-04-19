import os # Ajoute cet import en haut du fichier

# ... (tout ton code précédent reste identique) ...

# Montage de l'app Gradio dans FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Récupère le port de Render ou utilise 7860 par défaut
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
