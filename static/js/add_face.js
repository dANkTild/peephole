var loading = new bootstrap.Modal($(".modal")[0], {
    keyboard: false
});

$(".add_face").click(function () {
    socket.emit("add_face", {user_id: $(".users").val()});
});

socket.on("added_face", function (data) {
    const blb = new Blob([data], {type: 'image/jpeg'});
    const url = URL.createObjectURL(blb);

    $(".added_faces").prepend('<div class="col">\n' +
        '    <div class="card h-100">\n' +
        '        <img src="' + url + '" class="card-img-top" alt="...">\n' +
        '    </div>\n' +
        '</div>');
});

socket.on("faces_notfound", function () {
    $(".faces_notfound").fadeIn(100);
    setTimeout(function () {
        $(".faces_notfound").fadeOut(500);
    }, 500);
});

socket.on("train_started", function () {
    loading.show();
});

socket.on("train_finished", function () {
    loading.hide();
});

$(".train").click(function () {
    socket.emit("train", {user_id: $(".users").val()});
});
