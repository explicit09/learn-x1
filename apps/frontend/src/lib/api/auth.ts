import apiClient from './client';
import { jwtDecode } from 'jwt-decode';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  organization_id?: string;
  organization_name?: string;
  organization_domain?: string;
}

export interface AuthResponse {
  data: {
    access_token: string;
    token_type: string;
    expires_at: string;
  };
  message: string;
}

export interface UserData {
  id: string;
  email: string;
  name: string;
  role: string;
  organization_id: string;
  is_active: boolean;
}

export interface DecodedToken {
  sub: string; // user ID
  org: string; // organization ID
  role: string; // user role
  exp: number; // expiration timestamp
}

const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    if (response.data.data.access_token) {
      localStorage.setItem('auth_token', response.data.data.access_token);
    }
    return response.data;
  },

  async register(data: RegisterData): Promise<any> {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  async logout(): Promise<void> {
    localStorage.removeItem('auth_token');
  },

  async getCurrentUser(): Promise<UserData | null> {
    try {
      const response = await apiClient.get('/users/me');
      return response.data.data;
    } catch (error) {
      return null;
    }
  },

  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    
    const token = localStorage.getItem('auth_token');
    if (!token) return false;
    
    try {
      const decoded = jwtDecode<DecodedToken>(token);
      const currentTime = Date.now() / 1000;
      
      return decoded.exp > currentTime;
    } catch (error) {
      return false;
    }
  },

  getDecodedToken(): DecodedToken | null {
    if (typeof window === 'undefined') return null;
    
    const token = localStorage.getItem('auth_token');
    if (!token) return null;
    
    try {
      return jwtDecode<DecodedToken>(token);
    } catch (error) {
      return null;
    }
  },

  getUserRole(): string | null {
    const decoded = this.getDecodedToken();
    return decoded?.role || null;
  },

  getOrganizationId(): string | null {
    const decoded = this.getDecodedToken();
    return decoded?.org || null;
  },
};

export default authService;
