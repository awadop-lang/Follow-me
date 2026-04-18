# Remplace les lignes @app.route par celle-ci (Route universelle)
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    # Si c'est un POST, c'est l'objet Second Life qui parle
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

    # Si c'est un GET, on affiche l'interface ou l'API JSON
    if path == "api":
        if 'user' not in session: return jsonify({"error": "unauth"}), 401
        return jsonify(users_db.get(session.get('user', ''), {}))
    
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML)
