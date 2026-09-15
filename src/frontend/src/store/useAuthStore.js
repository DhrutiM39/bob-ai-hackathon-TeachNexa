import { create } from 'zustand';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

function loadFromStorage() {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const user = JSON.parse(localStorage.getItem(USER_KEY) || 'null');
    return { token, user };
  } catch {
    return { token: null, user: null };
  }
}

export const useAuthStore = create((set) => ({
  ...loadFromStorage(),

  login: ({ access_token, user_id, name, email, role }) => {
    const user = { id: user_id, name, email, role };
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ token: access_token, user });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({ token: null, user: null });
  },
}));
