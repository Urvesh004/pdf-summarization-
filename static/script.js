function cleanOutput(text) {
    return text.replace(/[📌🔑📄🏢📚💻⚠️🔮✅]/g, "")
               .replace(/\n\s*[-*]\s+/g, "\n• ")
               .trim();
}

function addMessage(text, type) {
    const chatBox = document.getElementById("chatBox");
    const msg = document.createElement("div");
    msg.classList.add("message", type);
    msg.innerText = text;
    chatBox.appendChild(msg);
}

function summarize() {
    const file = document.getElementById("fileInput").files[0];
    if (!file) return alert("Upload file");

    addMessage("Processing...", "user");

    const formData = new FormData();
    formData.append("file", file);

    fetch("/summarize", {
        method: "POST",
        body: formData
    })
    .then(res => res.text())
    .then(data => {
        const clean = cleanOutput(data);
        addMessage(clean, "bot");
    });
}
