<script setup lang="ts">
import PulseLoader from "vue-spinner/src/PulseLoader.vue";
import * as monaco from "monaco-editor"; // skipcq: JS-C1003
import Timer from "./Timer.vue";
import { onMounted, ref, toRaw } from "vue";
import { themes } from "../assets/js/theme";

const props = defineProps({
  state: Object, // skipcq: JS-0682
  sync: Object, // skipcq: JS-0682
});
const emit = defineEmits(["leaveRoom"]);

let collaborators = ref(toRaw(props.sync?.collaborators));
let code = props.sync?.code; // skipcq: JS-V005
let editor: monaco.editor.IStandaloneCodeEditor;
let joined = false;
let evalText = ref("");
let evalLoading = ref(false);
let time = ref(toRaw(props.sync?.time));

let syncinterval;
let bugsinterval;

onMounted(() => {
  for (let theme of themes) {
    monaco.editor.defineTheme(theme.name, theme.theme);
  }
  const theme = document.querySelector("body").getAttribute("data-theme");

  editor = monaco.editor.create(document.getElementById("content"), {
    value: "",
    language: "python",
    insertSpaces: true,
    theme,
  });

  editor.getModel()?.onDidChangeContent(contentHandler);
  editor.getModel()?.setValue(code);
  editor.getModel()?.setEOL(0);

  joined = true;
});

/**
 * Function to convert the editor lines to index positions.
 */
function positionToIndex(line, col) {
  let index = 0;
  for (let i = 1; i < line; i++) {
    index += code.split("\n")[i - 1].length + 1;
  }
  return index + col - 1;
}

/**
 * Function to transform content into JSOn serializable content.
 */
function contentHandler(ev) {
  if (code === editor.getModel()?.getValue()) return;
  if (!joined) return;

  const changes = ev.changes.map((change) => {
    return {
      from: positionToIndex(
        change.range.startLineNumber,
        change.range.startColumn
      ),
      to: positionToIndex(change.range.endLineNumber, change.range.endColumn),
      value: change.text,
    };
  });

  props.state?.websocket.send(
    JSON.stringify({
      type: "replace",
      data: {
        code: changes,
      },
    })
  );

  code = editor.getModel()?.getValue();
}

/**
 * Function to receive events from the server.
 */
// skipcq: JS-0611
props.state.websocket.onmessage = function (ev) {
  const message = JSON.parse(ev.data);

  switch (message.type) {
    case "connect":
      collaborators.value.push({
        id: message.data.id,
        username: message.data.username,
      });
      break;

    case "disconnect":
      collaborators.value = collaborators.value.filter((c) => {
        return c.id !== message.data.user[0].id;
      });
      break;

    case "replace":
      message.data.code.forEach((change) => {
        code =
          code.substring(0, change.from) +
          change.value +
          code.substring(change.to);
      });
      editor.setValue(code);
      break;

    case "evaluate":
      evalLoading.value = false;
      evalText.value = message.data.result;
      break;

    case "sync":
      collaborators.value = message.data.collaborators.filter((c) => {
        return c.id != props.sync.ownID;
      });
      code = message.data.code;
      time.value = message.data.time;
      editor.setValue(code);
      break;
  }
};

const bugTimes = {
  1: 60_000,
  2: 45_000,
  3: 30_000,
};

if (!collaborators.value.length) {
  syncinterval = setInterval(() => {
    props.state.websocket.send(
      JSON.stringify({
        type: "sync",
        data: {
          collaborators: collaborators.value,
          owner_id: props.sync?.owner_id,
          code: code,
          difficulty: props.sync?.difficulty,
        },
      })
    );
  }, 10000);

  bugsinterval = setInterval(() => {
    props.state.websocket.send(
      JSON.stringify({
        type: "bugs",
        data: {},
      })
    );
  }, bugTimes[props.sync?.difficulty]);
}

/**
 * Function to request the evaluation of the current code.
 */
function requestEval() {
  if (!joined) return;
  evalLoading.value = true;

  props.state.websocket.send(
    JSON.stringify({
      type: "sync",
      data: {
        collaborators: collaborators.value,
        owner_id: props.sync?.owner_id,
        code: code,
        difficulty: props.sync?.difficulty,
      },
    })
  );

  props.state.websocket.send(
    JSON.stringify({
      type: "evaluate",
      data: {},
    })
  );

  document.querySelector("input#evaluate-modal").checked = true;
}

/**
 * Function to close the Evaluate modal.
 */
function closeModal() {
  document.querySelector("input#evaluate-modal").checked = false;
}

/**
 * Function for a client to leave a room.
 */
function leaveRoom() {
  joined = false;
  props.state.websocket.send(
    JSON.stringify({
      type: "disconnect",
      data: {},
    })
  );

  clearInterval(syncinterval);
  clearInterval(bugsinterval);
  emit("leaveRoom");
}
</script>

<template>
  <div id="room">
    <!-- Model for displaying code evaluation -->
    <input type="checkbox" id="evaluate-modal" class="modal-toggle" />
    <label for="evaluate-modal" class="modal cursor-pointer">
      <label id="modalactual" class="modal-box relative">
        <button @click="closeModal" class="btn my-4">Okay</button>
        <label
          for="evaluate-modal"
          class="btn btn-sm btn-circle absolute right-2 top-2"
        >
          <i class="gg-close-o" style="--ggs: 1.2"></i>
        </label>
        <PulseLoader
          v-if="evalLoading"
          style="margin-bottom: 180px"
        ></PulseLoader>
        <div id="codebox" v-else>
          {{ evalText }}
        </div>
      </label>
    </label>

    <div id="sidebar">
      <h2 class="text-6xl m-3">Collaborators</h2>
      <ul style="margin-left: 20px">
        <li style="color: orange">
          {{ props.state?.username }}
          <span v-show="props.sync.owner_id === props.sync.ownID">👑</span>
        </li>
        <li v-for="collaborator in collaborators" :key="collaborator.id">
          {{ collaborator.username }}
          <span v-show="collaborator.id === props.sync.owner_id"> 👑</span>
        </li>
      </ul>
      <div id="info">
        <form id="aform">
          <button
            id="evalbut"
            type="button"
            @click="
              () => {
                requestEval();
              }
            "
            class="btn btn-primary mt-4"
          >
            Evaluate Code
          </button>
        </form>
        <Timer :time="time"></Timer>
        <p>Room: {{ props.state?.roomCode }}</p>
        <p>Difficulty: {{ props.sync?.difficulty }}</p>
      </div>
      <ul id="collabul"></ul>
      <button class="btn btn-primary mt-auto" @click="leaveRoom">
        <i class="gg-log-out mr-4"></i>
        Leave Room {{ props.state?.roomCode }}
      </button>
    </div>

    <div id="content">
      <div id="container"></div>
    </div>
  </div>
</template>

<style scoped>
#modalactual {
  display: flex;
  flex-direction: column-reverse;
  min-height: 512px;
}

#modalactual > button {
  margin-bottom: 0;
}

#codebox {
  background-color: hsl(var(--nf, var(--n)));
  border-radius: var(--rounded-btn, 0.5rem);
  text-align: left;
  padding: 16px;
  flex-grow: 1;
  overflow-y: auto;
  white-space: pre-wrap;
  font-family: monospace;
  color: hsl(var(--pc));
}

/* width */
::-webkit-scrollbar {
  width: 10px;
}

/* Track */
::-webkit-scrollbar-track {
  background: hsl(var(--b1)) / var(--tw-bg-opacity);
  border-radius: var(--rounded-btn, 0.5rem);
}

/* Handle */
::-webkit-scrollbar-thumb {
  background: hsl(var(--bc));
  border-radius: var(--rounded-btn, 0.5rem);
}

/* Handle on hover */
::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.dot {
  height: 8px;
  width: 8px;
  margin: 0 0 3px 4px;
  background-color: orange;
  border-radius: 50%;
  display: inline-block;
}

#room {
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 3fr;
}

#content {
  text-align: left;
}

#sidebar,
#content {
  border: solid hsl(var(--bc));
}

#sidebar {
  border-width: 4px 2px 4px 4px;
}

#content {
  border-width: 4px 4px 4px 2px;
  padding: 4px;
}

#sidebar h1 {
  text-align: center;
}

ul {
  text-align: center;
  font-size: 2em;
}

li {
  margin: 30px;
}

#sidebar,
#content {
  display: flex;
  flex-direction: column;
}

li {
  text-align: left;
  color: hsl(var(--bc));
  font-size: 24px;
  margin-left: 48px;
  list-style: disc;
}

#container {
  text-align: left;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

#info {
  position: absolute;
  left: 20px;
  bottom: 58px;
  font-size: 24px;
  text-align: left;
  line-height: 24px;
}

#aform {
  text-align: center;
}

#evalbut {
  margin-bottom: 28px;
  width: 100%;
}
</style>
