document.addEventListener("DOMContentLoaded", () => {
    const queryField = document.querySelector("#query");
    const chips = document.querySelectorAll(".prompt-chip");

    if (!queryField || !chips.length) {
        return;
    }

    chips.forEach((chip) => {
        chip.addEventListener("click", () => {
            queryField.value = chip.textContent.trim();
            queryField.focus();
        });
    });
});
