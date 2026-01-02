export interface User {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user';
  roles?: string[]; // Legacy support for roles array
  avatar?: string;
  createdAt: string;
  updatedAt: string;
  lastLogin?: string;
  preferences?: Record<string, any>;
}

export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthResponse {
  token: string; // Main auth token
  accessToken: string;
  refreshToken: string;
  user: Omit<User, 'password'>;
  expiresIn: number;
  tokenType: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
  initialized: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (data: PasswordResetConfirm) => Promise<void>;
  refreshUser: () => Promise<User | null>;
}
