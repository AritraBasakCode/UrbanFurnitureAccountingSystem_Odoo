const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';
const TOKEN_KEY = 'urban_furniture_access_token';

export type User = { id: number; name: string; email: string; role: string };
export type Contact = { id: number; name: string; type: 'CUSTOMER' | 'VENDOR' | 'BOTH'; email?: string | null; mobile?: string | null };
export type Product = { id: number; name: string; type: 'GOODS' | 'SERVICE' | 'COMBO'; sales_price: number; purchase_price: number; category_id?: number | null };
export type StockRow = { product_id: number; current_stock: number };

export class ApiError extends Error {}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(payload?.detail ?? `Request failed (${response.status})`);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

export const api = {
  login: async (email: string, password: string) => {
    const token = await request<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    localStorage.setItem(TOKEN_KEY, token.access_token);
  },
  logout: () => localStorage.removeItem(TOKEN_KEY),
  currentUser: () => request<User>('/auth/me'),
  contacts: () => request<Contact[]>('/contacts'),
  createContact: (payload: Omit<Contact, 'id'>) => request<Contact>('/contacts', { method: 'POST', body: JSON.stringify(payload) }),
  updateContact: (id: number, payload: Omit<Contact, 'id'>) => request<Contact>(`/contacts/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteContact: (id: number) => request<void>(`/contacts/${id}`, { method: 'DELETE' }),
  products: () => request<Product[]>('/products'),
  stock: async () => (await request<{ products: StockRow[] }>('/reports/stock')).products,
  createProduct: (payload: Omit<Product, 'id'>) => request<Product>('/products', { method: 'POST', body: JSON.stringify(payload) }),
  updateProduct: (id: number, payload: Omit<Product, 'id'>) => request<Product>(`/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteProduct: (id: number) => request<void>(`/products/${id}`, { method: 'DELETE' }),
};
