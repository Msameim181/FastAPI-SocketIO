let socket;

function fn() {
  socket = io("http://0.0.0.0:1234", {
    auth: {
      Authorization:
        "Bearer token",
    },
  });
  socket.on("connect", () => {
    console.log(`connect ${socket.id}`);
    let connectionID = document.getElementById("connectionID");
    connectionID.innerHTML = socket.id;
  });

  socket.on("disconnect", () => {
    console.log(`disconnect ${socket.id}`);
  });

  socket.on("message", (a, b, c) => {
    console.log(a, b, c);
    let messages = document.getElementById("messages");
    let span = document.createElement("p");
    span.classList.add("ai");
    span.innerHTML = a + "<br>";
    messages.appendChild(span);
    let divider = document.createElement("div");
    divider.classList.add("divider");
    messages.appendChild(divider);
  });
}

function handleKeyDown(e) {
  if (e.key === "Enter") {
    send();
    let chatInput = document.getElementById("chatInput");
    chatInput.value = "";
  }
}

function disconnect() {
  console.log(`disconnect ${socket.id}`);
  socket.disconnect();
  let connectionID = document.getElementById("connectionID");
  connectionID.innerHTML = "Disconnected";
}
function connect() {
  socket.connect();
  console.log(`connect ${socket.id}`);
  let connectionID = document.getElementById("connectionID");
  connectionID.innerHTML = "Disconnected";
}

function joinRoom() {
  const roomInput = document.getElementById("roomInput");
  socket.emit("join", roomInput);
}
function leaveRoom() {
  socket.emit("leave");
}

function send() {
  if (!socket.connected) {
    alert("Please connect first");
    return;
  }
  const chatInput = document.getElementById("chatInput");
  const message = chatInput.value;
  console.log(`message ${message}`);
  socket.emit("message", {
    live_chat_id: 1,
    message: message,
  });
  let messages = document.getElementById("messages");
  let span = document.createElement("p");
  span.classList.add("client");
  span.innerHTML = message + "<br>";
  messages.appendChild(span);
  let divider = document.createElement("div");
  divider.classList.add("divider");
  messages.appendChild(divider);
  chatInput.value = "";
}
