document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#chatForm");
    const queryField = document.querySelector("#chatQuery");
    const messages = document.querySelector("#chatMessages");
    const status = document.querySelector("#chatStatus");
    const promptButtons = document.querySelectorAll(".chat-prompt");

    if (!form || !queryField || !messages || !status) {
        return;
    }

    const appendMessage = (role, content, matches = []) => {
        const article = document.createElement("article");
        article.className = `chat-message ${role === "user" ? "chat-message-user" : "chat-message-bot"}`;

        const roleLabel = document.createElement("span");
        roleLabel.className = "chat-role";
        roleLabel.textContent = role === "user" ? "You" : "LyricLens";
        article.appendChild(roleLabel);

        const paragraph = document.createElement("p");
        paragraph.textContent = content;
        article.appendChild(paragraph);

        if (matches.length) {
            const list = document.createElement("div");
            list.className = "chat-match-list";
            matches.forEach((match) => {
                const card = document.createElement("a");
                card.className = "chat-match-card";
                card.href = `/songs/${match.id}`;
                card.innerHTML = `<strong>${match.title}</strong><span>${match.artist}</span><p>${match.reason}</p>`;
                list.appendChild(card);
            });
            article.appendChild(list);
        }

        messages.appendChild(article);
        messages.scrollTop = messages.scrollHeight;
    };

    const runQuery = async (query) => {
        appendMessage("user", query);
        status.textContent = "Searching the current LyricLens library...";

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query }),
            });

            if (!response.ok) {
                throw new Error("Chat request failed.");
            }

            const payload = await response.json();
            appendMessage("bot", payload.answer, payload.matches || []);
            status.textContent = "Answers stay grounded in the current dataset.";
        } catch (error) {
            appendMessage("bot", "I can only answer from the current LyricLens music library, and the chat request failed just now.");
            status.textContent = "Chat is temporarily unavailable.";
        }
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const query = queryField.value.trim();
        if (!query) {
            status.textContent = "Enter a mood, theme, artist, or lyric question first.";
            queryField.focus();
            return;
        }

        queryField.value = "";
        await runQuery(query);
    });

    promptButtons.forEach((button) => {
        button.addEventListener("click", () => {
            queryField.value = button.textContent.trim();
            queryField.focus();
        });
    });
});
