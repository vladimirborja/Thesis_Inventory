/**
 * src/lib/api.ts
 * Lightweight HTTP client that:
 *  - Reads the JWT from localStorage and sends it as Bearer auth
 *  - Converts snake_case API responses to camelCase (already done by Pydantic alias_generator)
 *  - On 401 clears the token and redirects to /auth
 *  - Throws a plain Error with the server's `detail` message on failures
 */

const BASE = '/api';
const TOKEN_KEY = 'ims_token';

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    isFormData = false,
): Promise<T> {
    const token = getToken();
    const headers: Record<string, string> = {};

    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isFormData && body !== undefined) headers['Content-Type'] = 'application/json';

    const res = await fetch(`${BASE}${path}`, {
        method,
        headers,
        body: isFormData
            ? (body as FormData)
            : body !== undefined
            ? JSON.stringify(body)
            : undefined,
    });

    if (res.status === 401) {
        clearToken();
        window.location.href = '/auth';
        throw new Error('Unauthorized');
    }

    if (res.status === 204) return undefined as T;   // No content

    const text = await res.text();
    let data: any = null;
    if (text) {
        try {
            data = JSON.parse(text);
        } catch {
            data = { detail: text };
        }
    }

    if (!res.ok) {
        throw new Error(data?.detail ?? `Request failed (${res.status})`);
    }

    return data as T;
}

export const api = {
    get:    <T>(path: string)                        => request<T>('GET',    path),
    post:   <T>(path: string, body: unknown)         => request<T>('POST',   path, body),
    put:    <T>(path: string, body: unknown)         => request<T>('PUT',    path, body),
    patch:  <T>(path: string, body: unknown)         => request<T>('PATCH',  path, body),
    delete: <T>(path: string)                        => request<T>('DELETE', path),
    upload: <T>(path: string, formData: FormData)    => request<T>('POST',   path, formData, true),
};
