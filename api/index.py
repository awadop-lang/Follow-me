from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
# Mémoire vive pour stocker les positions
db = {"avatars": []}

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SL Region Monitor</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Courier New', monospace; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; overflow: hidden; }
        .radar-container { position: relative; width: 300px; height: 300px; border: 2px solid #004411; border-radius: 50%; box-shadow: 0 0 20px #002200; background: radial-gradient(circle, #001100 0%, #000000 70%); }
        canvas { position: absolute; top: 22px; left: 22px; }
        .grid { position: absolute; width: 100%; height: 100%; border-radius: 50%; background-image: linear-gradient(#004411 1px, transparent 1px), linear-gradient(90deg, #004411 1px, transparent 1px); background-size: 50px 50px; background-position: center; opacity: 0.3; }
        h2 { text-shadow: 0 0 10px #00ff41; letter-spacing: 3px; margin-bottom: 10px; }
        #status { margin-top: 15px; font-size: 0.9em; color: #008822; }
    </style>
</head>
<body>
    <h2>REGION MONITOR</h2>
    <div class="radar-container">
        <div class="grid"></div>
        <canvas id="radar" width="256" height="256"></canvas>
    </div>
    <div id="status">SCANNING...</div>

    <script>
        const canvas = document.getElementById('radar');
        const ctx = canvas.getContext('2d');

        async function updateRadar() {
            try {
                const response = await fetch('/api');
                const avatars = await response.json();
                
                document.getElementById('status').innerText = avatars.length + " AGENT(S) DETECTE(S)";
                ctx.clearRect(0, 0, 256, 256);

                avatars.forEach(av => {
                    const x = av.x;
                    const y = 256 - av.y; // Inversion pour coordonnées SL

                    // Dessin de l'avatar (point rouge brillant)
                    ctx.shadowBlur = 10;
                    ctx.shadowColor = "red";
                    ctx.fillStyle = "#ff0000";
                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, Math.PI * 2);
                    ctx.fill();

                    // Nom de l'avatar
                    ctx.shadowBlur = 0;
                    ctx.fillStyle = "#ffffff";
                    ctx.font = "bold 10px Arial";
                    ctx.fillText(av.name.toUpperCase(), x + 8, y + 3);
                });
            } catch (err) { console.log("Erreur de synchro..."); }
        }
        setInterval(updateRadar, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle_api():
    if request.method == 'POST':
        db["avatars"] = request.json
        return "OK", 200
    return jsonify(db["avatars"])

@app.route('/')
def home():
    return render_template_string(HTML)
