# WebRTC signaling server in python
## <b>Purpose</b>
To use the `WebRTC` protocol between two peers. We need to signal to another peer our network configuration in order to directly communicate browser by browser.

Because `WebRTC` doesn't propose the signaling protocol we need to implement it. 


## <b>Pre-requisites</b>
1. `docker` & `docker-compose`.
2. a web-browser compatible with the WebRTC protocol.
3. `python 3.5+` and `pip` if you want to run it without container.

## <b>Usage</b>
Here is the technologies, used by this solution:
1. `python 3.5+`
2. `HTML` + `js`
3. `nginx` for static files
4. `docker`

To run the solution, run the following commands:
```bash
cd webrtc_signaling_server
docker-compose up --build -d
```
When the two containers are up and running, open your web-browser and go to [http://localhost:8080](http://localhost:8080)

1. Click on the `Connect to websocket server` button
2. Fill your username textbox and click on the `Set my username` button
3. Repeat the first two steps into another web-browser tab
3. Fill the peer's username inside the textbox and click on the `Connect to peer user` button
4. Enter the text you want on the message textbox and click on the `Send my message` button



## <b>How it works</b>
This implementation use the `WebSocket` protocol as the signaling protocol in the `python` language. The architecture is straightforward, one websocket server that handle negotiation between peers.
Here is the communication process used:

1. The peer A send to the `WebSocket` server a login action with its `username`.
2. The WebSocket server stores the connection to A by using the `username` as the dictionary key.
3. The peer B runs, also the login action to the WebSocket server.
4. The peer A wants to communicate directly to the peer B. He tells to the WebSocket server that he wants to by creating a dataChannel and sending an offer to the WebSocket server, which will forward it to the peer B.
5. After that all the process of a WebRTC connection is running through the WebSocket server which handle the messages forwarding.
6. When everything is know between the two peers, all the communication is going through the dataChannel.


### <b>Which sort of data could pass through this implementation ?</b>
We use the `RTCDataChannel` API. Its purpose is to transfer arbitrary binary datas between peers. So, we can transfer a file, text (like us), etc.
We could use the `MediaStream` api to send video, audio as well as text data like subtitles.


# Limitations
1. RTCPeerConnection could host theoretically 65534 channels ([1]: https://developer.mozilla.org/en/docs/Web/API/RTCDataChannel)
2. Because WebSocket protocol depends on the TCP layer. The TCP layer can accept/establish 65534 connection because of the number of ports with the IPV4 version.

## <b>Limitations workaround</b>
Because of the  WebSocket server resources limitations. We need to scale-out our solution, how ?
1. By adding in front of the WebSocket server a load-balancer.
2. Adding more WebSocket servers.


## <b>Scenario</b>
We have one load-balancer and two servers attached to it:
* __peer A__ is attached to __server 1__
* __peer B__ is attached to __server 1__
* __peer C__ is attached to __server 2__

__<h3>How `peer A` could connect to `peer C` ?</h3>__

## <b>Solution</b>
### <b>Messaging solution</b>
1. Each server is connected to a messaging solution like (RabbitMQ, Redis or even Kafka...) by using the Pub/Sub protocol.
2. When a server receives a message from a peer, it publishs it to the messaging broker.
3. Each server subscribe to a channel hosted by the messaging broker.
4. With this architecture, when a WebRTC negotiation is initiated and the distant peer is not connected to the same server, the server send the negotiation message to the broker.
5. Each server receive the message and verify if the receiver is known.
6. If the receiver is known, the message is forwarded to it.




[1]: https://developer.mozilla.org/en/docs/Web/API/RTCDataChannel