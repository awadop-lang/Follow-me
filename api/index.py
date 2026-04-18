# ... (Code précédent) ...

# Nouvelle structure pour les statuts globaux
global_statuses = {} 

@app.route('/update_global_status', methods=['POST'])
def update_global_status():
    data = request.get_json()
    uuid = data.get('uuid')
    is_online = data.get('online') == "1"
    global_statuses[uuid] = {
        "online": is_online,
        "last_check": time.time()
    }
    return "OK"

@app.route('/get_watchlist_uuids')
def get_watchlist_uuids():
    op = request.args.get('operator_id')
    if op in users_db:
        # On renvoie juste la liste des UUIDs pour que le script LSL les interroge
        uuids = [w['uuid'] for w in users_db[op]['watchlist'] if 'uuid' in w]
        return jsonify(uuids)
    return "[]"

# --- Dans INTERFACE_HTML, modifie la logique d'affichage de la Watchlist ---
# Remplace la partie JS qui génère la Watchlist par celle-ci :
"""
    const isLocal = avatars.find(a => a.name === w.name);
    const gStatus = data.global_statuses[w.uuid] || {online: false};
    
    let statusLabel = "";
    if (isLocal) {
        statusLabel = '<span class="status-badge st-local">SUR SITE (RADAR)</span>';
    } else if (gStatus.online) {
        statusLabel = '<span class="status-badge st-global">EN LIGNE (AUTRE REGION)</span>';
    } else {
        statusLabel = '<span class="status-badge st-off">DÉCONNECTÉ</span>';
    }
"""
