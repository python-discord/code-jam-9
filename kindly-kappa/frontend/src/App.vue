<script setup>
import { ref } from "vue";
import Room from "./components/Room.vue";
import Home from "./components/Home.vue";

/**
 * Function to generate a room code.
 * @param length The number of characters.
 * @returns A randomly generated, uppercase, code.
 */
function generateCode(length = 4) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  let code = "";
  for (let i = 0; i < length; i++) {
    code += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
  }
  return code;
}

let app_errors = ref([]);

/**
 * Function to add errors.
 */
function add_error(err) {
  let error = {
    id: generateCode(),
    err,
  };
  app_errors.value.push(error);

  setTimeout(() => {
    app_errors.value = app_errors.value.filter((e) => e.id !== error.id);
  }, 5000);
}

const websocket = new WebSocket("ws://localhost:8000/room");
websocket.onerror = function (err) {
  add_error(
    "Oh no! Something has gone very wrong. This genuinely is a bug, not a feature :("
  );
};

websocket.onclose = function (err) {
  add_error("The websocket closed... why?");
};

const joined = ref(false);
const state = ref({
  roomCode: "",
  username: "",
  websocket,
});
const sync = ref({
  collaborators: [],
  code: "",
  difficulty: 0,
  time: undefined,
  ownerID: "",
  ownID: "",
});

let joining = false;

/**
 * Function to join a room.
 */
function joinRoom({ username, roomCode }) {
  if (joining) return;
  joining = true;

  roomCode = roomCode.toUpperCase();

  websocket.send(
    JSON.stringify({
      type: "connect",
      data: {
        connection_type: "join",
        room_code: roomCode,
        username,
      },
    })
  );

  state.value = {
    roomCode,
    username,
    websocket,
  };
}

/**
 * Function to create a room.
 */
function createRoom({ username, difficulty }) {
  if (joining) return;
  joining = true;

  const roomCode = generateCode();

  websocket.send(
    JSON.stringify({
      type: "connect",
      data: {
        connection_type: "create",
        difficulty,
        room_code: roomCode,
        username,
      },
    })
  );

  state.value = {
    roomCode,
    username,
    websocket,
  };
}

websocket.onmessage = function (ev) {
  const message = JSON.parse(ev.data);

  if (message.type === "sync") {
    sync.value = {
      collaborators: message.data.collaborators,
      code: message.data.code,
      difficulty: message.data.difficulty,
      time: message.data.time,
      owner_id: message.data.owner_id,
      ownID: "",
    };
  }
  if (message.type === "connect") {
    sync.value.ownID = message.data.user_id;
    joined.value = true;
  }

  if (message.type === "error") {
    joining = false;

    add_error(message.data.message);
  }
};

/**
 * Function to leave a room.
 */
function leaveRoom() {
  joined.value = false;
  joining = false;
}
</script>

<template>
  <div class="h-full">
    <div class="alerts">
      <div
        v-for="error of app_errors"
        :key="error.id"
        class="animate__animated animate__fadeInLeft alert my-2 alert-error w-full m-auto"
      >
        <div>
          <i class="gg-danger"></i>
          <span>{{ error.err }}</span>
        </div>
      </div>
    </div>
    <Room
      v-if="joined"
      :state="state"
      :sync="sync"
      @leaveRoom="leaveRoom"
    ></Room>
    <Home v-else @joinRoom="joinRoom" @createRoom="createRoom"></Home>
  </div>
</template>

<style scoped>
.alerts {
  position: fixed;
  top: 0;
  left: 8px;
  width: calc(100% - 16px);
  z-index: 10000;
}

.alert.alert-error {
  animation-duration: 0.3s;
}
</style>
