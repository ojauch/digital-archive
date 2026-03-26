document.addEventListener('DOMContentLoaded', () => {
    const logArea = document.querySelector('.crawl-log');

    function scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }

    if (logArea) {
        scrollToBottom(logArea);
    }
});
