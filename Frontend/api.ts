const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';
const TOKEN_KEY = 'urban_furniture_access_token';

export type User = { id: number; name: string; email: string; role: string };
export type Contact = { id: number; name: string; type: 'CUSTOMER' | 'VENDOR' | 'BOTH'; email?: string | null; mobile?: string | null };
export type Product = { id: number; name: string; type: 'GOODS' | 'SERVICE' | 'COMBO'; sales_price: number; purchase_price: number; category_id?: number | null };
export type StockRow = { product_id: number; current_stock: number };
export type Sale = { id: number; customer_id: number; product_id: number; quantity: number; unit_price: number; tax: number; total: number; date: string; status: string };
export type Purchase = { id: number; vendor_id: number; product_id: number; quantity: number; unit_price: number; tax: number; total: number; date: string; status: string };
export type Payment = { id: number; contact_id: number; reference_id: number | null; type: 'RECEIVE' | 'PAY'; method: 'CASH' | 'BANK'; amount: number; date: string };
export type UserCreate = { name: string; email: string; password: string; role: 'ADMIN' | 'ACCOUNTANT' | 'CONTACT' };

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
  users: () => request<User[]>('/users'),
  createUser: (payload: UserCreate) => request<User>('/users', { method: 'POST', body: JSON.stringify(payload) }),
  sales: () => request<Sale[]>('/sales'),
  createSale: (payload: { customer_id: number; product_id: number; quantity: number; unit_price?: number; tax_percent?: number }) => request<Sale>('/sales', { method: 'POST', body: JSON.stringify(payload) }),
  deleteSale: (id: number) => request<void>(`/sales/${id}`, { method: 'DELETE' }),
  purchases: () => request<Purchase[]>('/purchases'),
  createPurchase: (payload: { vendor_id: number; product_id: number; quantity: number; unit_price?: number; tax_percent?: number }) => request<Purchase>('/purchases', { method: 'POST', body: JSON.stringify(payload) }),
  deletePurchase: (id: number) => request<void>(`/purchases/${id}`, { method: 'DELETE' }),
  payments: () => request<Payment[]>('/payments'),
  createPayment: (payload: { contact_id: number; reference_id?: number; type: Payment['type']; method: Payment['method']; amount: number }) => request<Payment>('/payments', { method: 'POST', body: JSON.stringify(payload) }),
  profitLoss: () => request<Record<string, unknown>>('/reports/profit-loss'),
  balanceSheet: () => request<Record<string, unknown>>('/reports/balance-sheet'),
  trialBalance: () => request<Record<string, unknown>>('/reports/trial-balance'),
};
