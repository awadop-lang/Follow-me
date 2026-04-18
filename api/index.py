function inspectAgent(av) {
            selectedKey = av.key;
            const img = document.getElementById('i-img');
            const btn = document.getElementById('i-btn');
            
            // Photo Fix
            img.style.display = 'none';
            img.src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            img.onload = () => img.style.display = 'block';

            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-key').innerText = av.key;
            
            btn.style.display = 'block';

            // --- NOUVELLE LOGIQUE DE LIEN ROBUSTE ---
            let rawName = av.name.toLowerCase();
            let profilePath;

            if (rawName.includes(' resident')) {
                // Pour "Jean Resident", on ne garde que "jean"
                profilePath = rawName.replace(' resident', '');
            } else {
                // Pour "Jean Smith", on remplace l'espace par un point "jean.smith"
                profilePath = rawName.replace(/ /g, '.');
            }

            btn.onclick = () => window.open(`https://my.secondlife.com/${profilePath}`, '_blank');
        }
