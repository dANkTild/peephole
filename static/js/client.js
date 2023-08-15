var pc = null;
var ws = new WebSocket(location.origin.replace("http", 'ws') + "/ws");
var loading = null;

function negotiate() {
    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });
    return pc.createOffer().then(function (offer) {
        return pc.setLocalDescription(offer);
    }).then(function () {
        // wait for ICE gathering to complete
        return new Promise(function (resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function () {
        var offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function (response) {
        return response.json();
    }).then(function (answer) {
        return pc.setRemoteDescription(answer);
    }).catch(function (e) {
        console.log(e);
    });
}

function start() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }];
    // config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }];

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', function (evt) {
        if (evt.track.kind == 'video') {
            console.log(evt.streams[0]);
            document.getElementById('video').srcObject = evt.streams[0];
        }
    });

    negotiate();

    // await document.getElementById("video").play();
}

function stop() {
    setTimeout(function () {
        pc.close();
        console.log("stoped");
    }, 500);
}

ws.onmessage = function (event) {
    req = JSON.parse(event.data);
    if (req.trigger == "saved") {
        let notif = document.querySelector(".saved_notif");
        notif.classList.remove("hide");
        setTimeout(function () {
            notif.classList.add("hide");
        }, 1500);
    } else if (req.trigger == "video") {
        let btn = document.querySelector(".record_btn");
        if (req.is_recording) {
            btn.classList.add("text-primary");
        } else {
            btn.classList.remove("text-primary");
        }
    } else if (req.trigger == "face_added") {
        if (req.success) {
            let img_container = document.createElement("div");
            img_container.setAttribute("class", "col")
            img_container.innerHTML = `<div class="card h-100">\n
                <img src="data:image/png;base64,${req.data}" class="card-img-top" alt="...">
            </div>`;

            document.querySelector(".added_faces").appendChild(img_container);
        } else {
            let notif = document.querySelector(".faces_notfound");
            notif.classList.remove("hide");
            setTimeout(function () {
                notif.classList.add("hide");
            }, 300);
        }
    } else if (req.trigger == "train_started") {
        loading.show();
    } else if (req.trigger == "train_finished") {
        loading.hide();
    }
};

window.onload = function () {
    document.querySelectorAll(".video-feed").forEach(function (elem) {
        elem.addEventListener("click", function () {
            elem.parentElement.querySelector(".video-control").classList.toggle("hide");
        });
    });

    document.querySelectorAll(".fullscreen_btn").forEach(function (elem) {
        elem.addEventListener("click", function () {
            let video_container = elem.parentElement.parentElement;

            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                video_container.requestFullscreen();
            }
        });
    });

    document.querySelectorAll(".screenshot_btn").forEach(function (elem) {
        elem.addEventListener("click", function () {
            ws.send(JSON.stringify({ trigger: "screenshot" }))
        });
    });

    document.querySelectorAll(".record_btn").forEach(function (elem) {
        elem.addEventListener("click", function () {
            ws.send(JSON.stringify({ trigger: "record" }))
        });
    });

    document.querySelectorAll(".add_face").forEach(function (elem) {
        elem.addEventListener("click", function () {
            ws.send(JSON.stringify({ trigger: "add_face" }))
        });
    });

    document.querySelectorAll(".train").forEach(function (elem) {
        elem.addEventListener("click", function () {
            ws.send(JSON.stringify({ trigger: "train", id: document.querySelector(".users").value}))
        });
    });

    start();
};

