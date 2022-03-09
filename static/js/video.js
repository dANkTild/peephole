let socket = io();

let img_url, old_url;
let c = 0;

let img_tag = new Image();
img_tag.onload = function() {
        $(".video_feed").css("background-image", 'url("' + img_url + '")');

        if ($(".video_feed").css("background-image") !== 'url("' + old_url + '")') {
            URL.revokeObjectURL(old_url);
        }

        old_url = img_url;
    }


socket.on('frame', function(data) {
    $(".fps").text(data.fps.toFixed(1));

    const blb = new Blob([data.img], {type: 'image/jpeg'});

    // console.log("rcv");
    img_url = URL.createObjectURL(blb);
    $(".test-text").text(c);
    c += 1;
    img_tag.src = img_url;
});

$(".video_feed").click(function() {
    $(".video-control").toggle(300);
});

$(".fullscreen_btn").click(function() {
    const elem = $(".video-container").get(0);

    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        elem.requestFullscreen();
    }
});

$(".recognition_btn").click(function() {
    socket.emit("trigger", {type: "recognition"});
});

$(".screenshot_btn").click(function() {
    socket.emit("trigger", {type: "screenshot"});
});

$(".video_btn").click(function() {
    socket.emit("trigger", {type: "video"});
});

socket.on('state', function(data) {
    switch (data.type){
        case "recognition":
            if (data.state) {
                $(".recognition_btn").addClass("text-primary");
            } else {
                $(".recognition_btn").removeClass("text-primary");
            }
            break;

        case "saved":
            console.log("saved");
            $(".saved-notif").fadeIn(100);
            setTimeout(function () {
                $(".saved-notif").fadeOut(1000);
            }, 1500);
            break;

        case "video":
            if (data.state) {
                $(".video_btn").addClass("text-primary");
            } else {
                $(".video_btn").removeClass("text-primary");
            }
            break;

    }
});

socket.on('detected_face', function(data) {
    $(".detected_name").text(data.name);
    $(".detected_conf").text(data.confidence);
    let toast = new bootstrap.Toast($(".detected_toast")[0], {delay: 50000});
    toast.show();
});

function test(data){
    $(".detected_name").text(data.name);
    $(".detected_conf").text(data.confidence);
    let toast = new bootstrap.Toast($(".detected_toast")[0], {delay: 50000});
    toast.show();
}

socket.on('tested', function(data) {
    console.log("tested", data)
});
