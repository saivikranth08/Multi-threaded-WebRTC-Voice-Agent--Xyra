/* ─────────────────────────────────────────────
   XYRA — Holographic Orb Dashboard
   Three.js glowing bubbles + LiveKit voice sync
───────────────────────────────────────────── */

// ── Scene Setup ──────────────────────────────────────────────────────────────
const canvas   = document.getElementById("orb-canvas");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x000000, 1);

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 0, 5);

const clock = new THREE.Clock();

// ── Lighting ─────────────────────────────────────────────────────────────────
const ambientLight = new THREE.AmbientLight(0x111122, 1.5);
scene.add(ambientLight);

const cyanLight  = new THREE.PointLight(0x00e5ff, 3, 8);
cyanLight.position.set(0, 0, 0);
scene.add(cyanLight);

const purpleLight = new THREE.PointLight(0x7b2ff7, 2, 6);
purpleLight.position.set(-2, 1, 1);
scene.add(purpleLight);

const blueLight = new THREE.PointLight(0x0066ff, 2, 6);
blueLight.position.set(2, -1, 1);
scene.add(blueLight);

// ── Orb Factory ──────────────────────────────────────────────────────────────
function createOrb(radius, color, opacity, detail = 3) {
    const geo = new THREE.IcosahedronGeometry(radius, detail);
    const mat = new THREE.MeshPhongMaterial({
        color,
        transparent: true,
        opacity,
        shininess: 120,
        specular: new THREE.Color(0xffffff),
        side: THREE.FrontSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);
    return mesh;
}

function createWireOrb(radius, color, opacity) {
    const geo = new THREE.IcosahedronGeometry(radius, 1);
    const mat = new THREE.MeshBasicMaterial({
        color,
        wireframe: true,
        transparent: true,
        opacity,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);
    return mesh;
}

// ── Main Central Orb ──────────────────────────────────────────────────────────
const mainOrbGeo = new THREE.SphereGeometry(1.3, 32, 32);
const mainOrbMat = new THREE.MeshPhongMaterial({
    color: 0x00e5ff,
    transparent: true,
    opacity: 0.35,
    shininess: 120,
    specular: new THREE.Color(0x00e5ff),
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
});
const mainOrb = new THREE.Mesh(mainOrbGeo, mainOrbMat);
scene.add(mainOrb);

const mainOrbInner = createOrb(0.9, 0x0099cc, 0.15, 3);
const mainOrbCore  = createOrb(0.4, 0xffffff, 0.30, 2);
const mainWire     = createWireOrb(1.38, 0x00e5ff, 0.06);


// ── Floating Bubble Satellites ────────────────────────────────────────────────
const bubbles = [];
const bubbleData = [
    { radius: 0.38, color: 0x7b2ff7, opacity: 0.22, orbitR: 2.1, speed: 0.35, phase: 0.0,   yOffset: 0.4  },
    { radius: 0.28, color: 0x00e5ff, opacity: 0.18, orbitR: 2.5, speed: 0.25, phase: 2.1,   yOffset: -0.5 },
    { radius: 0.45, color: 0x0066ff, opacity: 0.15, orbitR: 1.8, speed: 0.45, phase: 4.2,   yOffset: 0.2  },
    { radius: 0.22, color: 0x00ffaa, opacity: 0.20, orbitR: 2.8, speed: 0.20, phase: 1.0,   yOffset: 0.8  },
    { radius: 0.32, color: 0xff44cc, opacity: 0.16, orbitR: 2.3, speed: 0.30, phase: 3.5,   yOffset: -0.3 },
    { radius: 0.18, color: 0x00e5ff, opacity: 0.25, orbitR: 1.5, speed: 0.55, phase: 5.8,   yOffset: -0.7 },
];

bubbleData.forEach(bd => {
    const mesh     = createOrb(bd.radius, bd.color, bd.opacity, 2);
    const wireFrame = createWireOrb(bd.radius * 1.05, bd.color, 0.06);
    bubbles.push({ mesh, wireFrame, ...bd, t: bd.phase });
});

// ── Particle System (Background Stars) ───────────────────────────────────────
function createParticles() {
    const count = 300;
    const geo   = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
        positions[i * 3]     = (Math.random() - 0.5) * 20;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
        color: 0x00e5ff,
        size: 0.025,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
    });
    const particles = new THREE.Points(geo, mat);
    scene.add(particles);
    return particles;
}
const particles = createParticles();

// ── Audio Analysis State ──────────────────────────────────────────────────────
let audioContext = null;
let analyser     = null;
let dataArray    = null;
let volume       = 0;   // 0..1 smoothed

// ── LiveKit State ─────────────────────────────────────────────────────────────
let room = null;

// ── UI Elements ───────────────────────────────────────────────────────────────
const connectBtn  = document.getElementById("connect-btn");
const btnText     = connectBtn.querySelector(".btn-text");
const statusBadge = document.getElementById("status-badge");
const waveCanvas  = document.getElementById("wave-canvas");
const waveCtx     = waveCanvas.getContext("2d");
let   wavePhase   = 0;

// ── Event Listeners ───────────────────────────────────────────────────────────
connectBtn.addEventListener("click", toggleConnection);
window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});


// ── Animation Loop ────────────────────────────────────────────────────────────
function animate() {
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    // Smooth volume from analyser
    let rawVol = 0;
    if (analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        rawVol = Math.min(1.0, (sum / dataArray.length) / 80.0);
    }
    volume += (rawVol - volume) * 0.15; // smooth

    // ── Main Orb Animation ────────────────────────────────────────────────────
    const breathe   = 1 + Math.sin(t * 1.4) * 0.03;
    const voiceBoost = 1 + volume * 0.55;
    const scale = breathe * voiceBoost;

    mainOrb.scale.setScalar(scale);
    mainOrbInner.scale.setScalar(scale * 0.98);
    mainOrbCore.scale.setScalar(scale * (0.9 + volume * 0.4));
    mainWire.scale.setScalar(scale * 1.02);

    mainOrb.rotation.y = t * 0.04;

    mainOrbInner.rotation.y = -t * 0.08;
    mainOrbInner.rotation.z =  t * 0.05;
    mainWire.rotation.y    =  t * 0.10;
    mainWire.rotation.x    = -t * 0.07;

    // Color shift on voice
    const baseColor   = new THREE.Color(0x00e5ff);
    const activeColor = new THREE.Color(0x7b2ff7);
    mainOrb.material.color.lerpColors(baseColor, activeColor, volume * 0.7);
    mainOrbCore.material.color.lerpColors(new THREE.Color(0xffffff), new THREE.Color(0x00e5ff), volume);

    // Light intensity on voice
    cyanLight.intensity  = 3 + volume * 6;
    purpleLight.intensity = 2 + volume * 4;

    // ── Bubble Satellites ─────────────────────────────────────────────────────
    bubbles.forEach((b, i) => {
        b.t += b.speed * clock.getDelta() * 0.5 + 0.004;

        const x = Math.cos(b.t) * b.orbitR;
        const z = Math.sin(b.t) * b.orbitR * 0.5;
        const y = b.yOffset + Math.sin(b.t * 1.3 + b.phase) * 0.3;

        b.mesh.position.set(x, y, z);
        b.wireFrame.position.copy(b.mesh.position);

        const bubbleScale = 1 + Math.sin(t * 2 + b.phase) * 0.06 + volume * 0.25;
        b.mesh.scale.setScalar(bubbleScale);
        b.wireFrame.scale.setScalar(bubbleScale * 1.03);

        b.mesh.rotation.y = t * 0.3 * (i % 2 === 0 ? 1 : -1);
        b.wireFrame.rotation.y = -b.mesh.rotation.y;
    });

    // ── Particles slow drift ─────────────────────────────────────────────────
    particles.rotation.y = t * 0.015;
    particles.rotation.x = t * 0.008;

    // ── Siri Wave Visualizer ─────────────────────────────────────────────────
    drawWave(t);

    renderer.render(scene, camera);
}

// ── Siri Wave ─────────────────────────────────────────────────────────────────
function drawWave(t) {
    const w = waveCanvas.width  = waveCanvas.offsetWidth;
    const h = waveCanvas.height = waveCanvas.offsetHeight;

    waveCtx.clearRect(0, 0, w, h);
    wavePhase += 0.05 + volume * 0.1;

    const waves = [
        { color: `rgba(0,229,255,0.5)`,  freq: 3, amp: 10 + volume * 20, phaseOff: 0     },
        { color: `rgba(123,47,247,0.35)`, freq: 5, amp: 7  + volume * 14, phaseOff: 1.0   },
        { color: `rgba(0,102,255,0.25)`,  freq: 7, amp: 5  + volume * 10, phaseOff: 2.0   },
    ];

    waves.forEach(wave => {
        waveCtx.beginPath();
        waveCtx.lineWidth = 1.5;
        waveCtx.strokeStyle = wave.color;

        for (let x = 0; x < w; x++) {
            const nx = x / w;
            const envelope = Math.sin(nx * Math.PI);
            const y = h / 2 + Math.sin(nx * Math.PI * wave.freq + wavePhase + wave.phaseOff)
                              * wave.amp * envelope;
            x === 0 ? waveCtx.moveTo(x, y) : waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();
    });
}

// ── LiveKit Connection ────────────────────────────────────────────────────────
async function toggleConnection() {
    if (room && room.state === "connected") {
        await disconnect();
        return;
    }

    connectBtn.disabled = true;
    btnText.innerText   = "Connecting...";
    statusBadge.innerText   = "Connecting";
    statusBadge.className   = "badge connecting";

    try {
        // ── Step 1: Request microphone permission explicitly first ──
        // This makes Chrome show the Allow/Deny popup before anything else
        let micStream = null;
        try {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            micStream.getTracks().forEach(t => t.stop()); // Release immediately — LiveKit will re-request
        } catch (micErr) {
            throw new Error(`Microphone Error: ${micErr.name} - ${micErr.message}`);
        }

        // ── Step 2: Fetch LiveKit token from local server ──
        const res  = await fetch("/api/token");
        const data = await res.json();
        if (data.error) throw new Error(`Token error: ${data.error}`);

        // ── Step 3: Init audio context ──
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioContext.state === "suspended") await audioContext.resume();

        // ── Step 4: Connect LiveKit room ──
        room = new LivekitClient.Room({ adaptiveStream: true, dynacast: true });

        room.on("trackSubscribed", (track) => {
            if (track.kind === "audio") {
                const el = track.attach();
                document.body.appendChild(el);

                try {
                    analyser              = audioContext.createAnalyser();
                    analyser.fftSize      = 64;
                    dataArray             = new Uint8Array(analyser.frequencyBinCount);
                    
                    // Use MediaStreamSource directly from the WebRTC track instead of the audio element
                    const stream = new MediaStream([track.mediaStreamTrack]);
                    const src = audioContext.createMediaStreamSource(stream);
                    src.connect(analyser);
                    // Do NOT connect to destination, as the <audio> element is already playing it
                } catch (e) {
                    console.error("Audio Analyser Error:", e);
                }
            }
        });

        room.on("disconnected", handleDisconnect);
        room.on("dataReceived", handleDataReceived);

        await room.connect(data.url, data.token);
        await room.localParticipant.setMicrophoneEnabled(true);

        connectBtn.disabled   = false;
        btnText.innerText     = "End Session";
        connectBtn.className  = "connect-btn danger";
        statusBadge.innerText = "Live";
        statusBadge.className = "badge connected";

    } catch (err) {
        console.error("Connection failed:", err);
        alert(`Connection failed: ${err.message}`);
        handleDisconnect();
    }
}

async function disconnect() {
    if (room) { room.disconnect(); room = null; }
    handleDisconnect();
}

function handleDisconnect() {
    analyser  = null;
    dataArray = null;
    volume    = 0;

    connectBtn.disabled   = false;
    btnText.innerText     = "Start Voice Session";
    connectBtn.className  = "connect-btn";
    statusBadge.innerText = "Offline";
    statusBadge.className = "badge disconnected";
}

// ── Start ─────────────────────────────────────────────────────────────────────
animate();

// ── Widget Rendering (Phase 3) ────────────────────────────────────────────────
function handleDataReceived(payload, participant, kind, topic) {
    console.log("Data packet received. Topic:", topic, "Payload size:", payload.byteLength);
    try {
        const strData = new TextDecoder().decode(payload);
        const event = JSON.parse(strData);
        
        if (event && event.type === "render_widget") {
            console.log("Rendering widget:", event.widget, event.data);
            renderWidget(event.widget, event.data);
        }
    } catch (e) {
        console.error("Failed to parse data received from LiveKit room:", e);
    }
}

function renderWidget(widgetType, data) {
    const container = document.getElementById("dashboard-container");
    if (!container) return;

    // Create the widget wrapper
    const widget = document.createElement("div");
    widget.className = "widget";

    let innerHTML = "";

    if (widgetType === "weather") {
        let city = data.location || 'Unknown';
        let condition = 'N/A';
        let temp = 'N/A';
        let feels = 'N/A';
        let humidity = 'N/A';
        let wind = 'N/A';
        let lat = null;
        let lon = null;

        // Parse fields from weather tool output string
        const lines = data.result.split('\n');
        lines.forEach(line => {
            if (line.includes('Weather in')) {
                city = line.replace(/🌍 Weather in /, '').trim();
            } else if (line.includes('Condition')) {
                condition = line.split(':')[1]?.trim() || 'N/A';
            } else if (line.includes('Temperature')) {
                const parts = line.split(':')[1]?.trim().split('(') || [];
                temp = parts[0]?.trim() || 'N/A';
                feels = parts[1]?.replace('Feels like ', '')?.replace(')', '')?.trim() || 'N/A';
            } else if (line.includes('Humidity')) {
                humidity = line.split(':')[1]?.trim() || 'N/A';
            } else if (line.includes('Wind Speed')) {
                wind = line.split(':')[1]?.trim() || 'N/A';
            } else if (line.includes('Coordinates')) {
                const coords = line.split(':')[1]?.trim().split(',');
                lat = parseFloat(coords[0]);
                lon = parseFloat(coords[1]);
            }
        });

        innerHTML = `
            <div class="widget-title">SYSTEM TELEMETRY: WEATHER</div>
            <div class="widget-content">
                <div style="font-size: 11px; text-transform: uppercase; color: rgba(0, 229, 255, 0.6); margin-bottom: 4px; letter-spacing: 1px;">LOCATION</div>
                <div style="font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 15px; letter-spacing: 0.5px;">${city}</div>
                
                <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px;">
                    <div>
                        <div style="font-size: 10px; color: rgba(0, 229, 255, 0.6); letter-spacing: 1px;">TEMPERATURE</div>
                        <div style="font-size: 24px; font-weight: 800; color: #00e5ff; text-shadow: 0 0 10px rgba(0, 229, 255, 0.3); margin-top: 2px;">${temp}</div>
                        <div style="font-size: 11px; color: rgba(255, 255, 255, 0.5); margin-top: 1px;">Feels like ${feels}</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: rgba(0, 229, 255, 0.6); letter-spacing: 1px;">CONDITION</div>
                        <div style="font-size: 15px; font-weight: 700; color: #fff; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.5px;">${condition}</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; padding-top: 12px; border-top: 1px solid rgba(0, 229, 255, 0.15);">
                    <div>
                        <div style="font-size: 10px; color: rgba(0, 229, 255, 0.6); letter-spacing: 0.5px;">HUMIDITY</div>
                        <div style="font-size: 14px; font-weight: 700; color: #fff; margin-top: 2px;">${humidity}</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: rgba(0, 229, 255, 0.6); letter-spacing: 0.5px;">WIND SPEED</div>
                        <div style="font-size: 14px; font-weight: 700; color: #fff; margin-top: 2px;">${wind}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (widgetType === "news") {
        const newsLines = data.result.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0 && !line.toLowerCase().includes('news for') && !line.includes('---'));

        const itemsHtml = newsLines.slice(0, 6).map(item => {
            let cleanItem = item.replace(/^📌|^🔗|^📝|^\d+\.\s*|^[-*]\s*/g, '').trim();
            if (item.startsWith('🔗')) {
                return '';
            }
            if (item.startsWith('📝')) {
                return `<div style="font-size: 11px; color: rgba(255, 255, 255, 0.6); margin-bottom: 12px; padding-left: 10px; border-left: 2px solid rgba(0, 229, 255, 0.3); line-height: 1.4;">${cleanItem}</div>`;
            }
            return `<div class="news-item" style="font-weight: 700; color: #00e5ff; font-size: 13px; margin-top: 6px; letter-spacing: 0.3px; line-height: 1.3;">${cleanItem}</div>`;
        }).filter(html => html !== '').join('');

        // News telemetry layout build
        innerHTML = `
            <div class="widget-title">SECURE FEED: NEWS (${(data.topic || 'AI').toUpperCase()})</div>
            <div class="widget-content" style="max-height: 250px; overflow-y: auto; padding-right: 4px;">
                ${itemsHtml}
            </div>
        `;
    } else {
        innerHTML = `
            <div class="widget-title">TELEMETRY DATA: ${widgetType.toUpperCase()}</div>
            <div class="widget-content" style="font-family: monospace; font-size: 12px; color: #00e5ff;">${JSON.stringify(data.result || data)}</div>
        `;
    }

    widget.innerHTML = innerHTML;

    // Clear old widgets if we have too many
    if (container.children.length >= 3) {
        container.removeChild(container.firstChild);
    }

    container.appendChild(widget);

    // Auto-remove widget after 30 seconds
    setTimeout(() => {
        if (container.contains(widget)) {
            widget.style.animation = "fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards";
            setTimeout(() => {
                if (container.contains(widget)) {
                    container.removeChild(widget);
                }
            }, 600);
        }
    }, 30000);
}

