export type UseInitialsReturn = {
    getInitials: (fullName?: string) => string;
};

export function getInitials(fullName?: string): string {
    if (!fullName) {
        return '';
    }

    const names = fullName.trim().split(' ');

    if (names.length === 0) {
        return '';
    }

    const first = names[0] ?? '';
    if (names.length === 1) {
        return first.charAt(0).toUpperCase();
    }

    const last = names[names.length - 1] ?? '';
    return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase();
}

export function useInitials(): UseInitialsReturn {
    return { getInitials };
}
