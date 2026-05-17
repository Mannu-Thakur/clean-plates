import { writable } from 'svelte/store';

export interface Toast {
  id: number;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
}

export const toasts = writable<Toast[]>([]);
let counter = 1;

export function notify(message: string, type: Toast['type'] = 'info') {
  const id = counter++;
  toasts.update((items) => [...items, { id, message, type }]);
  setTimeout(() => dismissToast(id), 4200);
}

export function dismissToast(id: number) {
  toasts.update((items) => items.filter((item) => item.id !== id));
}
