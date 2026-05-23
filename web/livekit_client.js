// LiveKit Client Logic for LiveTalking

let currentRoom = null;

async function startLiveKit() {
    console.log("Starting LiveKit connection...");
    
    // 1. Get Token from Backend
    const identity = "user_" + Math.floor(Math.random() * 10000);
    const response = await fetch(`${window.CONFIG.API_BASE_URL}/token?identity=${identity}`);
    const data = await response.json();
    
    if (data.code !== 0) {
        console.error("Failed to get LiveKit token:", data.msg);
        return;
    }
    
    const { token, url } = data.data;
    const serverUrl = url || window.CONFIG.LIVEKIT_URL;

    // 2. Connect to Room
    currentRoom = new LivekitClient.Room({
        adaptiveStream: true,
        dynacast: true,
    });

    // Handle track subscriptions
    currentRoom.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log(`Subscribed to track ${track.kind} from ${participant.identity}`);
        if (track.kind === 'video') {
            const videoElement = document.getElementById('video');
            track.attach(videoElement);
        } else if (track.kind === 'audio') {
            const audioElement = document.getElementById('audio');
            track.attach(audioElement);
        }
    });

    await currentRoom.connect(serverUrl, token);
    console.log("Connected to LiveKit room:", currentRoom.name);
    
    // Handle Autoplay: Resume AudioContext after connection
    if (LivekitClient.isBrowserSupported) {
        currentRoom.startAudio();
    }

    // Set sessionid to '0' to match the backend's default session
    document.getElementById('sessionid').value = "0";
    
    window.onWebRTCConnected();
}

// Override the global start function
const originalStart = window.start;
window.start = function() {
    if (window.CONFIG.TRANSPORT === 'livekit') {
        startLiveKit().catch(console.error);
        document.getElementById('start').style.display = 'none';
        document.getElementById('stop').style.display = 'inline-block';
    } else {
        originalStart();
    }
};

// Override the global stop function
const originalStop = window.stop;
window.stop = function() {
    if (window.CONFIG.TRANSPORT === 'livekit' && currentRoom) {
        currentRoom.disconnect();
        document.getElementById('stop').style.display = 'none';
        document.getElementById('start').style.display = 'inline-block';
    } else {
        originalStop();
    }
};
