document.addEventListener("DOMContentLoaded", () => {
    const slides = Array.from(document.querySelectorAll("[data-lyric-slide]"));

    if (slides.length <= 1) {
        return;
    }

    let activeIndex = 0;

    const showSlide = (nextIndex) => {
        slides[activeIndex].classList.remove("is-active");
        activeIndex = nextIndex;
        slides[activeIndex].classList.add("is-active");
    };

    window.setInterval(() => {
        const nextIndex = (activeIndex + 1) % slides.length;
        showSlide(nextIndex);
    }, 3800);
});