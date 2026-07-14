import { onBeforeUnmount, onMounted } from 'vue';

export function useScrollReveal(selector = '[data-reveal]') {
    let observer: IntersectionObserver | null = null;

    onMounted(() => {
        const nodes = document.querySelectorAll<HTMLElement>(selector);

        if (!nodes.length || !('IntersectionObserver' in window)) {
            return;
        }

        observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add('is-visible');
                observer?.unobserve(entry.target);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

        nodes.forEach((node) => observer?.observe(node));
    });

    onBeforeUnmount(() => {
        observer?.disconnect();
    });
}
