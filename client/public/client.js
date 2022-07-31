console.log("Starting client");
var socket = ""

function connectToServer() {
  // Lockout User Input
  document.getElementById('input-label').innerHTML = "Connecting...";
  document.getElementById('input').disabled = true;
  document.getElementById('input-button').disabled = true;
  document.getElementById('error-field').innerHTML = "";

  // Process Address
  address = document.getElementById('input').value;
  if (address == "") {
    address = "ws://localhost:8081";
  } else if (address.slice(0,2) != "ws") {
    address = "ws://" + address;
  }
  console.log("Connecting to ", address);

  // Attempt Connection
  try {
    socket = new WebSocket(address);
  } catch (e) {
    console.log("Error connecting to server");
    resetSetup();
    document.getElementById('error-field').innerHTML = "Bad Address";
    return;
  }

  socket.onerror = function(event){
    console.log(event);
    resetSetup();
    document.getElementById('error-field').innerHTML = "Unable To Connect";
  }

  // Verify connection
  socket.addEventListener("open", function (event) {
    console.log("Connected to server");
    console.log(event);
  });

  // Handle messages
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
      document.getElementById('error-field').innerHTML = "Server Full";
      resetSetup();
    }

    if (message.event == "start_request"){
        document.getElementById('start-button').disabled = false;
    }

    if (message.event == "game_start"){
        document.getElementById('start-button').disabled = true;
        gameSetup(event_data);
    }

  });
}

function resetSetup () {
  document.getElementById('input-label').innerHTML = "Server Address:";
  document.getElementById('input').disabled = false;
  document.getElementById('input').value = "";
  document.getElementById('input-button').disabled = false;
}

function handleSetup() {
  let type = document.getElementById('input-label').innerHTML
  if (type == "Username:") {
    sendUName();
  } else if (type == "Max Players:") {
    sendULimit();
  } else if (type == "Server Address:") {
    connectToServer();
  }
}

function sendUName() {
  var uname = document.getElementById('input').value;
  console.log("Sending uname ", uname);
  socket.send(JSON.stringify({
    "uname": uname
  }));
  document.getElementById('input').disabled = true;
  document.getElementById('input').value = "";
  document.getElementById('input-button').disabled = true;
}

function sendULimit() {
  var ulimit = parseInt(document.getElementById('input').value);
  console.log("Sending ulimit ", ulimit);
  socket.send(JSON.stringify({
    "ulimit": ulimit
  }));
  document.getElementById('input').disabled = true;
  document.getElementById('input').value = "";
  document.getElementById('input-button').disabled = true;
}

function sendStartRequest() {
    console.log("send start request from client");
    socket.send(JSON.stringify(true));
}

function gameSetup() {

}

function processAnswer(answer) {
}
