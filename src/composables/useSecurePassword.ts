import { computed   } from 'vue';
import type {ComputedRef, Ref} from 'vue';

export type PasswordRequirementKey =
    | 'minLength'
    | 'uppercase'
    | 'lowercase'
    | 'number'
    | 'special';

export type PasswordRequirement = {
    key: PasswordRequirementKey;
    label: string;
    met: boolean;
};

export type PasswordStrength = 'weak' | 'medium' | 'strong' | 'empty';

const SPECIAL_CHARS = '!@#$%^&*';
const UPPERCASE_PATTERN = /[A-Z]/;
const LOWERCASE_PATTERN = /[a-z]/;
const NUMBER_PATTERN = /[0-9]/;
const SPECIAL_PATTERN = /[!@#$%^&*]/;

const REQUIREMENT_DEFINITIONS: Array<{
    key: PasswordRequirementKey;
    label: string;
    test: (password: string) => boolean;
}> = [
    {
        key: 'minLength',
        label: 'At least 8 characters',
        test: (password) => password.length >= 8,
    },
    {
        key: 'uppercase',
        label: 'At least 1 uppercase letter (A–Z)',
        test: (password) => UPPERCASE_PATTERN.test(password),
    },
    {
        key: 'lowercase',
        label: 'At least 1 lowercase letter (a–z)',
        test: (password) => LOWERCASE_PATTERN.test(password),
    },
    {
        key: 'number',
        label: 'At least 1 number (0–9)',
        test: (password) => NUMBER_PATTERN.test(password),
    },
    {
        key: 'special',
        label: 'At least 1 special character (! @ # $ % ^ & *)',
        test: (password) => SPECIAL_PATTERN.test(password),
    },
];

function randomIndex(max: number): number {
    const array = new Uint32Array(1);
    crypto.getRandomValues(array);
    return (array[0] ?? 0) % max;
}

function pickRandom(characters: string): string {
    return characters.charAt(randomIndex(characters.length));
}

function shuffle(value: string): string {
    const characters = value.split('');

    for (let index = characters.length - 1; index > 0; index -= 1) {
        const swapIndex = randomIndex(index + 1);
        [characters[index], characters[swapIndex]] = [
            characters[swapIndex] ?? '',
            characters[index] ?? '',
        ];
    }

    return characters.join('');
}

export function checkPasswordRequirements(
    password: string,
): PasswordRequirement[] {
    return REQUIREMENT_DEFINITIONS.map((definition) => ({
        key: definition.key,
        label: definition.label,
        met: definition.test(password),
    }));
}

export function getPasswordStrength(password: string): PasswordStrength {
    if (!password) {
        return 'empty';
    }

    const metCount = checkPasswordRequirements(password).filter(
        (requirement) => requirement.met,
    ).length;

    if (metCount <= 2) {
        return 'weak';
    }

    if (metCount <= 4) {
        return 'medium';
    }

    return 'strong';
}

export function isPasswordValid(password: string): boolean {
    return checkPasswordRequirements(password).every(
        (requirement) => requirement.met,
    );
}

export function generateSecurePassword(length = 14): string {
    const uppercase = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const lowercase = 'abcdefghijkmnopqrstuvwxyz';
    const numbers = '23456789';
    const special = SPECIAL_CHARS;

    const required = [
        pickRandom(uppercase),
        pickRandom(lowercase),
        pickRandom(numbers),
        pickRandom(special),
    ];

    const all = uppercase + lowercase + numbers + special;
    const remaining = Array.from(
        { length: Math.max(length - required.length, 0) },
        () => pickRandom(all),
    );

    return shuffle([...required, ...remaining].join(''));
}

export function useSecurePassword(password: Ref<string>) {
    const requirements: ComputedRef<PasswordRequirement[]> = computed(() =>
        checkPasswordRequirements(password.value),
    );

    const strength: ComputedRef<PasswordStrength> = computed(() =>
        getPasswordStrength(password.value),
    );

    const isValid: ComputedRef<boolean> = computed(() =>
        isPasswordValid(password.value),
    );

    const strengthLabel = computed(() => {
        switch (strength.value) {
            case 'weak':
                return 'Weak';
            case 'medium':
                return 'Medium';
            case 'strong':
                return 'Strong';
            default:
                return '';
        }
    });

    const strengthPercent = computed(() => {
        switch (strength.value) {
            case 'weak':
                return 33;
            case 'medium':
                return 66;
            case 'strong':
                return 100;
            default:
                return 0;
        }
    });

    const strengthBarClass = computed(() => {
        switch (strength.value) {
            case 'weak':
                return 'bg-red-500';
            case 'medium':
                return 'bg-amber-500';
            case 'strong':
                return 'bg-emerald-500';
            default:
                return 'bg-gray-200';
        }
    });

    return {
        requirements,
        strength,
        isValid,
        strengthLabel,
        strengthPercent,
        strengthBarClass,
        generateSecurePassword,
    };
}
