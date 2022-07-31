console.log("Starting client");
var socket = ""
var gameStarted = false;
var uname_list = [];
var onlineCount = 0;
var scores = {};

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

    else if (message.event == "ulimit_request") {
      document.getElementById('input-label').innerHTML = "Max Players:";
      document.getElementById('input').disabled = false;
      document.getElementById('input').value = "";
      document.getElementById('input-button').disabled = false;
    }

    else if (message.event == "user_join" || message.event == "user_leave") {
      if (message.event == "user_join") {
        message.uname_list.map((player) => {
          scores[player] = 0;
        })
        onlineCount = message.count;
        uname_list = message.uname_list;
      }
      updatePlayerData();
    }

    else if (message.error == "user limit has been reached"){
      document.getElementById('error-field').innerHTML = "Server Full";
      resetSetup();
    }

    else if (message.event == "start_request"){
        document.getElementById('start-button').disabled = false;
    }

    else if (message.event == "game_start"){
        document.getElementById('start-button').disabled = true;
        gameStarted = true;
    }

    else if (message.event == "question"){
        document.getElementById('question-field').innerHTML = message.question;
        document.getElementById('traceback').innerHTML = message.traceback;
        document.getElementById('code-area').innerHTML = message.code;

        document.getElementById('0').innerHTML = message.possible_answers[0];
        document.getElementById('1').innerHTML = message.possible_answers[1];
        document.getElementById('2').innerHTML = message.possible_answers[2];
        document.getElementById('3').innerHTML = message.possible_answers[3];

        document.getElementById('0').disabled = false;
        document.getElementById('1').disabled = false;
        document.getElementById('2').disabled = false;
        document.getElementById('3').disabled = false;
    }

    else if (message.event == "score_update"){
        scores = message.scores;
        updatePlayerData();
    }

    else if (message.event == "game_over"){
        scores = message.scores;
        updatePlayerData();

        document.getElementById('question-area').innerHTML = "The Winner Is " + message.winner + "!";
        document.getElementById('0').innerHTML = "GAME OVER";
        document.getElementById('1').innerHTML = "GAME OVER";
        document.getElementById('2').innerHTML = "GAME OVER";
        document.getElementById('3').innerHTML = "GAME OVER";
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
  console.log("send start request from client");
  var ulimit = parseInt(document.getElementById('input').value);
  console.log("Sending ulimit ", ulimit);
  socket.send(JSON.stringify({
    "ulimit": ulimit
  }));
  document.getElementById('input').disabled = true;
  document.getElementById('input').value = "";
  document.getElementById('input-button').disabled = true;
}

function updatePlayerData() {
  document.getElementById('player-count').innerHTML = `${onlineCount}<br>`;
  let playerListHtml = uname_list.map((player) => {
    return `<li>${player} - ${scores.player}</li>`;
  }).join('')
  console.log(playerListHtml);
  document.getElementById('player-list').innerHTML = playerListHtml;
}

function sendStartRequest() {
    console.log("Sending Start Request To Server");
    socket.send('{"event": "start_request"}');
}

function processAnswer(answer) {
  console.log("Sending Answer To Server");

  document.getElementById('0').disabled = true;
  document.getElementById('1').disabled = true;
  document.getElementById('2').disabled = true;
  document.getElementById('3').disabled = true;

  // Uncomment the below line if you would rather send the answer as the text, not a number
  // answer = document.getElementById(answer).innerHTML;

  // Modify this send if this is not the desired behavior
  socket.send(JSON.stringify({
    "answer": answer
  }));
}
