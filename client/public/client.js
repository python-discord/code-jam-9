console.log("Starting client");

const socket = new WebSocket("ws://localhost:8081/");
socket.addEventListener("open", function (event) {
  console.log("Connected to server");
  console.log(event);
});

socket.addEventListener("message", function (event) {
  console.log("Message from server ", event.data);
});
