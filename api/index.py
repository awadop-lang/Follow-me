@app.route('/', methods=['GET', 'POST'])
def home():
    # 1. Traitement des données venant de Second Life (POST)
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        op_id = data.get("operator_id", "").lower()
        
        if op_id in users_db:
            users_db[op_id].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': data.get('avatars', [])
            })
            return "OK", 200
        return "USER_NOT_FOUND", 404

    # 2. Affichage de l'interface pour toi (GET)
    if 'user' not in session: 
        return redirect(url_for('login'))
    return render_template_string(HTML_DASH)
