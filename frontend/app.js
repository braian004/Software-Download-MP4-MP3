const API_BASE_URL = "https://software-download-mp4-mp3-2026.onrender.com/api";
const TITULO_ORIGINAL = document.title;
const SOUND_SUCCESS = new Audio("https://assets.mixkit.co/active_storage/sfx/2869/2869-600.wav");

// 🔑 Manejador global para la interrupción de red
let currentAbortController = null;

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("analyzeBtn").addEventListener("click", analizarURL);
    
    document.getElementById("urlInput").addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            analizarURL();
        }
    });

    // Vinculación del evento del nuevo botón de cancelar
    document.getElementById("cancelBtn").addEventListener("click", abortarDescargaActiva);
});

function limpiarUrlYouTube(url) {
    const videoId = extraerVideoId(url);
    if (!videoId) return url;
    
    if (url.includes("shorts/")) {
        return `https://www.youtube.com/shorts/${videoId}`;
    }
    return `https://www.youtube.com/watch?v=${videoId}`;
}

async function analizarURL() {
    let urlInput = document.getElementById('urlInput').value.trim();
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultCard = document.getElementById('resultCard');
    
    if (!urlInput) {
        alert("Por favor, ingresa una URL de YouTube.");
        return;
    }

    urlInput = limpiarUrlYouTube(urlInput);
    document.getElementById('urlInput').value = urlInput; 

    analyzeBtn.disabled = true;
    analyzeBtn.innerText = "ANALYZING...";
    resultCard.classList.add('hidden');
    
    document.getElementById('optionsContainer').classList.remove('hidden');
    document.getElementById('loadingContainer').classList.add('hidden');
    document.title = TITULO_ORIGINAL;

    try {
        const videoId = extraerVideoId(urlInput);
        if (!videoId) {
            throw new Error("No se pudo reconocer un ID de video válido. Verifica la URL.");
        }

        document.getElementById('videoThumb').src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;

        const response = await fetch(`${API_BASE_URL}/formats`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: urlInput })
        });

        if (!response.ok) throw new Error("No se pudieron extraer los formatos multimedia.");

        const data = await response.json();
        
        document.getElementById('videoTitle').innerText = data.title;
        document.getElementById('videoAuthor').innerText = `by YouTube Creator`;
        document.getElementById('videoDuration').innerText = "Ready";

        const videoContainer = document.getElementById('videoQualitiesContainer');
        videoContainer.innerHTML = '';
        
        const backendQualities = data.available_video_qualities; 

        if (backendQualities && backendQualities.length > 0) {
            backendQualities.forEach(q => {
                videoContainer.innerHTML += createInteractiveRow(`MP4 ${q}p`, '2', q); 
            });
        }
        
        videoContainer.innerHTML += createInteractiveRow(`MP4 Mejor disponible`, '2', 'mejor');

        const audioContainer = document.getElementById('audioQualitiesContainer');
        audioContainer.innerHTML = '';
        audioContainer.innerHTML += createInteractiveRow(`MP3 Alta calidad (192kbps)`, '1', 'mejor');

        resultCard.classList.remove('hidden');

    } catch (error) {
        alert(error.message);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerText = "ANALYZE URL";
    }
}

function createInteractiveRow(label, type, quality) {
    return `
        <div class="flex justify-between items-center bg-[#161d2b] border border-white/[0.02] px-4 py-2 rounded-xl text-xs">
            <span class="font-semibold text-slate-300 text-[11px]">${label}</span>
            <button onclick="ejecutarDescarga('${type}', '${quality}', '${label}', this)" 
                    class="bg-[#2563eb] hover:bg-blue-600 text-white font-bold px-3 py-1.5 rounded-lg text-[10px] tracking-wider transition-all shadow-md shadow-blue-600/10 active:scale-[0.90]">
                DOWNLOAD
            </button>
        </div>
    `;
}

async function ejecutarDescarga(type, quality, label, buttonElement) {
    let urlInput = document.getElementById('urlInput').value.trim();
    const videoTitle = document.getElementById('videoTitle').innerText;
    
    const optionsContainer = document.getElementById('optionsContainer');
    const loadingContainer = document.getElementById('loadingContainer');
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    const dataAbsorbedLabel = document.getElementById('dataAbsorbedLabel');
    const downloadingFileName = document.getElementById('downloadingFileName');
    const downloadFormatLabel = document.getElementById('downloadFormatLabel');
    const loadingIcon = document.getElementById('loadingIcon');
    const cancelBtn = document.getElementById('cancelBtn');

    urlInput = limpiarUrlYouTube(urlInput);

    buttonElement.style.backgroundColor = "#10b981"; 
    buttonElement.innerText = "STARTING...";

    optionsContainer.classList.add('hidden');
    loadingContainer.classList.remove('hidden');
    cancelBtn.classList.remove('hidden'); 

    downloadingFileName.innerText = type === "1" ? `${videoTitle}.mp3` : `${videoTitle}.mp4`;
    downloadFormatLabel.innerText = `DESCARGANDO ${label.toUpperCase()}`;
    
    // 🛠️ Restablecer estilos de texto por si la descarga anterior fue exitosa (Evita el texto verde fijo)
    statusText.style.color = "#94a3b8"; 
    
    document.title = "⏳ Processing...";
    loadingIcon.className = "bg-blue-600/10 p-2.5 rounded-xl border border-blue-500/20 text-blue-400 text-lg animate-spin";
    progressBar.style.backgroundColor = "#2563eb";
    progressBar.style.boxShadow = "0 0 20px rgba(37, 99, 235, 0.8)";
    progressBar.style.width = "10%";
    statusText.innerText = "CONVERTING...";
    dataAbsorbedLabel.innerText = "0 MB / Calculando";

    // 🔑 Generar la señal para permitir abortar el hilo de red
    currentAbortController = new AbortController();
    const signal = currentAbortController.signal;

    try {
        const response = await fetch(`${API_BASE_URL}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: urlInput,
                download_type: type,
                quality: quality
            }),
            signal: signal
        });

        if (!response.ok) throw new Error("Error interno en el servidor.");

        const contentLength = response.headers.get('Content-Length');
        let totalBytes = contentLength ? parseInt(contentLength, 10) : 0;
        let totalMB = totalBytes ? (totalBytes / (1024 * 1024)).toFixed(1) + " MB" : "De flujo continuo";

        const reader = response.body.getReader();
        let bytesRecibidos = 0;
        let chunks = [];
        let startTime = Date.now();

        statusText.innerText = "DOWNLOADING...";

        while(true) {
            const { done, value } = await reader.read();
            if (done) break;

            chunks.push(value);
            bytesRecibidos += value.length;

            const elapsedTime = (Date.now() - startTime) / 1000; 
            const mbRecibidos = (bytesRecibidos / (1024 * 1024)).toFixed(1);

            if (totalBytes > 0) {
                const porcentaje = Math.round((bytesRecibidos / totalBytes) * 100);
                const bps = bytesRecibidos / elapsedTime; 
                const bytesRestantes = totalBytes - bytesRecibidos;
                const etaSegundos = bps > 0 ? Math.round(bytesRestantes / bps) : 0;
                
                progressBar.style.width = `${porcentaje}%`;
                dataAbsorbedLabel.innerText = `${mbRecibidos} MB / ${totalMB}`;
                statusText.innerText = `ACTIVO (${etaSegundos}s)`;
                document.title = `(${porcentaje}%) Downloading...`;
            } else {
                let progresoEstimado = Math.min(10 + Math.round(bytesRecibidos / 500000), 95); 
                progressBar.style.width = `${progresoEstimado}%`;
                dataAbsorbedLabel.innerText = `${mbRecibidos} MB absorbidos`;
                statusText.innerText = "STREAMING...";
                document.title = `⏳ ${mbRecibidos} MB...`;
            }
        }

        const blob = new Blob(chunks, { type: 'application/octet-stream' });
        const downloadUrl = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = type === "1" ? `${videoTitle}.mp3` : `${videoTitle}.mp4`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        cancelBtn.classList.add('hidden'); 
        loadingIcon.className = "bg-green-500/10 p-2.5 rounded-xl border border-green-500/20 text-[#00ff87]";
        progressBar.style.backgroundColor = "#00ff87"; 
        progressBar.style.boxShadow = "0 0 30px #00ff87, 0 0 10px #00ff87"; 
        progressBar.style.width = "100%";
        
        statusText.innerText = "SUCCESS ✅";
        statusText.style.color = "#00ff87";
        
        document.title = "✅ ¡DOWNLOAD COMPLETE!";
        SOUND_SUCCESS.play().catch(e => console.log("Bloqueo de audio."));
        
        agregarARecientes(videoTitle, label);

        // 🧠 Limpiar el input de la URL automáticamente para dejar listo el siguiente link
        document.getElementById('urlInput').value = "";

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log("Descarga interrumpida de forma exitosa por el usuario.");
            return;
        }
        
        loadingIcon.className = "bg-red-500/10 p-2.5 rounded-xl border border-red-500/20 text-red-500";
        statusText.innerText = "ERROR ❌";
        statusText.style.color = "#ef4444";
        progressBar.style.width = "0%";
        progressBar.style.boxShadow = "none";
        document.title = "❌ Download Error";
        alert(error.message);
    } finally {
        currentAbortController = null;
        // Restablecer el texto original del botón de la fila interactiva
        buttonElement.disabled = false;
        buttonElement.innerText = "DOWNLOAD";
        buttonElement.style.backgroundColor = "#2563eb";
    }
}

function abortarDescargaActiva() {
    if (currentAbortController) {
        currentAbortController.abort(); 
        currentAbortController = null;
    }

    document.getElementById('optionsContainer').classList.remove('hidden');
    document.getElementById('loadingContainer').classList.add('hidden');
    document.title = TITULO_ORIGINAL;
    
    console.log("Canal cerrado. Frontend y Backend alineados en modo aborto.");
}

function agregarARecientes(titulo, formato) {
    const container = document.getElementById('recentDownloads');
    if (!container) return; // Evita errores si el contenedor no existe en el DOM
    const nuevaTarjeta = document.createElement('div');
    nuevaTarjeta.className = "bg-[#141b29]/60 border border-white/[0.03] p-4 rounded-xl flex justify-between items-center";
    nuevaTarjeta.innerHTML = `
        <div>
            <p class="text-xs font-bold text-slate-200 truncate max-w-[220px]">${titulo}</p>
            <span class="text-[10px] text-slate-500 block mt-0.5">${formato} — Just now</span>
        </div>
        <button class="bg-[#18202e] text-[#00ff87] text-[10px] font-bold px-3 py-1.5 rounded-lg border border-white/[0.02] cursor-not-allowed flex items-center gap-1"><i class="fa-solid fa-check"></i> [Success]</button>
    `;
    container.insertBefore(nuevaTarjeta, container.firstChild);
}

function extraerVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|shorts\/)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}