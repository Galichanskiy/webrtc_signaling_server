$("#user_form").hide();
$("#connect_form").hide();
$("#send_form").hide();
$("#user_form").submit(set_username);
$("#connect_form").submit(initiate_rtc_connection);
$("#send_form").submit(send_via_webrtc);
$("#set_name_btn").click(set_username);
$("#connect_btn").click(initiate_rtc_connection);
$("#send_btn").click(send_via_webrtc);

var ws = null;
var username = "";
var distant_username = "";

//stun relay server in case of non working connection
var config = {
    "iceServers": [{
        "url": "stun:stun.l.google.com:19302"
    }]
};
var connection = {};

var rtc_connection;
var data_channel;



$("#ws-connect").click(function () {
    ws = new WebSocket("ws://0.0.0.0:5000");

    ws.onopen = function (e) {
        console.log("Websocket opened");
        $("#user_form").show();
    }
    ws.onclose = function (e) {
        console.log("Websocket closed");
    }
    ws.onmessage = function (e) {
        var json = JSON.parse(e.data);

        if (json.action == "candidate") {
            if (json.to == username) {
                handle_ice(json.data);
            }
        } else if (json.action == "offer") {
            if (json.to == username) {
                distant_username = json.from;
                handle_offer(json.data)
            }
        } else if (json.action == "answer") {
            if (json.to == username) {
                handle_answer(json.data);
            }
        }

    }
    ws.onerror = function (e) {
        console.log("Websocket error");
    }
});

//Set username that will be used by the websocket server
//To know on which websocket connection it needs to send the datas
function set_username(e) {
    e.preventDefault();
    username = $("#user").val();
    var json = {
        action: 'login',
        data: username
    };
    ws.send(JSON.stringify(json));
    $("#connect_form").show();
    return false;
}

//Send text message directly via the channel
function send_via_webrtc(e) {
    e.preventDefault();
    data_channel.send($("#message").val());
    $('body').append('Me: <div class="message">' + $("#message").val() + '</div>');
    $("#message").val('');
}

//Method that send all the rtc negotation to the websocket server
function send_negotiation(type, sdp) {
    var json = {
        from: username,
        to: distant_username,
        action: type,
        data: sdp
    };
    ws.send(JSON.stringify(json));
}

//We iniate rtc connection by:
//- asking to create a channel...
//- creating an offer with the local sdp and send it to the peer
function initiate_rtc_connection(e) {
    e.preventDefault();
    distant_username = $("#distant_username").val();
    create_datachannel();

    var sdpConstraints = {
        offerToReceiveAudio: false,
        offerToReceiveVideo: false
    }
    rtc_connection.createOffer(sdpConstraints).then(function (sdp) {
        rtc_connection.setLocalDescription(sdp);
        send_negotiation("offer", sdp);
    }, function (err) {
        console.log(err)
    });
}

//We create a data channel from the RTCPeerConnection
//On ice candidate we send it to the peer
function create_datachannel() {
    rtc_connection = new RTCPeerConnection(config, connection);
    rtc_connection.onicecandidate = function (e) {
        if (!rtc_connection || !e || !e.candidate) return;
        var candidate = event.candidate;
        send_negotiation("candidate", candidate);
    }

    data_channel = rtc_connection.createDataChannel("data_channel", {
        reliable: false
    });

    data_channel.onopen = function () {
        console.log("data channel opened")
        $("#send_form").show();
    };
    data_channel.onclose = function () {
        console.log("data channel closed")
    };
    data_channel.onerror = function () {
        console.log("data channel error")
    };

    rtc_connection.ondatachannel = function (ev) {
        ev.channel.onopen = function () {
            console.log('Data channel is open and ready.');
        };
        ev.channel.onmessage = function (e) {
            $('body').append(distant_username + ': <div class="message from">' + e.data + '</div>')
        }
    };

    return rtc_connection
}

//Create data channel + set remote description from peer offer
//then we create an answer and send it to the peer (via websocket server, thanks to the distant_username)
function handle_offer(offer) {
    var rtc_connection = create_datachannel();
    rtc_connection.setRemoteDescription(new RTCSessionDescription(offer)).catch(e => {
        console.log("Error while setting remote description", e);
    });

    var sdp_constraints = {
        'mandatory': {
            'OfferToReceiveAudio': false,
            'OfferToReceiveVideo': false
        }
    };

    rtc_connection.createAnswer(sdp_constraints).then(function (sdp) {
        return rtc_connection.setLocalDescription(sdp).then(function () {
            send_negotiation("answer", sdp);
        })
    }, function (err) {
        console.log(err)
    });
};

//Handle peer answer (include configuration and media format)
function handle_answer(answer) {
    rtc_connection.setRemoteDescription(new RTCSessionDescription(answer));
};

//Handle ice data -> network configuratin (host candidate; server reflex candidate; relay candidate)
function handle_ice(iceCandidate) {
    rtc_connection.addIceCandidate(new RTCIceCandidate(iceCandidate)).catch(e => {
        console.log("Error while adding candidate ", e);
    })
}