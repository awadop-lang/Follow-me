from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
db = {"avatars": []}

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SL Region Monitor Pro</title>
    <style>
        body { 
            background: #050505; color: #00ff41; 
            font-family: 'Courier New', monospace; 
            display: flex; flex-direction: column; align-items: center; 
            height: 100vh; margin: 0; padding: 20px;
        }
        .main-container { 
            display: flex; flex-direction: row; align-items: flex-start; 
            gap: 30px; background: rgba(0, 20, 0, 0.5); 
            padding: 20px; border: 1px solid #004411; border-radius: 10px;
        }
        .radar-side { position: relative; width: 256px; height: 256px; }
        canvas { border: 1px solid #004411; border-radius: 50%; background: black; }
        
        .list-side { 
            width: 200px; height: 256px; 
            border-left: 1px solid #004411; padding-left: 20px;
            overflow-y: auto;
        }
        .list-side h3 { font-size: 14px; text-decoration: underline; margin-top: 0; }
        .avatar-item { font-size: 12px; margin-bottom: 5px; border-bottom: 1px solid #002200; padding-bottom: 2px; }
        
        #status { margin-top: 20px; font-size: 0.8em; color: #008822; }
        h2 { text-shadow: 0 0 10px #00ff41; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h2>REGION MONITOR SYSTEM</h2>
    
    <div class="main-container">
        <div class="radar-side">
            <canvas id="radar" width="256" height="256"></canvas>
        </div>

        <div class="list-side">
            <h3>AGENTS EN LIGNE</h3>
            <div id="avatar-list"></div>
        </div>
    </div>

    <div id="status">SCANNING EN COURS...</div>

    <script>
        const canvas = document.getElementById('radar');
        const ctx = canvas.getContext('2d');
        const listDiv = document.getElementById('avatar-list');

        async function updateData() {
            try {
                const response = await fetch('/api');
                const avatars = await response.json();
                
                document.getElementById('status').innerText = "DERNIER SCAN : " + avatars.length + " AGENT(S)";
                
                // 1. Mise à jour de la liste de noms
                listDiv.innerHTML = "";
                if (avatars.length === 0) {
                    listDiv.innerHTML = "<span style='color:#444'>Aucun agent</span>";
                }

                // 2. Dessin sur le Radar
                ctx.clearRect(0, 0, 256, 256);
                // Dessin d'une grille simple
                ctx.strokeStyle = "#002200";
                ctx.strokeRect(0,0,256,256);

                avatars.forEach(av => {
                    // Ajouter à la liste
                    const item = document.createElement('div');
                    item.className = 'avatar-item';
                    item.innerText = "> " + av.name;
                    listDiv.appendChild(item);

                    // Dessiner le point
                    const x = av.x;
                    const y = 256 - av.y;
                    ctx.fillStyle = "#ff0000";
                    ctx.beginPath();
                    ctx.arc(x, y, 4, 0, Math.PI * 2);
                    ctx.fill();
                    
                    ctx.fillStyle = "white";
                    ctx.font = "9px Arial";
                    ctx.fillText(av.name, x + 6, y + 2);
                });
            } catch (err) { console.log("Erreur..."); }
        }
        setInterval(updateData, 2000);
    </script>
</body>
</html>
