import { computed, onMounted } from 'vue';
import {
    initializeTheme,
    updateTheme,
    useAppearance
    
} from '@/composables/useAppearance';
import type {Appearance} from '@/composables/useAppearance';

export { initializeTheme, updateTheme };

export function useDarkMode() {
    const { appearance, resolvedAppearance, updateAppearance } = useAppearance();

    onMounted(() => {
        const saved = localStorage.getItem('appearance') as Appearance | null;

        if (saved === 'light' || saved === 'dark') {
            appearance.value = saved;
            updateTheme(saved);
        } else if (!saved) {
            updateAppearance('light');
        }
    });

    const isDark = computed(() => resolvedAppearance.value === 'dark');

    function toggleDarkMode() {
        updateAppearance(isDark.value ? 'light' : 'dark');
    }

    function setDarkMode(value: boolean) {
        updateAppearance(value ? 'dark' : 'light');
    }

    return {
        appearance,
        isDark,
        toggleDarkMode,
        setDarkMode,
    };
}
