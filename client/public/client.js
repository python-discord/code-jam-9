console.log("Starting client");

const socket = new WebSocket("ws://localhost:8081/");
socket.addEventListener("open", function (event) {
  console.log("Connected to server");
  console.log(event);
});

socket.addEventListener("message", function (event) {
  console.log("Message from server ", event.data);

  let message = JSON.parse(event.data);

  if (message.event == "uname_request") {
    document.getElementById('input-label').innerHTML = "Username:";
    document.getElementById('input').disabled = false;
    document.getElementById('input').value = "";
    document.getElementById('input-button').disabled = false;
  }

  if (message.event == "ulimit_request") {
    document.getElementById('input-label').innerHTML = "Max Players:";
    document.getElementById('input').disabled = false;
    document.getElementById('input').value = "";
    document.getElementById('input-button').disabled = false;
  }

  if (message.event == "user_join" || message.event == "user_leave") {
    document.getElementById('player-count').innerHTML = `${message.count}<br>`;
    let playerListHtml = message.uname_list.map((player) => {
      return `<li>${player}</li>`;
    }).join('')
    document.getElementById('player-list').innerHTML = playerListHtml;
  }

  if (message.error == "user limit has been reached"){
    document.getElementById('input-label').innerHTML = "Server Full";
  }

});

function handleSetup() {
  let type = document.getElementById('input-label').innerHTML
  if (type == "Username:") {
    sendUName();
  } else if (type == "Max Players:") {
    sendULimit();
  }
}

function sendUName() {
  var uname = document.getElementById('input').value;
  console.log("Sending uname ", uname);
  socket.send(JSON.stringify({
    "uname": uname
  }));
}

function sendULimit() {
  var ulimit = parseInt(document.getElementById('input').value);
  console.log("Sending ulimit ", ulimit);
  socket.send(JSON.stringify({
    "ulimit": ulimit
  }));
}
